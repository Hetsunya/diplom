import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMediaStream } from "../hooks/useMediaStream";
import { useMeetingWebSocket } from "../features/meeting/useMeetingWebSocket";
import { useMeetingStore } from "../features/meeting/useMeetingStore";
import { useScreenShare } from "../hooks/useScreenShare";
import {
  MeetingTranscriptRail,
  type ChatLine,
  type TranscriptLine,
} from "../features/meeting/MeetingTranscriptRail";
import { useMeetingAudioChunks } from "../features/meeting/useMeetingAudioChunks";
import { getSessionChatMessages } from "../api/sessions";

export type Emotion = "Happy" | "Neutral" | "Engaged" | "Focused" | "Surprised" | "Thoughtful";

type Participant = {
  id: string;
  name: string;
  emotion: Emotion;
  emotionConfidence: number;
  faceSignalReceived: boolean;
};

function mapEmotionLabel(normalized: string): Emotion | undefined {
  if (normalized.includes("happy")) return "Happy";
  if (normalized.includes("surpris")) return "Surprised";
  if (normalized.includes("neutral")) return "Neutral";
  if (normalized.includes("fear") || normalized.includes("disgust")) return "Engaged";
  if (normalized.includes("sad")) return "Focused";
  if (normalized.includes("angry")) return "Thoughtful";
  return undefined;
}

function parseEmotionFromLegacyPayload(p: Record<string, unknown>): { emotion: Emotion; confidence: number } | null {
  let emotion: Emotion | undefined;
  let confidence = 0;

  const maybeEmotion = p["emotion"];
  if (typeof maybeEmotion === "string") {
    emotion = mapEmotionLabel(maybeEmotion.toLowerCase());
  }

  const maybeConfidence = p["confidence"];
  if (typeof maybeConfidence === "number") {
    confidence = maybeConfidence > 1 ? maybeConfidence : maybeConfidence * 100;
  }

  const probs = p["probs"] ?? p["probabilities"];
  if (!emotion && probs && typeof probs === "object") {
    const pr = probs as Record<string, unknown>;
    let bestKey: string | null = null;
    let bestVal = -1;
    for (const [k, v] of Object.entries(pr)) {
      if (typeof v !== "number") continue;
      if (v > bestVal) {
        bestVal = v;
        bestKey = k;
      }
    }
    if (bestKey) {
      emotion = mapEmotionLabel(bestKey.toLowerCase());
      confidence = bestVal > 1 ? bestVal : bestVal * 100;
    }
  }

  if (!emotion) return null;
  return { emotion, confidence: Math.round(confidence) };
}

function parseFaceAnalysisPayload(p: Record<string, unknown>): { emotion: Emotion; confidence: number } | null {
  const ff = p["face_features"];
  if (!ff || typeof ff !== "object") return null;
  const f = ff as Record<string, unknown>;
  let emotion: Emotion | undefined;
  let confidence = 0;
  const dom = f["dominant_emotion"];
  if (typeof dom === "string") emotion = mapEmotionLabel(dom.toLowerCase());

  const probs = f["probs"] ?? f["probabilities"];
  if (!emotion && probs && typeof probs === "object") {
    const pr = probs as Record<string, unknown>;
    let bestKey: string | null = null;
    let bestVal = -1;
    for (const [k, v] of Object.entries(pr)) {
      if (typeof v !== "number") continue;
      if (v > bestVal) {
        bestVal = v;
        bestKey = k;
      }
    }
    if (bestKey) {
      emotion = mapEmotionLabel(bestKey.toLowerCase());
      confidence = bestVal > 1 ? bestVal : bestVal * 100;
    }
  }

  const maybeConf = f["confidence"];
  if (typeof maybeConf === "number") {
    confidence = maybeConf > 1 ? maybeConf : maybeConf * 100;
  }

  if (!emotion) return null;
  return { emotion, confidence: Math.round(confidence) };
}

const VideoMeet = () => {
  const { id = "" } = useParams(); // session ID
  const navigate = useNavigate();
  const getOrCreateParticipant = () => {
    const existingId = sessionStorage.getItem("participant_id") || localStorage.getItem("participant_id");
    if (existingId) return existingId;

    const uuid =
      globalThis.crypto?.randomUUID?.() ||
      `p_${Date.now()}_${Math.floor(Math.random() * 100000)}`;
    sessionStorage.setItem("participant_id", uuid);

    if (!sessionStorage.getItem("participant_name") && !localStorage.getItem("participant_name")) {
      sessionStorage.setItem("participant_name", "You");
    }

    return uuid;
  };

  const [participantId] = useState<string>(getOrCreateParticipant);
  const participantName =
    sessionStorage.getItem("participant_name") || localStorage.getItem("participant_name") || "You";
  const participantRole =
    sessionStorage.getItem("participant_role") || localStorage.getItem("participant_role") || "participant";

  const {
    videoRef,
    streamRef,
    mediaReady,
    captureFrame,
    toggleMic,
    toggleCam,
    micEnabled,
    camEnabled,
    error: mediaError,
  } = useMediaStream();

  const { startShare, error: shareError } = useScreenShare();

  const meetingParticipants = useMeetingStore((s) => s.participants);
  const toasts = useMeetingStore((s) => s.toasts);
  const popToast = useMeetingStore((s) => s.popToast);
  const upsert = useMeetingStore((s) => s.upsertParticipant);
  const resetMeetingStore = useMeetingStore((s) => s.reset);

  const [transcriptLines, setTranscriptLines] = useState<TranscriptLine[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatLine[]>([]);
  const [lastTextAt, setLastTextAt] = useState<number | null>(null);
  const [verdictSummary, setVerdictSummary] = useState<string | null>(null);
  const [verdictDetail, setVerdictDetail] = useState<unknown | null>(null);
  const [verdictSource, setVerdictSource] = useState<string | null>(null);
  const [verdictExpanded, setVerdictExpanded] = useState(false);

  useEffect(() => {
    resetMeetingStore();
  }, [id, resetMeetingStore]);

  // Ensure "self" exists in store immediately (snapshot с сервера затем дополнит список).
  useEffect(() => {
    upsert({
      id: participantId,
      name: participantName,
      emotion: "Neutral",
      emotionConfidence: 0,
      faceSignalReceived: false,
    });
  }, [participantId, participantName, upsert]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      try {
        const rows = await getSessionChatMessages(id, 150);
        if (cancelled) return;
        const mapped: ChatLine[] = rows.map((r) => ({
          id: String(r.chat_message_id),
          participantId: r.participant_id,
          name: r.sender_name?.trim() || `Participant ${r.participant_id}`,
          text: r.body,
          at: r.created_at,
        }));
        setChatMessages((prev) => {
          const byId = new Map<string, ChatLine>();
          for (const m of mapped) byId.set(m.id, m);
          for (const m of prev) {
            if (!byId.has(m.id)) byId.set(m.id, m);
          }
          return Array.from(byId.values())
            .sort((a, b) => new Date(a.at).getTime() - new Date(b.at).getTime())
            .slice(-200);
        });
      } catch {
        // History is optional; live chat still works over WS.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const onAnalysisMessage = useCallback(
    (msg: unknown) => {
      if (typeof msg !== "object" || msg === null) return;
      const m = msg as { type?: unknown; participant_id?: unknown; payload?: unknown };
      const type = typeof m.type === "string" ? m.type : undefined;
      const pid = typeof m.participant_id === "string" ? m.participant_id : undefined;

      const store = useMeetingStore.getState();
      const nameFor = (id: string) => store.participants[id]?.name ?? `Participant ${id}`;

      if (type === "chat_message" && pid && m.payload && typeof m.payload === "object") {
        const p = m.payload as Record<string, unknown>;
        const text = typeof p.text === "string" ? p.text.trim() : "";
        if (!text) return;
        const nameRaw = p.name;
        const dispName = typeof nameRaw === "string" && nameRaw.trim() ? nameRaw.trim() : nameFor(pid);
        const clientId = typeof p.client_id === "string" ? p.client_id : "";
        const tsRaw = (m as { timestamp?: unknown }).timestamp;
        const at = typeof tsRaw === "string" ? tsRaw : new Date().toISOString();
        const mid = p.chat_message_id;
        const id =
          typeof mid === "number" && Number.isFinite(mid)
            ? String(mid)
            : clientId
              ? `${pid}:${clientId}`
              : `${pid}-${at}-${text.slice(0, 48)}`;
        setChatMessages((prev) => {
          if (prev.some((x) => x.id === id)) return prev;
          return [...prev, { id, participantId: pid, name: dispName, text, at }].slice(-200);
        });
        return;
      }

      if (type === "emotion" && pid && m.payload && typeof m.payload === "object") {
        const parsed = parseEmotionFromLegacyPayload(m.payload as Record<string, unknown>);
        if (parsed) {
          upsert({
            id: pid,
            name: nameFor(pid),
            emotion: parsed.emotion,
            emotionConfidence: parsed.confidence,
            faceSignalReceived: true,
          });
        }
        return;
      }

      if (type === "face_analysis" && pid && m.payload && typeof m.payload === "object") {
        const parsed = parseFaceAnalysisPayload(m.payload as Record<string, unknown>);
        if (parsed) {
          upsert({
            id: pid,
            name: nameFor(pid),
            emotion: parsed.emotion,
            emotionConfidence: parsed.confidence,
            faceSignalReceived: true,
          });
        }
        return;
      }

      if (type === "text_analysis" && pid && m.payload && typeof m.payload === "object") {
        const p = m.payload as Record<string, unknown>;
        const traceRaw = p["trace_id"];
        const traceId = typeof traceRaw === "string" ? traceRaw : `local-${Date.now()}-${pid}`;
        const partial = p["transcript_partial"];
        const final = p["transcript_final"];
        const text =
          typeof final === "string" ? final : typeof partial === "string" ? partial : "";
        const stage = p["stage"];
        const isFinal =
          typeof final === "string" ||
          stage === "final" ||
          (typeof stage === "string" && stage.toLowerCase().includes("final"));

        setTranscriptLines((prev) => {
          const idx = prev.findIndex((l) => l.traceId === traceId && l.participantId === pid);
          const line: TranscriptLine = {
            traceId,
            participantId: pid,
            speakerLabel: nameFor(pid),
            text,
            final: isFinal,
            at: new Date().toISOString(),
          };
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = { ...next[idx], ...line };
            return next;
          }
          return [...prev, line].slice(-80);
        });
        setLastTextAt(Date.now());
        return;
      }

      if ((type === "analysis_report_partial" || type === "analysis_report") && m.payload && typeof m.payload === "object") {
        const p = m.payload as Record<string, unknown>;
        const report = p["report"];
        const srcRaw = p["report_source"];
        const source = typeof srcRaw === "string" ? srcRaw : null;
        let summary: string | null = null;
        if (report && typeof report === "object") {
          const r = report as Record<string, unknown>;
          if (typeof r.summary === "string") summary = r.summary;
          else if (typeof r.headline === "string") summary = r.headline;
        }
        setVerdictDetail(report ?? p);
        setVerdictSummary(summary ?? (type === "analysis_report" ? "Итоговый отчёт" : "Частичный отчёт"));
        setVerdictSource(source);
        setVerdictExpanded(false);
      }
    },
    [upsert]
  );

  const { send, close, connected } = useMeetingWebSocket(
    id,
    participantId,
    onAnalysisMessage,
    () => {
      sessionStorage.setItem("meeting_notice", "Митинг завершён (хост вышел).");
      navigate("/sessions");
    }
  );

  const sendChatMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      const client_id =
        globalThis.crypto?.randomUUID?.() ?? `c_${Date.now()}_${Math.floor(Math.random() * 1e9)}`;
      send("chat_message", {
        text: trimmed.slice(0, 2000),
        name: participantName,
        client_id,
      });
    },
    [send, participantName]
  );

  useMeetingAudioChunks(streamRef, send, {
    enabled: micEnabled,
    mediaReady,
    timesliceMs: 3500,
  });

  useEffect(() => {
    if (toasts.length === 0) return;
    const t = window.setTimeout(() => popToast(), 2500);
    return () => window.clearTimeout(t);
  }, [toasts.length, popToast]);

  const participants: Record<string, Participant> = Object.fromEntries(
    Object.entries(meetingParticipants).map(([k, v]) => [
      k,
      {
        id: v.id,
        name: v.name,
        emotion: (v.emotion as Emotion) ?? "Neutral",
        emotionConfidence: v.emotionConfidence ?? 0,
        faceSignalReceived: v.faceSignalReceived === true,
      },
    ])
  );

  // Отправка кадра каждые 2 секунды
  useEffect(() => {
    const timer = setInterval(() => {
      const frame = captureFrame();
      if (!frame) return;

      send("frame", { frame });
    }, 2000);

    return () => clearInterval(timer);
  }, [captureFrame, send]);

  const emotionToClass = (emotion: Emotion) => {
    switch (emotion) {
      case "Happy":
        return "happy";
      case "Engaged":
        return "engaged";
      case "Focused":
        return "focused";
      case "Surprised":
        return "surprised";
      case "Thoughtful":
        return "thoughtful";
      case "Neutral":
      default:
        return "neutral";
    }
  };

  const leaveMeeting = () => {
    send("leave", { name: participantName, role: participantRole });
    close();
    sessionStorage.setItem("meeting_notice", "Вы вышли из встречи.");
    navigate("/sessions");
  };

  const endMeeting = () => {
    // If not host, behave like leave.
    if (participantRole !== "host") {
      leaveMeeting();
      return;
    }
    send("end_meeting", { role: "host" });
    close();
    sessionStorage.setItem("meeting_notice", "Вы завершили встречу.");
    navigate("/sessions");
  };

  return (
    <div className="video-container">
      <div className="video-meet-layout">
        <div className="video-meet-main">
          {(mediaError || shareError) && (
            <div
              style={{
                background: "#3b2a1f",
                color: "white",
                padding: "10px 12px",
                borderRadius: 10,
                marginBottom: 12,
              }}
              role="status"
            >
              {mediaError || shareError}
            </div>
          )}
          {toasts.length > 0 && (
            <div style={{ position: "fixed", top: 12, right: 12, zIndex: 10 }}>
              {toasts.map((t, idx) => (
                <div
                  key={`${idx}-${t}`}
                  style={{
                    background: "rgba(0,0,0,0.75)",
                    color: "white",
                    padding: "10px 12px",
                    borderRadius: 10,
                    marginBottom: 8,
                    maxWidth: 320,
                  }}
                >
                  {t}
                </div>
              ))}
            </div>
          )}
          <div className="video-grid">
            {Object.values(participants).map((p) => {
              const isSelf = p.id === participantId;
              const showMicOff = isSelf && !micEnabled;
              const showCamOff = isSelf && !camEnabled;
              return (
                <div key={p.id} className="video-tile">
                  <div className="tile-media">
                    {isSelf ? (
                      <>
                        <video
                          ref={videoRef}
                          autoPlay
                          playsInline
                          className={`tile-media__video ${showCamOff ? "video-hidden" : ""}`}
                        />
                        {showCamOff && <div className="video-placeholder video-placeholder--overlay" />}
                      </>
                    ) : (
                      <div className="fake-video fake-video--remote">
                        <div className="face-placeholder" />
                      </div>
                    )}

                    {!p.faceSignalReceived ? (
                      <div
                        className="emotion-indicator emotion-indicator--pending"
                        title="Ожидание данных о лице с сервера"
                      >
                        Лицо: —
                      </div>
                    ) : (
                      <div className={`emotion-indicator ${emotionToClass(p.emotion)}`}>
                        {p.emotion} {p.emotionConfidence}%
                      </div>
                    )}

                    <div className="participant-chip">
                      <span className="participant-chip__name">{p.name}</span>
                      {(showMicOff || showCamOff) && (
                        <span className="participant-chip__status">
                          {showMicOff ? "Mic off" : ""}
                          {showMicOff && showCamOff ? " · " : ""}
                          {showCamOff ? "Cam off" : ""}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="controls">
            <button
              className={`control-btn mic-btn ${micEnabled ? "active" : ""}`}
              onClick={toggleMic}
              type="button"
            >
              🎤 {micEnabled ? "Микрофон: вкл" : "Микрофон: выкл"}
            </button>

            <button
              className={`control-btn cam-btn ${camEnabled ? "active" : ""}`}
              onClick={toggleCam}
              type="button"
            >
              📹 {camEnabled ? "Камера: вкл" : "Камера: выкл"}
            </button>

            <button className="control-btn share-btn" onClick={startShare} type="button">
              🖥️ Поделиться экраном
            </button>

            <button className="control-btn" onClick={leaveMeeting} type="button">
              Выйти
            </button>

            <button className="control-btn end-btn" onClick={endMeeting} type="button">
              Завершить
            </button>
          </div>
        </div>

        <MeetingTranscriptRail
          lines={transcriptLines}
          asrStatus={lastTextAt ? "receiving" : "waiting…"}
          verdictSummary={verdictSummary}
          verdictDetail={verdictDetail}
          verdictSource={verdictSource}
          verdictExpanded={verdictExpanded}
          onToggleVerdict={() => setVerdictExpanded((e) => !e)}
          chatMessages={chatMessages}
          currentParticipantId={participantId}
          onSendChat={sendChatMessage}
          chatConnected={connected}
        />
      </div>
    </div>
  );
};

export default VideoMeet;

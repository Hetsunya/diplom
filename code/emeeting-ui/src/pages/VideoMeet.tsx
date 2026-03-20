import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useMediaStream } from "../hooks/useMediaStream";
import { useSessionWS } from "../hooks/useSessionWS";
import { useScreenShare } from "../hooks/useScreenShare";

const VideoMeet = () => {
  const { id = "" } = useParams(); // session ID
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

  const { videoRef, captureFrame, toggleMic, toggleCam, micEnabled, camEnabled } =
    useMediaStream();

  const { startShare } = useScreenShare();
  type Emotion = "Analyzing" | "Happy" | "Neutral" | "Engaged" | "Focused" | "Surprised" | "Thoughtful";
  type Participant = {
    id: string;
    name: string;
    emotion: Emotion;
    emotionConfidence: number;
  };

  const [participants, setParticipants] = useState<Record<string, Participant>>({
    [participantId]: {
      id: participantId,
      name: participantName,
      emotion: "Analyzing",
      emotionConfidence: 0,
    },
  });

  const { send } = useSessionWS(id, participantId, (msg) => {
    if (typeof msg !== "object" || msg === null) return;

    const m = msg as {
      type?: unknown;
      participant_id?: unknown;
      payload?: unknown;
    };

    const type = typeof m.type === "string" ? m.type : undefined;
    const pid = typeof m.participant_id === "string" ? m.participant_id : undefined;

    if (!type || !pid) return;

    if (type === "join") {
      let name = `Participant ${pid}`;
      const payload = m.payload;
      if (payload && typeof payload === "object") {
        const maybeName = (payload as Record<string, unknown>)["name"];
        if (typeof maybeName === "string") name = maybeName;
      }
      setParticipants((prev) => {
        if (prev[pid]) {
          return {
            ...prev,
            [pid]: { ...prev[pid], name },
          };
        }

        return {
          ...prev,
          [pid]: {
            id: pid,
            name,
            emotion: "Neutral",
            emotionConfidence: 80,
          },
        };
      });
    }

    if (type === "leave") {
      if (pid === participantId) return;
      setParticipants((prev) => {
        if (!prev[pid]) return prev;
        const next = { ...prev };
        delete next[pid];
        return next;
      });
    }

    if (type === "emotion") {
      const payload = m.payload;
      let emotion: Emotion | undefined;
      let confidence = 0;

      // Flexible parsing: different AI implementations may send different payload shapes.
      if (payload && typeof payload === "object") {
        const p = payload as Record<string, unknown>;
        const maybeEmotion = p["emotion"];
        if (typeof maybeEmotion === "string") {
          const normalized = maybeEmotion.toLowerCase();
          // Map arbitrary AI emotion labels to our UI set.
          if (normalized.includes("happy")) emotion = "Happy";
          else if (normalized.includes("surpris")) emotion = "Surprised";
          else if (normalized.includes("neutral")) emotion = "Neutral";
          else if (normalized.includes("fear") || normalized.includes("disgust")) emotion = "Engaged";
          else if (normalized.includes("sad")) emotion = "Focused";
          else if (normalized.includes("angry")) emotion = "Thoughtful";
        }

        const maybeConfidence = p["confidence"];
        if (typeof maybeConfidence === "number") {
          // assume either 0..1 or 0..100
          confidence = maybeConfidence > 1 ? maybeConfidence : maybeConfidence * 100;
        }

        const probs = p["probs"] ?? p["probabilities"];
        if ((!emotion || emotion === "Analyzing") && probs && typeof probs === "object") {
          const pr = probs as Record<string, unknown>;
          // pick max prob from probs
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
            const normalized = bestKey.toLowerCase();
            if (normalized.includes("happy")) emotion = "Happy";
            else if (normalized.includes("surpris")) emotion = "Surprised";
            else if (normalized.includes("neutral")) emotion = "Neutral";
            else if (normalized.includes("fear") || normalized.includes("disgust")) emotion = "Engaged";
            else if (normalized.includes("sad")) emotion = "Focused";
            else if (normalized.includes("angry")) emotion = "Thoughtful";
            confidence = bestVal > 1 ? bestVal : bestVal * 100;
          }
        }
      }

      setParticipants((prev) => {
        const current = prev[pid];
        if (!current) {
          return {
            ...prev,
            [pid]: {
              id: pid,
              name: `Participant ${pid}`,
              emotion: emotion ?? "Neutral",
              emotionConfidence: Math.round(confidence),
            },
          };
        }
        return {
          ...prev,
          [pid]: {
            ...current,
            emotion: emotion ?? current.emotion,
            emotionConfidence: emotion ? Math.round(confidence) : current.emotionConfidence,
          },
        };
      });
    }
  });

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
      case "Analyzing":
        return "neutral";
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

  return (
    <div className="video-container">
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
                    className={showCamOff ? "video-hidden" : ""}
                  />
                  {showCamOff && (
                    <div className="video-placeholder video-placeholder--overlay" />
                  )}
                </>
              ) : (
                <div className="fake-video">
                  <div className="face-placeholder" />
                  <div className="video-placeholder" />
                </div>
              )}
            </div>

            <div className={`emotion-indicator ${emotionToClass(p.emotion)}`}>
              {p.emotion === "Analyzing" ? "AI analyzing..." : `${p.emotion} ${p.emotionConfidence}%`}
            </div>

            <div className="participant-name">
              {p.name}
              {showMicOff ? " • Mic off" : ""}
              {showCamOff ? " • Cam off" : ""}
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

        <button className="control-btn end-btn" type="button">
          Завершить
        </button>
      </div>
    </div>
  );
};

export default VideoMeet;

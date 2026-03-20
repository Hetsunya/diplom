import { useEffect, useMemo, useState } from "react";
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
  type Emotion = "Happy" | "Neutral" | "Engaged" | "Focused" | "Surprised" | "Thoughtful";
  type Participant = {
    id: string;
    name: string;
    emotion: Emotion;
    emotionConfidence: number;
  };

  const emotions: Emotion[] = useMemo(
    () => ["Happy", "Neutral", "Engaged", "Focused", "Surprised", "Thoughtful"],
    []
  );

  const [participants, setParticipants] = useState<Record<string, Participant>>({
    [participantId]: {
      id: participantId,
      name: participantName,
      emotion: "Neutral",
      emotionConfidence: 80,
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

  // Симуляция эмоций (пока AI-детектор не подключён)
  useEffect(() => {
    const interval = setInterval(() => {
      setParticipants((prev) => {
        const next: Record<string, Participant> = {};
        for (const [key, p] of Object.entries(prev)) {
          const nextEmotion = emotions[Math.floor(Math.random() * emotions.length)];
          const confidence = Math.floor(Math.random() * 31) + 60; // 60..90
          next[key] = { ...p, emotion: nextEmotion, emotionConfidence: confidence };
        }
        return next;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [emotions]);

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
                showCamOff ? (
                  <div className="video-placeholder" />
                ) : (
                  <video ref={videoRef} autoPlay playsInline />
                )
              ) : (
                <div className="fake-video">
                  <div className="face-placeholder" />
                  <div className="video-placeholder" />
                </div>
              )}
            </div>

            <div className={`emotion-indicator ${emotionToClass(p.emotion)}`}>
              {p.emotion} {p.emotionConfidence}%
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

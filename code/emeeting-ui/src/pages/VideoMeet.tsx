import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMediaStream } from "../hooks/useMediaStream";
import { useSessionWS } from "../hooks/useSessionWS";
import { useScreenShare } from "../hooks/useScreenShare";

const VideoMeet = () => {
  const { id = "" } = useParams(); // session ID
  const participantId = localStorage.getItem("participant_id") || "anon"; // или берём реальный id

  const { videoRef, captureFrame, toggleMic, toggleCam, micEnabled, camEnabled } =
    useMediaStream();

  const { startShare } = useScreenShare();
  const { send } = useSessionWS(id, participantId); // передаём participantId

  type Emotion = "Happy" | "Neutral" | "Engaged" | "Focused" | "Surprised" | "Thoughtful";
  type Participant = {
    id: string;
    name: string;
    isMuted: boolean;
    isVideoOff: boolean;
    emotion: Emotion;
    emotionConfidence: number;
  };

  const emotions: Emotion[] = useMemo(
    () => ["Happy", "Neutral", "Engaged", "Focused", "Surprised", "Thoughtful"],
    []
  );

  const [participants, setParticipants] = useState<Participant[]>([
    { id: "you", name: "You", isMuted: false, isVideoOff: false, emotion: "Neutral", emotionConfidence: 80 },
    { id: "p2", name: "Sarah Chen", isMuted: false, isVideoOff: false, emotion: "Engaged", emotionConfidence: 75 },
    { id: "p3", name: "Michael Rodriguez", isMuted: true, isVideoOff: false, emotion: "Focused", emotionConfidence: 72 },
    { id: "p4", name: "Emily Johnson", isMuted: false, isVideoOff: false, emotion: "Thoughtful", emotionConfidence: 78 },
  ]);

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
      setParticipants((prev) =>
        prev.map((p) => {
          const nextEmotion = emotions[Math.floor(Math.random() * emotions.length)];
          const confidence = Math.floor(Math.random() * 31) + 60; // 60..90
          return { ...p, emotion: nextEmotion, emotionConfidence: confidence };
        })
      );
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
        {participants.map((p) => {
          const isMuted = p.id === "you" ? !micEnabled : p.isMuted;
          const isVideoOff = p.id === "you" ? !camEnabled : p.isVideoOff;
          return (
          <div key={p.id} className="video-tile">
            <div className="tile-media">
              {p.id === "you" ? (
                isVideoOff ? (
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
              {p.id === "you" && isMuted ? " • Mic off" : ""}
              {p.id === "you" && isVideoOff ? " • Cam off" : ""}
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

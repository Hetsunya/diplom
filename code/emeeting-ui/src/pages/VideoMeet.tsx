import { useEffect } from "react";
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

  // Отправка кадра каждые 2 секунды
  useEffect(() => {
    const timer = setInterval(() => {
      const frame = captureFrame();
      if (!frame) return;

      send("frame", { frame });
    }, 2000);

    return () => clearInterval(timer);
  }, [captureFrame, send]);

  return (
    <div className="video-container">
      <video ref={videoRef} autoPlay playsInline />

      <div className="controls">
        <button onClick={toggleMic}>
          🎤 {micEnabled ? "Выкл" : "Вкл"}
        </button>

        <button onClick={toggleCam}>
          📹 {camEnabled ? "Выкл" : "Вкл"}
        </button>

        <button onClick={startShare}>🖥️ Поделиться</button>
        <button>Завершить</button>
      </div>
    </div>
  );
};

export default VideoMeet;

import { useParams } from "react-router-dom";
import { useMediaStream } from "../hooks/useMediaStream";
import { useSessionWS } from "../hooks/useSessionWS";
import { useScreenShare } from "../hooks/useScreenShare";

const VideoMeet = () => {
  const { id = "" } = useParams();

  const { videoRef, toggleMic, toggleCam, micEnabled, camEnabled } =
    useMediaStream();

  const { startShare } = useScreenShare();
  useSessionWS(id);

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

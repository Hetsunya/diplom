// src/pages/VideoMeet.tsx
import { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';

const VideoMeet = () => {
  const { id } = useParams();
  const videoRef = useRef<HTMLVideoElement>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const getMedia = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        if (videoRef.current) videoRef.current.srcObject = stream;
      } catch (error) {
        console.error(error);
      }
    };
    getMedia();

    ws.current = new WebSocket(`ws://localhost:8080/ws/${id}`);
    ws.current.onopen = () => console.log('WS connected');
    ws.current.onmessage = (msg) => console.log('WS message:', msg.data);

    return () => {
      ws.current?.close();
    };
  }, [id]);

  return (
    <div className="video-container">
      <div className="video-header">
        <h1>Видеоконференция {id}</h1>
        <div className="participants-list">Участники: ...</div>
      </div>
      <div className="video-grid">
        <div className="video-tile">
          <div className="participant-name">Вы</div>
          <video className="video-placeholder" ref={videoRef} autoPlay playsInline />
        </div>
      </div>
      <div className="controls">
        <button className="control-btn mic-btn"><span className="icon">🎤</span>Микрофон</button>
        <button className="control-btn cam-btn"><span className="icon">📹</span>Камера</button>
        <button className="control-btn share-btn"><span className="icon">🖥️</span>Поделиться</button>
        <button className="end-btn">Завершить</button>
      </div>
      <div className="status-bar">
        <span className="analysis-status">Анализ эмоций активен</span>
      </div>
    </div>
  );
};

export default VideoMeet;
import { useEffect, useRef, useState } from "react";

export const useMediaStream = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(document.createElement("canvas"));

  const canUseMedia = !!globalThis.navigator?.mediaDevices?.getUserMedia;
  const [micEnabled, setMicEnabled] = useState(() => canUseMedia);
  const [camEnabled, setCamEnabled] = useState(() => canUseMedia);
  const [error, setError] = useState<string | null>(() => {
    const md = globalThis.navigator?.mediaDevices;
    if (!md?.getUserMedia) {
      return "Камера/микрофон недоступны в этом контексте. Откройте приложение через http://localhost:5173 или используйте HTTPS.";
    }
    return null;
  });

  useEffect(() => {
    const md = globalThis.navigator?.mediaDevices;
    if (!md?.getUserMedia) {
      return;
    }

    md.getUserMedia({ video: true, audio: true })
      .then((stream) => {
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Не удалось получить доступ к камере/микрофону");
        setMicEnabled(false);
        setCamEnabled(false);
      });

    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const captureFrame = (): string | null => {
    const video = videoRef.current;
    if (!video || video.videoWidth === 0) return null;

    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.6);
  };

  const toggleMic = () => {
    streamRef.current?.getAudioTracks().forEach(
      (t) => (t.enabled = !t.enabled)
    );
    setMicEnabled((v) => !v);
  };

  const toggleCam = () => {
    streamRef.current?.getVideoTracks().forEach(
      (t) => (t.enabled = !t.enabled)
    );
    setCamEnabled((v) => !v);
  };

  return {
    videoRef,
    captureFrame,
    toggleMic,
    toggleCam,
    micEnabled,
    camEnabled,
    error,
  };
};

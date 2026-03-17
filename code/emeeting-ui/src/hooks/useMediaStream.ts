import { useEffect, useRef, useState } from "react";

export const useMediaStream = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(document.createElement("canvas"));

  const [micEnabled, setMicEnabled] = useState(true);
  const [camEnabled, setCamEnabled] = useState(true);

  useEffect(() => {
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: true })
      .then((stream) => {
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
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
  };
};

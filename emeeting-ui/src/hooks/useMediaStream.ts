import { useEffect, useRef, useState } from "react";

export const useMediaStream = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

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

  return { videoRef, toggleMic, toggleCam, micEnabled, camEnabled };
};

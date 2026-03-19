import { useEffect, useRef } from "react";

const DEFAULT_WS_URL = "ws://localhost:8080";
const WS_URL = import.meta.env.VITE_WS_URL || DEFAULT_WS_URL;

export const useSessionWS = (
  sessionId: string,
  participantId: string
) => {
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    ws.current = new WebSocket(`${WS_URL}/ws/sessions/${sessionId}`);

    ws.current.onopen = () => console.log("WS connected");
    ws.current.onmessage = (msg) => console.log("WS:", msg.data);

    return () => ws.current?.close();
  }, [sessionId]);

  const send = (type: string, payload?: unknown) => {
    ws.current?.send(
      JSON.stringify({
        type,
        session_id: Number(sessionId),
        participant_id: participantId,
        payload,
        timestamp: new Date().toISOString(),
      })
    );
  };

  return { send };
};

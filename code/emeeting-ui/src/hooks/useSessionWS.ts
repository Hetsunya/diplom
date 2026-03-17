import { useEffect, useRef } from "react";

export const useSessionWS = (
  sessionId: string,
  participantId: string
) => {
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    ws.current = new WebSocket(`ws://localhost:8080/ws/sessions/${sessionId}`);

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

import { useEffect, useRef } from "react";

const DEFAULT_WS_URL = "ws://localhost:8080";
const WS_URL = import.meta.env.VITE_WS_URL || DEFAULT_WS_URL;

export const useSessionWS = (
  sessionId: string,
  participantId: string,
  onMessage?: (msg: unknown) => void
) => {
  const ws = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    ws.current = new WebSocket(`${WS_URL}/ws/sessions/${sessionId}`);

    // Сообщения пока не отображаем в UI (бекенд будет отправлять события в будущем).
    ws.current.onopen = () => {
      const name = sessionStorage.getItem("participant_name") || localStorage.getItem("participant_name") || "You";
      ws.current?.send(
        JSON.stringify({
          type: "join",
          session_id: Number(sessionId),
          participant_id: participantId,
          payload: { name },
          timestamp: new Date().toISOString(),
        })
      );
    };

    ws.current.onmessage = (event) => {
      const handler = onMessageRef.current;
      if (!handler) return;
      try {
        handler(JSON.parse(event.data));
      } catch {
        handler(event.data);
      }
    };

    return () => ws.current?.close();
  }, [sessionId, participantId]);

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

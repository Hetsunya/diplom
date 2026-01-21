import { useEffect, useRef } from "react";

export const useSessionWS = (sessionId: string) => {
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    ws.current = new WebSocket(`ws://localhost:8080/ws/sessions/${sessionId}`);

    ws.current.onopen = () => console.log("WS connected");
    ws.current.onmessage = (msg) => console.log("WS:", msg.data);

    return () => ws.current?.close();
  }, [sessionId]);

  const send = (data: unknown) => {
    ws.current?.send(JSON.stringify(data));
  };

  return { send };
};

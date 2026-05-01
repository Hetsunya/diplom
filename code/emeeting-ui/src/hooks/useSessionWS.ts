import { useEffect, useRef } from "react";

const DEFAULT_WS_URL = "ws://localhost:8080";
const WS_URL = import.meta.env.VITE_WS_URL || DEFAULT_WS_URL;

type UseSessionWSOptions = {
  reconnect?: boolean;
  maxReconnectDelayMs?: number;
};

export const useSessionWS = (
  sessionId: string,
  participantId: string,
  onMessage?: (msg: unknown) => void,
  options: UseSessionWSOptions = {}
) => {
  const buildSocketUrl = (sid: string) => {
    const raw = (WS_URL || "").trim().replace(/\/+$/, "");
    if (raw.startsWith("ws://") || raw.startsWith("wss://")) {
      return `${raw}/ws/sessions/${sid}`;
    }
    if (raw.startsWith("http://") || raw.startsWith("https://")) {
      const wsBase = raw.replace(/^http/i, "ws");
      return `${wsBase}/ws/sessions/${sid}`;
    }
    if (raw.startsWith("/")) {
      // Reverse-proxy mode: VITE_WS_URL is path prefix (usually "/ws").
      return `${raw}/sessions/${sid}`;
    }
    return `${DEFAULT_WS_URL}/ws/sessions/${sid}`;
  };

  const ws = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<number | null>(null);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    const reconnectEnabled = options.reconnect ?? true;
    const maxDelay = options.maxReconnectDelayMs ?? 15_000;
    let disposed = false;

    const clearReconnectTimer = () => {
      if (reconnectTimer.current !== null) {
        window.clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
    };

    const sendJoin = () => {
      const name =
        sessionStorage.getItem("participant_name") ||
        localStorage.getItem("participant_name") ||
        "You";
      const role =
        sessionStorage.getItem("participant_role") ||
        localStorage.getItem("participant_role") ||
        "participant";
      ws.current?.send(
        JSON.stringify({
          type: "join",
          session_id: Number(sessionId),
          participant_id: participantId,
          payload: { name, role },
          timestamp: new Date().toISOString(),
        })
      );
    };

    const connect = () => {
      clearReconnectTimer();
      ws.current = new WebSocket(buildSocketUrl(sessionId));

      ws.current.onopen = () => {
        reconnectAttempt.current = 0;
        sendJoin();
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

      ws.current.onclose = () => {
        if (disposed) return;
        if (!reconnectEnabled) return;

        const attempt = reconnectAttempt.current++;
        const base = Math.min(maxDelay, 250 * 2 ** attempt);
        const jitter = Math.floor(Math.random() * 250);
        const delay = Math.min(maxDelay, base + jitter);
        reconnectTimer.current = window.setTimeout(() => connect(), delay);
      };
    };

    connect();

    return () => {
      disposed = true;
      clearReconnectTimer();
      ws.current?.close();
    };
  }, [sessionId, participantId, options.reconnect, options.maxReconnectDelayMs]);

  const send = (type: string, payload?: unknown) => {
    const sock = ws.current;
    if (!sock || sock.readyState !== WebSocket.OPEN) return;
    try {
      sock.send(
        JSON.stringify({
          type,
          session_id: Number(sessionId),
          participant_id: participantId,
          payload,
          timestamp: new Date().toISOString(),
        })
      );
    } catch {
      // Ignore transient close races during reconnect.
    }
  };

  const close = () => ws.current?.close();

  return { send, close };
};

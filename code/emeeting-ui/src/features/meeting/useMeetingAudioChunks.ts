import { useEffect } from "react";

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

function pickRecorderMime(): string {
  if (typeof MediaRecorder === "undefined") return "";
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  for (const m of candidates) {
    if (MediaRecorder.isTypeSupported(m)) return m;
  }
  return "";
}

/**
 * Sends periodic mic chunks over WS as `type: "audio"` for ai-gateway speech pipeline.
 * When mic is disabled, recording stops (no chunks).
 */
export function useMeetingAudioChunks(
  streamRef: React.RefObject<MediaStream | null>,
  send: (type: string, payload?: unknown) => void,
  opts: { enabled: boolean; mediaReady: boolean; timesliceMs?: number }
) {
  const { enabled, mediaReady, timesliceMs = 3500 } = opts;

  useEffect(() => {
    if (!enabled || !mediaReady || !streamRef.current) return;
    const audioTracks = streamRef.current.getAudioTracks().filter((t) => t.readyState === "live");
    if (audioTracks.length === 0) return;

    const mime = pickRecorderMime();
    if (!mime) return;

    let cancelled = false;
    let mr: MediaRecorder;
    let chunkSeq = 0;

    try {
      mr = new MediaRecorder(streamRef.current, { mimeType: mime });
    } catch {
      return;
    }

    mr.ondataavailable = async (ev: BlobEvent) => {
      if (cancelled || !ev.data || ev.data.size < 128) return;
      try {
        const buf = await ev.data.arrayBuffer();
        const chunk_base64 = bytesToBase64(new Uint8Array(buf));
        send("audio", {
          chunk_base64,
          mime,
          encoding: "base64",
          timeslice_ms: timesliceMs,
          sent_at_ms: Date.now(),
          chunk_seq: ++chunkSeq,
        });
      } catch {
        /* ignore chunk upload errors */
      }
    };

    try {
      mr.start(timesliceMs);
    } catch {
      return;
    }

    return () => {
      cancelled = true;
      try {
        if (mr.state !== "inactive") mr.stop();
      } catch {
        /* noop */
      }
    };
  }, [enabled, mediaReady, streamRef, send, timesliceMs]);
}

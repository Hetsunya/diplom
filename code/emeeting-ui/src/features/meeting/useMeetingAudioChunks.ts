import { useEffect } from "react";

/** Bound CPU/network: ~60–90s of Opus-in-WebM per rolling segment. */
const SEGMENT_MAX_MS = 90_000;
const SEGMENT_MAX_BYTES = 2 * 1024 * 1024;

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

function concatUint8Arrays(partials: Uint8Array[]): Uint8Array {
  let len = 0;
  for (const p of partials) len += p.byteLength;
  const out = new Uint8Array(len);
  let off = 0;
  for (const p of partials) {
    out.set(p, off);
    off += p.byteLength;
  }
  return out;
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
 *
 * MediaRecorder timeslice blobs are often **not** standalone WebM files; ffmpeg/Whisper needs
 * the initialization segment plus subsequent clusters. We concatenate all blobs since the last
 * segment boundary and POST that cumulative buffer so decoding stays stable.
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
    const parts: Uint8Array[] = [];
    let segmentStarted = Date.now();
    let segmentClosing = false;

    try {
      mr = new MediaRecorder(streamRef.current, { mimeType: mime });
    } catch {
      return;
    }

    const flushSegment = () => {
      parts.length = 0;
      segmentClosing = false;
      segmentStarted = Date.now();
      if (cancelled) return;
      try {
        mr.start(timesliceMs);
      } catch {
        /* recorder may be unusable after aggressive stop/start */
      }
    };

    mr.onstop = () => {
      flushSegment();
    };

    mr.ondataavailable = async (ev: BlobEvent) => {
      if (cancelled || !ev.data || ev.data.size < 64) return;
      try {
        const buf = new Uint8Array(await ev.data.arrayBuffer());
        if (buf.byteLength < 64) return;
        parts.push(buf);
        const merged = concatUint8Arrays(parts);
        if (merged.byteLength < 256) return;

        const elapsed = Date.now() - segmentStarted;
        const overBytes = merged.byteLength >= SEGMENT_MAX_BYTES;
        const overTime = elapsed >= SEGMENT_MAX_MS;
        const isFinal = overBytes || overTime;

        send("audio", {
          chunk_base64: bytesToBase64(merged),
          mime,
          encoding: "base64",
          timeslice_ms: timesliceMs,
          sent_at_ms: Date.now(),
          chunk_seq: ++chunkSeq,
          final_chunk: isFinal,
          segment_elapsed_ms: elapsed,
        });

        if (isFinal && !segmentClosing && mr.state === "recording") {
          segmentClosing = true;
          mr.stop();
        }
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

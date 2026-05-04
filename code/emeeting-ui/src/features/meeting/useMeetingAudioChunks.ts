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

/** Preferred mime for payload labelling; recorder may omit codec in `mimeType` after create. */
function createMediaRecorder(stream: MediaStream): { recorder: MediaRecorder; mimeHint: string } | null {
  if (typeof MediaRecorder === "undefined") return null;
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
    "audio/ogg",
  ];
  const supported = typeof MediaRecorder.isTypeSupported === "function";
  for (const m of candidates) {
    if (supported && !MediaRecorder.isTypeSupported(m)) continue;
    try {
      const recorder = new MediaRecorder(stream, { mimeType: m });
      return { recorder, mimeHint: recorder.mimeType || m };
    } catch {
      continue;
    }
  }
  try {
    const recorder = new MediaRecorder(stream);
    const mimeHint = recorder.mimeType || "audio/webm";
    return { recorder, mimeHint };
  } catch {
    return null;
  }
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
  opts: { enabled: boolean; mediaReady: boolean; streamEpoch?: number; timesliceMs?: number }
) {
  const { enabled, mediaReady, streamEpoch = 0, timesliceMs = 3500 } = opts;

  useEffect(() => {
    if (!enabled || !mediaReady || !streamRef.current) return;
    const base = streamRef.current;
    // Mic on/off is `enabled`; do not require `track.enabled` here (avoids UI vs track mismatch).
    const audioTracks = base.getAudioTracks().filter((t) => t.readyState === "live");
    if (audioTracks.length === 0) {
      console.warn("[emeeting-audio] skip MediaRecorder: no live audio tracks", {
        total: base.getAudioTracks().length,
        states: base.getAudioTracks().map((t) => t.readyState),
      });
      return;
    }

    // Some browsers record mic more reliably on an audio-only MediaStream than video+audio.
    const recordStream = new MediaStream(audioTracks);
    const created = createMediaRecorder(recordStream);
    if (!created) {
      console.warn("[emeeting-audio] MediaRecorder unsupported for this stream/mime");
      return;
    }

    let cancelled = false;
    const { recorder: mr, mimeHint: mime } = created;
    let chunkSeq = 0;
    const parts: Uint8Array[] = [];
    let segmentStarted = Date.now();
    let segmentClosing = false;

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
      if (cancelled || !ev.data || ev.data.size === 0) return;
      try {
        const buf = new Uint8Array(await ev.data.arrayBuffer());
        if (buf.byteLength === 0) return;
        parts.push(buf);
        const merged = concatUint8Arrays(parts);
        // Первый кластер WebM часто <256 B; иначе можем годами не вызвать send и ASR «мёртв».
        const elapsedWall = Date.now() - segmentStarted;
        const stalled =
          parts.length >= 2 ||
          (parts.length >= 1 && elapsedWall >= timesliceMs + 400) ||
          elapsedWall > 8000;
        if (merged.byteLength < 256 && !stalled) return;

        const elapsed = Date.now() - segmentStarted;
        const overBytes = merged.byteLength >= SEGMENT_MAX_BYTES;
        const overTime = elapsed >= SEGMENT_MAX_MS;
        const isFinal = overBytes || overTime;

        send("audio", {
          chunk_base64: bytesToBase64(merged),
          mime,
          encoding: "base64",
          /** Passed through to speech-service / faster-whisper (default ru in service if omitted). */
          language: "ru",
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
    } catch (e) {
      console.warn("[emeeting-audio] MediaRecorder.start failed", e);
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
  }, [enabled, mediaReady, streamEpoch, streamRef, send, timesliceMs]);
}

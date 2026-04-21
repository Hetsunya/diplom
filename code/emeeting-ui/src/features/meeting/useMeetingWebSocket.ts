import { useMeetingStore } from "./useMeetingStore";
import { handleMeetingEvent } from "./handleMeetingEvent";
import { useSessionWS } from "../../hooks/useSessionWS";

export function useMeetingWebSocket(
  sessionId: string,
  participantId: string,
  onMessage?: (msg: unknown) => void,
  onMeetingEnded?: (payload: unknown) => void
) {
  const upsertParticipant = useMeetingStore((s) => s.upsertParticipant);
  const removeParticipant = useMeetingStore((s) => s.removeParticipant);
  const pushToast = useMeetingStore((s) => s.pushToast);

  return useSessionWS(
    sessionId,
    participantId,
    (msg) => {
      handleMeetingEvent(msg, { upsertParticipant, removeParticipant, pushToast, onMeetingEnded });
      onMessage?.(msg);
    },
    { reconnect: true }
  );
}


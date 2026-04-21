import { create } from "zustand";

export type MeetingParticipant = {
  id: string;
  name: string;
  emotion?: string;
  emotionConfidence?: number;
};

type MeetingState = {
  participants: Record<string, MeetingParticipant>;
  toasts: string[];
  upsertParticipant: (p: MeetingParticipant) => void;
  removeParticipant: (id: string) => void;
  pushToast: (message: string) => void;
  popToast: () => void;
  reset: () => void;
};

export const useMeetingStore = create<MeetingState>((set) => ({
  participants: {},
  toasts: [],
  upsertParticipant: (p) =>
    set((s) => ({
      participants: {
        ...s.participants,
        [p.id]: { ...(s.participants[p.id] ?? {}), ...p },
      },
    })),
  removeParticipant: (id) =>
    set((s) => {
      if (!s.participants[id]) return s;
      const next = { ...s.participants };
      delete next[id];
      return { participants: next };
    }),
  pushToast: (message) =>
    set((s) => ({
      toasts: [...s.toasts, message].slice(-3),
    })),
  popToast: () =>
    set((s) => ({
      toasts: s.toasts.slice(1),
    })),
  reset: () => set({ participants: {}, toasts: [] }),
}));


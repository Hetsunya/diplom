export type WSEvent<T = unknown> = {
  type: string;
  payload?: T;
  ts?: string;
};

export type UserJoinedPayload = {
  participant_id: string;
  name?: string;
  joined_at?: string;
};

export type UserLeftPayload = {
  participant_id: string;
  name?: string;
  left_at?: string;
};


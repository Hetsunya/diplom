import { apiFetch } from "./http";
import type { Session, CreateSessionDTO } from "../types/db";

export async function getSessions(): Promise<Session[]> {
  const res = await apiFetch("/sessions");
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function createSession(data: CreateSessionDTO): Promise<Session> {
  const res = await apiFetch("/sessions", {
    method: "POST",
    body: JSON.stringify(data),
  });

  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function getSession(id: string): Promise<Session> {
  const res = await apiFetch(`/sessions/${id}`);
  if (!res.ok) throw new Error("Failed to fetch session");
  return res.json();
}

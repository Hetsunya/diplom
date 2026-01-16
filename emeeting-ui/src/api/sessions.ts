// src/api/sessions.ts
import { apiFetch } from './http';

export async function getSessions() {
  const res = await apiFetch('/sessions');
  if (!res.ok) throw new Error('Failed to fetch sessions');
  return res.json();
}

export async function createSession(data: any) {
  const res = await apiFetch('/sessions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function getSession(id: string) {
  const res = await apiFetch(`/sessions/${id}`);
  if (!res.ok) throw new Error('Failed to fetch session');
  return res.json();
}
// src/api/http.ts
export const API_URL = 'http://localhost:8080';

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(API_URL + path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
}
// src/api/http.ts
const DEFAULT_API_URL = 'http://localhost:8080';
export const API_URL = import.meta.env.VITE_API_URL || DEFAULT_API_URL;

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(API_URL + path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
}
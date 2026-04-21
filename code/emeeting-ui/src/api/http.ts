// src/api/http.ts
const DEFAULT_API_URL = 'http://localhost:8080';
export const API_URL = import.meta.env.VITE_API_URL || DEFAULT_API_URL;

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const res = await fetch(API_URL + path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (res.status !== 401 || path.startsWith("/auth/")) return res;

  // Try refresh once, then retry original request.
  try {
    const refresh = await fetch(API_URL + "/auth/refresh", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });
    if (!refresh.ok) return res;
    return await fetch(API_URL + path, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch {
    return res;
  }
}
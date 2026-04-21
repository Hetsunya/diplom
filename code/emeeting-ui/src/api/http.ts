// src/api/http.ts
const DEFAULT_API_URL = 'http://localhost:8080';
export const API_URL = import.meta.env.VITE_API_URL || DEFAULT_API_URL;

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const accessToken = sessionStorage.getItem("access_token");
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;

  const res = await fetch(API_URL + path, {
    credentials: 'include',
    headers: { ...headers, ...(options.headers as Record<string, string> | undefined) },
    ...options,
  });
  if (res.status !== 401 || path.startsWith("/auth/")) return res;

  // Try refresh once, then retry original request.
  try {
    const refreshToken = sessionStorage.getItem("refresh_token");
    const refresh = await fetch(API_URL + "/auth/refresh", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: refreshToken ? JSON.stringify({ refreshToken }) : undefined,
    });
    if (!refresh.ok) {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");
      sessionStorage.removeItem("auth_email");
      if (!window.location.pathname.startsWith("/login")) window.location.assign("/login");
      return res;
    }

    const pair = await refresh.json().catch(() => null) as
      | { accessToken?: string; refreshToken?: string }
      | null;
    if (pair?.accessToken) sessionStorage.setItem("access_token", pair.accessToken);
    if (pair?.refreshToken) sessionStorage.setItem("refresh_token", pair.refreshToken);

    const nextAccess = sessionStorage.getItem("access_token");
    const retryHeaders: Record<string, string> = { 'Content-Type': 'application/json' };
    if (nextAccess) retryHeaders.Authorization = `Bearer ${nextAccess}`;
    return await fetch(API_URL + path, {
      credentials: 'include',
      headers: { ...retryHeaders, ...(options.headers as Record<string, string> | undefined) },
      ...options,
    });
  } catch {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
    sessionStorage.removeItem("auth_email");
    if (!window.location.pathname.startsWith("/login")) window.location.assign("/login");
    return res;
  }
}
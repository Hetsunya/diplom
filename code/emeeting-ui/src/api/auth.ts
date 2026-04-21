// src/api/auth.ts
import { apiFetch } from './http';

export async function login(email: string, password: string) {
  const res = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error('Login failed');
  const json = await res.json();
  const user = (json?.user ?? json) as { email?: string };
  const tokens = json?.tokens as
    | { accessToken?: string; refreshToken?: string }
    | undefined;

  if (tokens?.accessToken) sessionStorage.setItem("access_token", tokens.accessToken);
  if (tokens?.refreshToken) sessionStorage.setItem("refresh_token", tokens.refreshToken);
  if (!user?.email) throw new Error("Login response missing user email");
  return { email: user.email };
}

export async function logout() {
  const res = await apiFetch('/auth/logout', { method: 'POST' });
  if (!res.ok) throw new Error('Logout failed');
}
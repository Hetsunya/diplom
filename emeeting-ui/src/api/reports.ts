// src/api/reports.ts
import { apiFetch } from './http';

export async function getReport(id: string) {
  const res = await apiFetch(`/reports/${id}`);
  if (!res.ok) throw new Error('Failed to fetch report');
  return res.json();
}
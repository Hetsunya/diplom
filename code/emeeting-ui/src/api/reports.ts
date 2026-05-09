// src/api/reports.ts
import { apiFetch } from './http';

export async function getReport(id: string) {
  // Preferred: analysis report stored from ai-gateway `analysis_report*` WS events.
  const res = await apiFetch(`/sessions/${id}/analysis/report`);
  if (res.ok) return res.json();

  // Backward compatibility (older backend stub route).
  const legacy = await apiFetch(`/reports/${id}`);
  if (!legacy.ok) throw new Error('Failed to fetch report');
  return legacy.json();
}
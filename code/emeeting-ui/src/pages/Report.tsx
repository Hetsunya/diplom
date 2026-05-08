import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReport } from "../api/reports";
import { getSessions } from "../api/sessions";
import type { Session } from "../types/db";

type ReportMode = "single" | "team";
type FaceBehaviorParticipant = {
  participant_id: string;
  events: number;
  trackable_events: number;
  trackable_ratio: number;
  avg_engagement_proxy: number;
};

type FaceBehaviorSummary = {
  events: number;
  trackable_events: number;
  trackable_ratio: number;
  guard_reasons?: Record<string, number>;
  participants?: FaceBehaviorParticipant[];
};

const Report = () => {
  const { id } = useParams();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [serverReport, setServerReport] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<ReportMode>(id ? "single" : "team");

  useEffect(() => {
    setMode(id ? "single" : "team");
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const rows = await getSessions();
        if (!cancelled) setSessions(Array.isArray(rows) ? rows : []);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await getReport(id);
        if (!cancelled) setServerReport(data);
      } catch {
        if (!cancelled) setServerReport(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const sortedSessions = useMemo(
    () =>
      [...sessions].sort(
        (a, b) =>
          new Date(b.startDatetime ?? b.createdAt).getTime() -
          new Date(a.startDatetime ?? a.createdAt).getTime()
      ),
    [sessions]
  );

  const selectedSession = useMemo(
    () => sortedSessions.find((s) => String(s.sessionId) === String(id)),
    [sortedSessions, id]
  );

  const teamStats = useMemo(() => {
    const total = sortedSessions.length;
    const byType = sortedSessions.reduce<Record<string, number>>((acc, s) => {
      const key = s.sessionType || "other";
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    }, {});
    const thisMonth = sortedSessions.filter((s) => {
      const d = new Date(s.startDatetime ?? s.createdAt);
      const now = new Date();
      return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
    }).length;
    return { total, byType, thisMonth };
  }, [sortedSessions]);

  const singleStats = useMemo(() => {
    if (!selectedSession) return null;
    const startedAt = selectedSession.startDatetime
      ? new Date(selectedSession.startDatetime)
      : null;
    const endedAt = selectedSession.endDatetime ? new Date(selectedSession.endDatetime) : null;
    const durationMinutes =
      startedAt && endedAt
        ? Math.max(1, Math.round((endedAt.getTime() - startedAt.getTime()) / (1000 * 60)))
        : null;
    return {
      title: selectedSession.title || `Сессия #${selectedSession.sessionId}`,
      type: selectedSession.sessionType,
      durationMinutes,
      startedAt: startedAt?.toLocaleString() ?? "Не указано",
    };
  }, [selectedSession]);

  const faceBehaviorSummary = useMemo<FaceBehaviorSummary | null>(() => {
    if (!serverReport || typeof serverReport !== "object") return null;
    const top = serverReport as Record<string, unknown>;
    const report =
      top.report && typeof top.report === "object"
        ? (top.report as Record<string, unknown>)
        : top;
    const raw = report.face_behavior_summary;
    if (!raw || typeof raw !== "object") return null;
    const m = raw as Record<string, unknown>;
    const events = Number(m.events);
    const trackableEvents = Number(m.trackable_events);
    const trackableRatio = Number(m.trackable_ratio);
    if (!Number.isFinite(events) || !Number.isFinite(trackableEvents) || !Number.isFinite(trackableRatio)) {
      return null;
    }
    const guardReasonsRaw = m.guard_reasons;
    let guard_reasons: Record<string, number> | undefined;
    if (guardReasonsRaw && typeof guardReasonsRaw === "object") {
      guard_reasons = Object.fromEntries(
        Object.entries(guardReasonsRaw as Record<string, unknown>)
          .filter(([, v]) => Number.isFinite(Number(v)))
          .map(([k, v]) => [k, Number(v)])
      );
    }
    const participantsRaw = m.participants;
    const participants: FaceBehaviorParticipant[] = Array.isArray(participantsRaw)
      ? participantsRaw
          .filter((p): p is Record<string, unknown> => !!p && typeof p === "object")
          .map((p) => ({
            participant_id: String(p.participant_id ?? "unknown"),
            events: Number(p.events ?? 0),
            trackable_events: Number(p.trackable_events ?? 0),
            trackable_ratio: Number(p.trackable_ratio ?? 0),
            avg_engagement_proxy: Number(p.avg_engagement_proxy ?? 0),
          }))
      : [];
    return {
      events,
      trackable_events: trackableEvents,
      trackable_ratio: trackableRatio,
      guard_reasons,
      participants,
    };
  }, [serverReport]);

  return (
    <div className="report-container">
      <header>
        <h1>Отчеты</h1>
        <p className="subtitle">Режимы: по одному звонку и по группе звонков команды.</p>
      </header>

      <div className="summary-box" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button
          type="button"
          className="primary-btn"
          onClick={() => setMode("single")}
          style={{ opacity: mode === "single" ? 1 : 0.75 }}
        >
          По 1 звонку
        </button>
        <button
          type="button"
          className="primary-btn"
          onClick={() => setMode("team")}
          style={{ opacity: mode === "team" ? 1 : 0.75 }}
        >
          По группе звонков
        </button>
      </div>

      {mode === "single" ? (
        <div className="summary-box">
          <h3>Отчет по звонку</h3>
          {!id && (
            <p>
              Выберите сессию из списка:{" "}
              <Link to="/sessions">перейти к сессиям</Link>.
            </p>
          )}
          {id && !selectedSession && <p>Сессия не найдена.</p>}
          {singleStats && (
            <>
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-value engagement">{singleStats.type}</div>
                  <div>Тип сессии</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value neutral">
                    {singleStats.durationMinutes ?? "—"}
                  </div>
                  <div>Длительность, мин</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value stress">{singleStats.startedAt}</div>
                  <div>Старт</div>
                </div>
              </div>
              <p style={{ marginTop: 12 }}>
                <strong>{singleStats.title}</strong>
              </p>
            </>
          )}
          {faceBehaviorSummary && (
            <div className="participant-section" style={{ marginTop: 20 }}>
              <h3>Face Behavior Summary</h3>
              <div className="metrics-grid" style={{ marginTop: 12 }}>
                <div className="metric-card">
                  <div className="metric-value engagement">{faceBehaviorSummary.events}</div>
                  <div>Face events</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value neutral">{faceBehaviorSummary.trackable_events}</div>
                  <div>Trackable events</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value stress">
                    {Math.round(faceBehaviorSummary.trackable_ratio * 100)}%
                  </div>
                  <div>Trackable ratio</div>
                </div>
              </div>
              {faceBehaviorSummary.guard_reasons &&
                Object.keys(faceBehaviorSummary.guard_reasons).length > 0 && (
                  <div style={{ marginTop: 14 }}>
                    <strong>Guard reasons:</strong>{" "}
                    {Object.entries(faceBehaviorSummary.guard_reasons)
                      .map(([reason, count]) => `${reason} (${count})`)
                      .join(", ")}
                  </div>
                )}
              <table className="participants-table" style={{ marginTop: 14 }}>
                <thead>
                  <tr>
                    <th>Участник</th>
                    <th>Событий</th>
                    <th>Trackable</th>
                    <th>Trackable %</th>
                    <th>Avg engagement</th>
                  </tr>
                </thead>
                <tbody>
                  {(faceBehaviorSummary.participants ?? []).map((p) => (
                    <tr key={p.participant_id}>
                      <td>{p.participant_id}</td>
                      <td>{p.events}</td>
                      <td>{p.trackable_events}</td>
                      <td>{Math.round(p.trackable_ratio * 100)}%</td>
                      <td>{Number.isFinite(p.avg_engagement_proxy) ? p.avg_engagement_proxy.toFixed(2) : "—"}</td>
                    </tr>
                  ))}
                  {(faceBehaviorSummary.participants ?? []).length === 0 && (
                    <tr>
                      <td colSpan={5}>Нет participant breakdown</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="summary-box">
          <h3>Отчет по команде (группа звонков)</h3>
          {loading ? (
            <p>Загрузка...</p>
          ) : (
            <>
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-value engagement">{teamStats.total}</div>
                  <div>Всего звонков</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value neutral">{teamStats.thisMonth}</div>
                  <div>За текущий месяц</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value stress">{Object.keys(teamStats.byType).length}</div>
                  <div>Типов встреч</div>
                </div>
              </div>
              <div className="participant-section">
                <table className="participants-table">
                  <thead>
                    <tr>
                      <th>Тип</th>
                      <th>Количество</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(teamStats.byType).map(([type, count]) => (
                      <tr key={type}>
                        <td>{type}</td>
                        <td>{count}</td>
                      </tr>
                    ))}
                    {Object.keys(teamStats.byType).length === 0 && (
                      <tr>
                        <td colSpan={2}>Нет данных</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      <div className="recommendations">
        <h3>Черновой контракт бэка под отчеты</h3>
        <ul>
          <li>GET `/reports/session/:sessionId` — итог по одному звонку.</li>
          <li>GET `/reports/team?from=&to=&groupBy=` — агрегат по группе звонков.</li>
          <li>GET `/reports/team/trends?metric=` — временные ряды для графиков.</li>
          <li>Рекомендуемый payload: `summary`, `transcription`, `participants`, `qualityFlags`.</li>
          <li>Пока AI-модуль не финален, UI использует fallback на `sessions`.</li>
        </ul>
      </div>

      {Boolean(serverReport) && mode === "single" && (
        <div className="summary-box">
          <h3>Сырые данные отчета (debug)</h3>
          <pre style={{ overflow: "auto", maxHeight: 320 }}>{JSON.stringify(serverReport, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default Report;
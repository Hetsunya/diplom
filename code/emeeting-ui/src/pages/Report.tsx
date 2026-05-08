import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReport } from "../api/reports";
import { getSessions } from "../api/sessions";
import type { Session } from "../types/db";

type ReportMode = "single" | "team";

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
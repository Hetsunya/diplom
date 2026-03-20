// src/pages/Report.tsx
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getReport } from '../api/reports';
import { useSessionWS } from '../hooks/useSessionWS';

const Report = () => {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [emotionCounts, setEmotionCounts] = useState<Record<string, number>>({});
  const [emotionTotal, setEmotionTotal] = useState(0);
  const participantId = sessionStorage.getItem('report_participant_id') || 'report_viewer';

  const normalizeEmotionLabel = (raw: string) => {
    const normalized = raw.toLowerCase();
    if (normalized.includes("happy")) return "Happy";
    if (normalized.includes("surpris")) return "Surprised";
    if (normalized.includes("neutral")) return "Neutral";
    if (normalized.includes("fear") || normalized.includes("disgust")) return "Engaged";
    if (normalized.includes("sad")) return "Focused";
    if (normalized.includes("angry")) return "Thoughtful";
    return raw;
  };

  useSessionWS(id!, participantId, (msg) => {
    if (typeof msg !== 'object' || msg === null) return;
    const m = msg as {
      type?: unknown;
      participant_id?: unknown;
      payload?: unknown;
    };
    if (m.type !== 'emotion') return;

    const payload = m.payload;
    const pid = typeof m.participant_id === 'string' ? m.participant_id : undefined;
    if (!pid) return;

    // Flexible parsing of emotion payload.
    let label: string | undefined;
    if (payload && typeof payload === 'object') {
      const p = payload as Record<string, unknown>;
      if (typeof p.emotion === 'string') label = p.emotion;
      if (!label && p.probs && typeof p.probs === 'object') {
        let bestKey: string | null = null;
        let bestVal = -1;
        for (const [k, v] of Object.entries(p.probs as Record<string, unknown>)) {
          if (typeof v !== 'number') continue;
          if (v > bestVal) {
            bestVal = v;
            bestKey = k;
          }
        }
        if (bestKey) label = bestKey;
      }
    }

    if (!label) return;

    const normalizedLabel = normalizeEmotionLabel(label!);
    setEmotionCounts((prev) => ({
      ...prev,
      [normalizedLabel]: (prev[normalizedLabel] ?? 0) + 1,
    }));
    setEmotionTotal((t) => t + 1);
  });

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await getReport(id!);
        setReport(data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchReport();
  }, [id]);

  return (
    <div className="report-container">
      <header>
        <h1>Отчет по сессии {id}</h1>
      </header>
      <div className="summary-box">
        {/* Саммари */}
      </div>
      <div className="metrics-grid">
        {/* Метрики */}
      </div>
      <div className="charts-section">
        {/* Чарты */}
      </div>
      <div className="participant-section">
        <table className="participants-table">
          {/* Таблица участников */}
        </table>
      </div>
      <div className="recommendations">
        <h3>Рекомендации</h3>
        <ul>
          {/* Рекомендации */}
        </ul>
      </div>

      <div className="summary-box" style={{ marginTop: 20 }}>
        <h2>Эмоции (aggregated)</h2>
        {emotionTotal === 0 ? (
          <p style={{ color: '#7f8c8d' }}>Пока AI не прислал данные об эмоциях.</p>
        ) : (
          <table className="participants-table" style={{ marginTop: 10 }}>
            <thead>
              <tr>
                <th>Эмоция</th>
                <th>Доля</th>
                <th>Событий</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(emotionCounts)
                .sort((a, b) => b[1] - a[1])
                .map(([emotion, count]) => {
                  const pct = Math.round((count / emotionTotal) * 100);
                  return (
                    <tr key={emotion}>
                      <td>{emotion}</td>
                      <td>{pct}%</td>
                      <td>{count}</td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        )}
      </div>

      {report && <pre>{JSON.stringify(report, null, 2)}</pre>}
    </div>
  );
};

export default Report;
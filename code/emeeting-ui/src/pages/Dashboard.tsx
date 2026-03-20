// src/pages/Dashboard.tsx
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { getSessions } from '../api/sessions';
import type { Session } from '../types/db';

const Dashboard = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    getSessions().then(setSessions).catch(console.error);
  }, []);

  const goToNewSession = () => {
    navigate('/sessions/new');
  };

  const stats = useMemo(() => {
    const total = sessions.length;
    const meetings = sessions.filter((s) => s.sessionType === 'meeting').length;
    const interviews = sessions.filter((s) => s.sessionType === 'interview').length;
    return { total, meetings, interviews };
  }, [sessions]);

  const formatDate = (value: string) => {
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? 'Не указано' : d.toLocaleString();
  };

  return (
    <div className="dashboard-container">
      <header>
        <h1>Дашборд</h1>
        {user && <p className="subtitle">Добро пожаловать, {user.email}</p>}
      </header>

      <div className="stats-overview">
        <div className="stat-card">
          <div className="stat-value engagement">{stats.total}</div>
          <div>Всего сессий</div>
        </div>

        <div className="stat-card">
          <div className="stat-value engagement">{stats.meetings}</div>
          <div>Meeting</div>
        </div>

        <div className="stat-card">
          <div className="stat-value stress">{stats.interviews}</div>
          <div>Interview</div>
        </div>
      </div>

      <div className="sessions-list">
        <h2>Сессии</h2>
        <table className="dashboard-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Тип</th>
              <th>Старт</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.sessionId}>
                <td>{s.title}</td>
                <td>{s.sessionType}</td>
                <td>{s.startDatetime ? formatDate(s.startDatetime) : 'Не указано'}</td>
                <td>
                  <Link to={`/sessions/${s.sessionId}`}>Открыть</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="action-buttons">
        <button className="primary-btn" onClick={goToNewSession}>
          Создать сессию
        </button>
      </div>
    </div>
  );
};

export default Dashboard;

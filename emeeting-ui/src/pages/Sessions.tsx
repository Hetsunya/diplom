// src/pages/Sessions.tsx
import { useEffect, useState } from 'react';
import { getSessions } from '../api/sessions';
import SessionCard from '../components/SessionCard';
import { Link } from 'react-router-dom';

const Sessions = () => {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const data = await getSessions();
        setSessions(data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchSessions();
  }, []);

  return (
    <div>
      <header>
        <h1>Сессии</h1>
      </header>
      <div className="date-filter">
        <input type="date" />
      </div>
      <table className="sessions-table">
        <thead>
          <tr>
            <th>Название</th>
            <th>Дата</th>
            <th>Статус</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((session: any) => (
            <SessionCard key={session.id} session={session} />
          ))}
        </tbody>
      </table>
      <div className="page-actions">
        <Link className="secondary-btn" to="/sessions/new">Новая сессия</Link>
      </div>
      <div className="calendar-section">
        <div className="calendar">
          {/* Календарь */}
        </div>
      </div>
    </div>
  );
};

export default Sessions;
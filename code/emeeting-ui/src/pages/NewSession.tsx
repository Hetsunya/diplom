import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createSession } from '../api/sessions';
import type { SessionType, CreateSessionDTO } from '../types/db';

const NewSession = () => {
  const [title, setTitle] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [sessionType, setSessionType] = useState<SessionType>('meeting'); // выбор типа
  const navigate = useNavigate();

  const submit = async () => {
    try {
      const payload: CreateSessionDTO = {
        title,
        startDatetime: scheduledAt,
        sessionType,
      };
      await createSession(payload);
      navigate('/sessions');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="new-session-form">
      <h2>Создание новой сессии</h2>
      <div className="form-row">
        <label>Название</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} />
      </div>
      <div className="form-row">
        <label>Дата и время</label>
        <input
          type="datetime-local"
          value={scheduledAt}
          onChange={(e) => setScheduledAt(e.target.value)}
        />
      </div>
      <div className="form-row">
        <label>Тип сессии</label>
        <select value={sessionType} onChange={(e) => setSessionType(e.target.value as SessionType)}>
          <option value="meeting">Встреча</option>
          <option value="interview">Собеседование</option>
          <option value="assessment">Оценка</option>
          <option value="other">Другое</option>
        </select>
      </div>
      <button onClick={submit}>Создать</button>
    </div>
  );
};

export default NewSession;

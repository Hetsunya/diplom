// src/pages/NewSession.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createSession } from '../api/sessions';

const NewSession = () => {
  const [title, setTitle] = useState('');
  const navigate = useNavigate();

  const submit = async () => {
    try {
      await createSession({ title });
      navigate('/sessions');
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="new-session-form">
      <h2>Создание новой сессии</h2>
      <div className="form-step">
        <div className="form-row">
          <div className="form-group">
            <label>Название</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
        </div>
        <div className="form-actions">
          <button className="back-btn">Назад</button>
          <button className="primary-btn" onClick={submit}>Создать</button>
        </div>
      </div>
    </div>
  );
};

export default NewSession;
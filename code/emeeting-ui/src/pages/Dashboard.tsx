// src/pages/Dashboard.tsx
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

const Dashboard = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const goToNewSession = () => {
    navigate('/sessions/new');
  };

  return (
    <div className="dashboard-container">
      <header>
        <h1>Дашборд</h1>
        {user && <p className="subtitle">Добро пожаловать, {user.email}</p>}
      </header>

      <div className="stats-overview">
        {/* Добавить статистики если есть данные */}
      </div>

      <div className="sessions-list">
        <h2>Недавние сессии</h2>
        <table className="dashboard-table">
          {/* Таблица сессий */}
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

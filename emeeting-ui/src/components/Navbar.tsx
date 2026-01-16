// src/components/Navbar.tsx
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { logout } from '../api/auth';

const Navbar = () => {
  const { isAuthenticated, setAuth } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    setAuth(null);
  };

  return (
    <nav>
      <Link to="/">Главная</Link>
      <Link to="/sessions">Сессии</Link>
      {isAuthenticated ? (
        <button className="action-btn" onClick={handleLogout}>Выйти</button>
      ) : (
        <Link className="action-btn" to="/login">Войти</Link>
      )}
    </nav>
  );
};

export default Navbar;
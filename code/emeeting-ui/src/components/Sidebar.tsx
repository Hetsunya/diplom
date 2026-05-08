import { Link, useLocation, useNavigate } from "react-router-dom";
import { featureRoutes } from "../config/features";
import { useAuthStore } from "../store/authStore";
import { logout } from "../api/auth";

const Sidebar = () => {
  const { isAuthenticated, user, setAuth } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      setAuth(null);
      navigate("/login");
    }
  };

  const navItems = featureRoutes.filter((f) => f.enabled && f.nav);

  return (
    <aside className="sidebar">
      <div className="sidebar__logo">
        <div className="sidebar__logo-badge" aria-hidden>
          <svg width="36" height="36" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="40" height="40" rx="12" fill="#3498db" />
            <path
              d="M12 26V14l8 6 8-6v12"
              stroke="white"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          </svg>
        </div>
        <div className="sidebar__logo-title">
          <div className="sidebar__title">eMeeting</div>
          <div className="sidebar__subtitle">
            {isAuthenticated ? user?.email ?? "Авторизован" : "Гость"}
          </div>
        </div>
      </div>

      <nav className="sidebar__nav">
        {navItems.map((f) => (
          <Link
            key={f.key}
            to={f.nav!.to}
            className={`sidebar__link ${
              location.pathname === f.nav!.to ? "active" : ""
            }`}
          >
            {f.nav!.label}
          </Link>
        ))}
      </nav>

      <div className="sidebar__footer">
        {isAuthenticated ? (
          <button className="sidebar__logout" onClick={handleLogout} type="button">
            Выйти
          </button>
        ) : (
          <Link className="sidebar__login" to="/login">
            Войти
          </Link>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;


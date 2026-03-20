import { Link, useLocation, useNavigate } from "react-router-dom";
import { featureRoutes } from "../config/features";
import { useAuthStore } from "../store/authStore";
import { logout } from "../api/auth";

const Sidebar = () => {
  const { isAuthenticated, setAuth } = useAuthStore();
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
        <div className="sidebar__logo-badge">e</div>
        <div className="sidebar__logo-title">
          <div className="sidebar__title">eMeeting</div>
          <div className="sidebar__subtitle">
            {isAuthenticated ? "Authorized" : "Guest"}
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


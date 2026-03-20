// src/components/Layout.tsx
import Sidebar from './Sidebar';

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-content">
        <main>{children}</main>
        <footer>© 2026 EMeeting. Все права защищены.</footer>
      </div>
    </div>
  );
};

export default Layout;
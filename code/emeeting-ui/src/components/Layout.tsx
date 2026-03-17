// src/components/Layout.tsx
import Navbar from './Navbar';

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="container">
      <Navbar />
      <main>{children}</main>
      <footer>© 2026 EMeeting. Все права защищены.</footer>
    </div>
  );
};

export default Layout;
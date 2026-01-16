// src/router.tsx
import { createBrowserRouter } from 'react-router-dom';
import App from './App';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Sessions from './pages/Sessions';
import NewSession from './pages/NewSession';
import VideoMeet from './pages/VideoMeet';
import Report from './pages/Report';
// import Configs from './pages/Configs'; // Если нужно

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/sessions', element: <Sessions /> },
      { path: '/sessions/new', element: <NewSession /> },
      { path: '/sessions/:id', element: <VideoMeet /> },
      { path: '/reports/:id', element: <Report /> },
      // { path: '/configs', element: <Configs /> },
    ],
  },
  { path: '/login', element: <Login /> },
]);

export default router;
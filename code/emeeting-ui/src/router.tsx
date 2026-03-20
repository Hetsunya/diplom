// src/router.tsx
import { createBrowserRouter } from 'react-router-dom';
import App from './App';
import { featureRoutes, publicRoutes } from "./config/features";

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      ...featureRoutes
        .filter((f) => f.enabled)
        .map((f) => {
          const Component = f.component;
          return { path: f.path, element: <Component /> };
        }),
    ],
  },
  ...publicRoutes
    .filter((r) => r.enabled)
    .map((r) => {
      const Component = r.component;
      return { path: r.path, element: <Component /> };
    }),
]);

export default router;
import { createBrowserRouter, Navigate, type RouteObject } from 'react-router-dom';
import { AppShell } from '../components/shared/AppShell';
import { ProjectsPage } from '../pages/ProjectsPage';
import { WorkspacePage } from '../pages/WorkspacePage';
import { ReportsPage } from '../pages/ReportsPage';
import { SettingsPage } from '../pages/SettingsPage';

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <Navigate to="/projects" replace />,
      },
      {
        path: 'projects',
        element: <ProjectsPage />,
      },
      {
        path: 'workspace',
        element: <WorkspacePage />,
      },
      {
        path: 'reports',
        element: <ReportsPage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      {
        path: '*',
        element: <Navigate to="/projects" replace />,
      },
    ],
  },
];

export const router = createBrowserRouter(routes);

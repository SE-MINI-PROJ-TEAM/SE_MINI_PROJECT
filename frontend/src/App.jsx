import { Suspense } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './core/auth/AuthContext.jsx';
import { AppShell } from './core/layout/AppShell.jsx';
import DashboardPage from './core/pages/DashboardPage.jsx';
import LoginPage from './core/pages/LoginPage.jsx';
import { ForbiddenPage, NotFoundPage } from './core/pages/NotFoundPage.jsx';
import { routes } from './core/registry.js';
import { LoadingState } from './core/ui/index.js';

/** Authentication, temporary-password gate and role check for one route. */
function Guard({ route, children }) {
  const { user, status } = useAuth();
  const location = useLocation();

  if (status === 'loading') return <LoadingState label="Loading your workspace…" />;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  if (user.must_change_password && !route.allowTemp) return <Navigate to="/change-password" replace />;
  if (route.roles && !route.roles.includes(user.role)) return <ForbiddenPage />;
  return <Suspense fallback={<LoadingState />}>{children}</Suspense>;
}

function ShellLayout() {
  const { user, status } = useAuth();
  if (status === 'loading') return <LoadingState label="Loading your workspace…" />;
  if (!user) return <Navigate to="/login" replace />;
  return <AppShell />;
}

export default function App() {
  const bare = routes.filter((r) => r.layout === 'bare');
  const inShell = routes.filter((r) => r.layout !== 'bare');

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      {bare.map(({ path, component: Page, ...route }) => (
        <Route
          key={path}
          path={path}
          element={
            <Guard route={route}>
              <Page />
            </Guard>
          }
        />
      ))}
      <Route element={<ShellLayout />}>
        <Route index element={<Guard route={{}}><DashboardPage /></Guard>} />
        {inShell.map(({ path, component: Page, ...route }) => (
          <Route
            key={path}
            path={path}
            element={
              <Guard route={route}>
                <Page />
              </Guard>
            }
          />
        ))}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { Spinner } from '../components/ui/Spinner';
import { useAuth } from '../hooks/useAuth';

/**
 * Convenience only. The backend rejects unauthenticated API calls regardless of
 * what the router does, so this guard is about UX, not security.
 */
export function ProtectedRoute() {
  const { status } = useAuth();
  const location = useLocation();

  // Without this, a browser refresh would flash the login page before /auth/me
  // has had a chance to answer.
  if (status === 'loading') {
    return (
      <div className="route-loading">
        <Spinner label="Checking your session" />
      </div>
    );
  }

  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

import { Navigate, Outlet } from 'react-router-dom';

import { Spinner } from '../components/ui/Spinner';
import { useAuth } from '../hooks/useAuth';

/** Keeps signed-in users out of the login and signup screens. */
export function GuestRoute() {
  const { status } = useAuth();

  if (status === 'loading') {
    return (
      <div className="route-loading">
        <Spinner label="Checking your session" />
      </div>
    );
  }

  return status === 'authenticated' ? <Navigate to="/gigs" replace /> : <Outlet />;
}

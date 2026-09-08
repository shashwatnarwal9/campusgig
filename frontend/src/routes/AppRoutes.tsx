import { Navigate, Route, Routes } from 'react-router-dom';

import { AppLayout } from '../layouts/AppLayout';
import { AppliedGigsPage } from '../pages/AppliedGigsPage';
import { GigDetailsPage } from '../pages/GigDetailsPage';
import { GigsPage } from '../pages/GigsPage';
import { LoginPage } from '../pages/LoginPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { ProfilePage } from '../pages/ProfilePage';
import { SignupPage } from '../pages/SignupPage';
import { GuestRoute } from './GuestRoute';
import { ProtectedRoute } from './ProtectedRoute';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/gigs" replace />} />
      {/* /dashboard was the old name for the gigs board; keep the link working. */}
      <Route path="/dashboard" element={<Navigate to="/gigs" replace />} />

      <Route element={<GuestRoute />}>
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/gigs" element={<GigsPage />} />
          <Route path="/gigs/:gigId" element={<GigDetailsPage />} />
          <Route path="/applied" element={<AppliedGigsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

import { BrowserRouter } from 'react-router-dom';

import { AuthProvider } from './context/AuthProvider';
import { ProfileProvider } from './context/ProfileProvider';
import { AppRoutes } from './routes/AppRoutes';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ProfileProvider>
          <AppRoutes />
        </ProfileProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

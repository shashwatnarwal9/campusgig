import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react';

import { UNAUTHORIZED_EVENT } from '../services/apiClient';
import { authApi } from '../services/authApi';
import type { User } from '../types/auth';
import { AuthContext, type AuthStatus } from './authContext';

/**
 * Holds the current user only. The session itself lives in an HttpOnly cookie,
 * so nothing sensitive is kept in React state, localStorage or sessionStorage.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');

  const refresh = useCallback(async () => {
    try {
      const current = await authApi.me();
      setUser(current);
      setStatus('authenticated');
    } catch {
      // Covers both "no session" (401) and "server unreachable". Either way the
      // app must settle on anonymous rather than spin on the loading state.
      setUser(null);
      setStatus('anonymous');
    }
  }, []);

  // Rehydrate on mount so a browser refresh keeps the user signed in.
  useEffect(() => {
    void refresh();
  }, [refresh]);

  // The server can expire a session at any time; the API client tells us.
  useEffect(() => {
    const handle = () => {
      setUser(null);
      setStatus('anonymous');
    };
    window.addEventListener(UNAUTHORIZED_EVENT, handle);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handle);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const authenticated = await authApi.login(email, password);
    setUser(authenticated);
    setStatus('authenticated');
    return authenticated;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      setStatus('anonymous');
    }
  }, []);

  const value = useMemo(
    () => ({ user, status, login, logout, refresh }),
    [user, status, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

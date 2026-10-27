import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react';

import { useAuth } from '../hooks/useAuth';
import { errorMessage } from '../services/apiClient';
import { profileApi } from '../services/profileApi';
import type { Profile } from '../types/profile';
import { ProfileContext } from './profileContext';

/** Loaded once per session and shared, so the header avatar and the profile
 *  page cannot disagree about what the picture is. */
export function ProfileProvider({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setProfile(await profileApi.get());
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (status === 'authenticated') {
      void reload();
    } else {
      setProfile(null);
    }
  }, [status, reload]);

  const value = useMemo(
    () => ({ profile, loading, error, setProfile, reload }),
    [profile, loading, error, reload],
  );

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

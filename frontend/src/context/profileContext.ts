import { createContext } from 'react';
import type { Profile } from '../types/profile';

export interface ProfileContextValue {
  profile: Profile | null;
  loading: boolean;
  error: string | null;
  /** Pages that change the profile push the server's reply back here so the
   *  header avatar updates without a second round trip. */
  setProfile: (profile: Profile) => void;
  reload: () => Promise<void>;
}

export const ProfileContext = createContext<ProfileContextValue | null>(null);

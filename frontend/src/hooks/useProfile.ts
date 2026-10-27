import { useContext } from 'react';
import { ProfileContext, type ProfileContextValue } from '../context/profileContext';

export function useProfile(): ProfileContextValue {
  const context = useContext(ProfileContext);
  if (!context) throw new Error('useProfile must be used inside <ProfileProvider>');
  return context;
}

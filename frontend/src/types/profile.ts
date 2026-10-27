import type { UserRole } from './auth';

export interface Profile {
  id: string;
  email: string;
  roll_no: string;
  dept: string;
  batch: number;
  role: UserRole;
  created_at: string;
  bio: string | null;
  avatar_url: string | null;
  resume_url: string | null;
}

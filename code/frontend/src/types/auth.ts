export type UserRole = 'STUDENT' | 'ADMIN';

export interface User {
  id: string;
  email: string;
  roll_no: string;
  dept: string;
  batch: number;
  role: UserRole;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  roll_no: string;
  dept: string;
  batch: number;
}

export interface RegisterResult {
  user_id: string;
  email: string;
  message: string;
}

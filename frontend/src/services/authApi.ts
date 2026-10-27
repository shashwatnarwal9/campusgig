import { request } from './apiClient';
import type { RegisterPayload, RegisterResult, User } from '../types/auth';

export const authApi = {
  register: (payload: RegisterPayload) =>
    request<RegisterResult>('/api/v1/auth/register', { method: 'POST', body: payload }),

  login: (email: string, password: string) =>
    request<User>('/api/v1/auth/login', { method: 'POST', body: { email, password } }),

  logout: () => request<{ message: string }>('/api/v1/auth/logout', { method: 'POST' }),

  me: (signal?: AbortSignal) => request<User>('/api/v1/auth/me', { signal }),
};

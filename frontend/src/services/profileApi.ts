import { request } from './apiClient';
import type { Profile } from '../types/profile';

function upload(path: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return request<Profile>(path, { method: 'POST', formData });
}

export const profileApi = {
  get: (signal?: AbortSignal) => request<Profile>('/api/v1/profile', { signal }),

  updateBio: (bio: string) => request<Profile>('/api/v1/profile', { method: 'PATCH', body: { bio } }),

  uploadAvatar: (file: File) => upload('/api/v1/profile/avatar', file),

  uploadResume: (file: File) => upload('/api/v1/profile/resume', file),
};

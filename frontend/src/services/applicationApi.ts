import { request } from './apiClient';
import type { ApplicationStatus, GigApplicant, MyApplication, MyApplications } from '../types/application';

export const applicationApi = {
  mine: (signal?: AbortSignal) => request<MyApplications>('/api/v1/applications/me', { signal }),

  setStatus: (applicationId: string, status: ApplicationStatus) =>
    request<MyApplication>(`/api/v1/applications/${applicationId}`, {
      method: 'PATCH',
      body: { status },
    }),

  forGig: (gigId: string, signal?: AbortSignal) =>
    request<GigApplicant[]>(`/api/v1/gigs/${gigId}/applications`, { signal }),
};

import { request } from './apiClient';
import type { MyApplication } from '../types/application';
import type { GigCreatePayload, GigDetail, GigQuery, GigSummary, Page } from '../types/gig';

export const gigApi = {
  list: (query: GigQuery, signal?: AbortSignal) =>
    request<Page<GigSummary>>('/api/v1/gigs', { query: { ...query }, signal }),

  get: (gigId: string, signal?: AbortSignal) =>
    request<GigDetail>(`/api/v1/gigs/${gigId}`, { signal }),

  create: (payload: GigCreatePayload) =>
    request<GigDetail>('/api/v1/gigs', { method: 'POST', body: payload }),

  mine: (signal?: AbortSignal) => request<GigDetail[]>('/api/v1/gigs/mine', { signal }),

  apply: (gigId: string, message: string | null) =>
    request<MyApplication>(`/api/v1/gigs/${gigId}/apply`, { method: 'POST', body: { message } }),
};

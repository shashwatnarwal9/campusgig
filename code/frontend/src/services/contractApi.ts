import { request } from './apiClient';
import type { ContractDetail, ContractSummary } from '../types/application';
import type { Page } from '../types/gig';

export const contractApi = {
  list: (query: { page?: number; page_size?: number }, signal?: AbortSignal) =>
    request<Page<ContractSummary>>('/api/v1/contracts', { query: { ...query }, signal }),

  get: (contractId: string, signal?: AbortSignal) =>
    request<ContractDetail>(`/api/v1/contracts/${contractId}`, { signal }),
};

import type { GigSummary, Poster } from './gig';

export const APPLICATION_STATUSES = ['APPLIED', 'ACCEPTED', 'REJECTED', 'COMPLETED'] as const;

export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

export interface MyApplication {
  id: string;
  status: ApplicationStatus;
  message: string | null;
  created_at: string;
  updated_at: string;
  gig: GigSummary;
}

export interface GigApplicant {
  id: string;
  status: ApplicationStatus;
  message: string | null;
  created_at: string;
  applicant: Poster;
}

export interface ApplicationSummary {
  total: number;
  applied: number;
  accepted: number;
  rejected: number;
  completed: number;
  /** Budget of completed work. No payment system exists yet. */
  earned: string;
  in_progress_value: string;
}

export interface MyApplications {
  summary: ApplicationSummary;
  items: MyApplication[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export const CONTRACT_STATUSES = [
  'OPEN',
  'ACCEPTED',
  'DELIVERED',
  'REVISION',
  'DISPUTED',
  'RELEASED',
  'REFUNDED',
  'SPLIT',
] as const;

export type ContractStatus = (typeof CONTRACT_STATUSES)[number];

export interface ContractHistoryItem {
  previous_status: ContractStatus;
  new_status: ContractStatus;
  actor: Poster;
  created_at: string;
}

export interface ContractSummary {
  id: string;
  gig_id: string;
  status: ContractStatus;
  gig_title: string;
  amount_paise: number;
  created_at: string;
  poster: Poster;
  worker: Poster;
}

export interface ContractDetail extends ContractSummary {
  application_id: string;
  gig_description: string;
  gig_category: GigSummary['category'];
  deadline: string;
  duration_days: number | null;
  confirmation_deadline: string | null;
  revisions_used: number;
  updated_at: string;
  history: ContractHistoryItem[];
}

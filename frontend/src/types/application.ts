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
}

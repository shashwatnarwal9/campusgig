export const GIG_CATEGORIES = [
  'ACADEMIC_HELP',
  'DESIGN',
  'DEVELOPMENT',
  'WRITING',
  'TUTORING',
  'EVENTS',
  'PHOTOGRAPHY',
  'OTHER',
] as const;

export type GigCategory = (typeof GIG_CATEGORIES)[number];

export type GigState = 'OPEN' | 'CLOSED';

export type GigSort = 'newest' | 'deadline' | 'budget_asc' | 'budget_desc';

export interface Poster {
  id: string;
  roll_no: string;
  dept: string;
  batch: number;
}

export interface GigSummary {
  id: string;
  title: string;
  category: GigCategory;
  short_description: string;
  budget: string;
  deadline: string;
  duration_days: number | null;
  state: GigState;
  created_at: string;
  poster: Poster;
}

export interface GigDetail {
  id: string;
  title: string;
  category: GigCategory;
  description: string;
  budget: string;
  deadline: string;
  duration_days: number | null;
  state: GigState;
  created_at: string;
  updated_at: string;
  poster: Poster;
}

export interface GigCreatePayload {
  title: string;
  description: string;
  category: GigCategory;
  budget: string;
  deadline: string;
  duration_days: number | null;
}

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface GigQuery {
  page?: number;
  page_size?: number;
  q?: string;
  category?: GigCategory | '';
  min_budget?: string;
  max_budget?: string;
  deadline_before?: string;
  sort?: GigSort;
}

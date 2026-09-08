/**
 * The only place that knows the backend URL or calls fetch.
 *
 * Session credentials travel in an HttpOnly cookie, so `credentials: 'include'`
 * is set on every request and no token is ever read or stored by this code.
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

export const UNAUTHORIZED_EVENT = 'campusgig:unauthorized';

export interface ApiFieldError {
  field: string;
  message: string;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly fields?: ApiFieldError[],
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor() {
    super('Could not reach the CampusGig server. Check your connection and try again.');
    this.name = 'NetworkError';
  }
}

type QueryValue = string | number | undefined | null;

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH';
  body?: unknown;
  /** Sent as multipart/form-data; the browser sets the boundary itself. */
  formData?: FormData;
  query?: Record<string, QueryValue>;
  signal?: AbortSignal;
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = new URL(`${BASE_URL}${path}`);
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, formData, query, signal } = options;

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      credentials: 'include',
      // Never set Content-Type for FormData: fetch must add the multipart boundary.
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: formData ?? (body === undefined ? undefined : JSON.stringify(body)),
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new NetworkError();
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401) {
      // Lets the auth provider drop a session the server has already dropped.
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    const detail = (payload as { detail?: Record<string, unknown> } | null)?.detail;
    throw new ApiError(
      response.status,
      (detail?.code as string) ?? 'unknown_error',
      (detail?.message as string) ?? 'Something went wrong. Please try again.',
      detail?.fields as ApiFieldError[] | undefined,
    );
  }

  return payload as T;
}

/** Absolute URL for a path the API returned, such as an uploaded file. */
export function mediaUrl(path: string | null | undefined): string | undefined {
  if (!path) return undefined;
  return path.startsWith('http') ? path : `${BASE_URL}${path}`;
}

/** Human-readable message for anything thrown by `request`. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const first = error.fields?.[0];
    return first ? `${first.field}: ${first.message}` : error.message;
  }
  if (error instanceof NetworkError) return error.message;
  return 'Something went wrong. Please try again.';
}

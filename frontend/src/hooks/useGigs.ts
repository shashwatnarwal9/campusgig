import { useEffect, useState } from 'react';

import { errorMessage } from '../services/apiClient';
import { gigApi } from '../services/gigApi';
import type { GigQuery, GigSummary, Page } from '../types/gig';

interface GigsState {
  page: Page<GigSummary> | null;
  loading: boolean;
  error: string | null;
}

/**
 * @param reloadKey bump to refetch the same query, e.g. after posting a gig.
 *   Kept out of `query` so it never reaches the API as a stray parameter.
 */
export function useGigs(query: GigQuery, reloadKey = 0): GigsState {
  const [state, setState] = useState<GigsState>({ page: null, loading: true, error: null });

  // Serialising the query keeps the effect from re-firing on every render just
  // because the caller built a fresh object literal.
  const key = JSON.stringify(query);

  useEffect(() => {
    const controller = new AbortController();
    setState((current) => ({ ...current, loading: true, error: null }));

    gigApi
      .list(JSON.parse(key) as GigQuery, controller.signal)
      .then((page) => setState({ page, loading: false, error: null }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({ page: null, loading: false, error: errorMessage(error) });
      });

    return () => controller.abort();
  }, [key, reloadKey]);

  return state;
}

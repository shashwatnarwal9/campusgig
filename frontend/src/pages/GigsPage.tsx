import { AnimatePresence, motion } from 'framer-motion';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { CategoryStrip } from '../components/gigs/CategoryStrip';
import { FilterControls } from '../components/gigs/FilterControls';
import { GigCard } from '../components/gigs/GigCard';
import { Pagination } from '../components/gigs/Pagination';
import { PostGigDialog } from '../components/gigs/PostGigDialog';
import { Alert } from '../components/ui/Alert';
import { EmptyState } from '../components/ui/EmptyState';
import { Spinner } from '../components/ui/Spinner';
import { useAuth } from '../hooks/useAuth';
import { useGigs } from '../hooks/useGigs';
import type { GigCategory, GigQuery } from '../types/gig';

const PAGE_SIZE = 12;

const DEFAULT_FILTERS: GigQuery = {
  q: '',
  category: '',
  min_budget: '',
  max_budget: '',
  deadline_before: '',
  sort: 'newest',
};

export function GigsPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();

  const [filters, setFilters] = useState<GigQuery>({
    ...DEFAULT_FILTERS,
    q: params.get('q') ?? '',
  });
  const [page, setPage] = useState(1);
  const [posting, setPosting] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [notice, setNotice] = useState<string | null>(
    params.get('posted') ? 'Your gig is live. Students can apply now.' : null,
  );

  // The topbar search navigates here with ?q=..., so the board follows the URL.
  const urlQuery = params.get('q') ?? '';
  useEffect(() => {
    setFilters((current) => (current.q === urlQuery ? current : { ...current, q: urlQuery }));
    setPage(1);
  }, [urlQuery]);

  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(null), 6000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const query = useMemo<GigQuery>(
    () => ({ ...filters, page, page_size: PAGE_SIZE }),
    [filters, page],
  );

  const { page: result, loading, error } = useGigs(query, reloadKey);

  const applyFilters = (patch: Partial<GigQuery>) => {
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1); // a narrowed result set makes the old page number meaningless
  };

  const resetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setPage(1);
    setParams({}, { replace: true });
  };

  const hasActiveFilters = Object.entries(DEFAULT_FILTERS).some(
    ([key, value]) => filters[key as keyof GigQuery] !== value,
  );

  return (
    <div className="dashboard">
      <header className="dashboard__header dashboard__header--hero">
        <div>
          <h1 className="dashboard__title">
            Unlock Your <em>Campus Gig!</em>
          </h1>
          <p className="dashboard__welcome">
            Welcome back, {user?.roll_no ?? 'student'}. Here is what the campus needs help with
            right now.
          </p>
        </div>
        {result ? (
          <span className="count-pill">
            ⚡ {result.total} open gig{result.total === 1 ? '' : 's'}
          </span>
        ) : null}
      </header>

      <CategoryStrip
        active={(filters.category ?? '') as GigCategory | ''}
        onSelect={(category) => applyFilters({ category })}
      />

      <FilterControls filters={filters} onChange={applyFilters} onReset={resetFilters} />

      <AnimatePresence>
        {notice ? (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Alert tone="success">{notice}</Alert>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {error ? <Alert tone="error">{error}</Alert> : null}

      <div className="section-head">
        <span className="section-head__bar" aria-hidden="true" />
        <h2 className="section-head__title">
          {filters.q ? `Results for "${filters.q}"` : 'Available gigs'}
        </h2>
      </div>

      {loading ? (
        <div className="dashboard__loading">
          <Spinner label="Loading gigs" />
        </div>
      ) : null}

      {!loading && !error && result ? (
        result.items.length === 0 ? (
          <EmptyState
            title="No gigs match your search"
            description={
              hasActiveFilters
                ? 'Try another category, widen the budget range, or clear the filters.'
                : 'Nothing has been posted yet. Be the first — tap Post a gig.'
            }
            action={
              hasActiveFilters ? (
                <button className="btn btn--secondary" type="button" onClick={resetFilters}>
                  Clear filters
                </button>
              ) : null
            }
          />
        ) : (
          <>
            <motion.div
              className="gig-grid"
              initial="hidden"
              animate="visible"
              variants={{
                hidden: {},
                // Cards arrive in sequence so the eye can follow the grid filling
                // in, rather than the whole page popping at once.
                visible: { transition: { staggerChildren: 0.04 } },
              }}
            >
              {result.items.map((gig) => (
                <motion.div
                  key={gig.id}
                  variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
                  whileHover={{ y: -5 }}
                  transition={{ duration: 0.24, ease: 'easeOut' }}
                >
                  <GigCard gig={gig} />
                </motion.div>
              ))}
            </motion.div>
            <Pagination
              page={result.page}
              totalPages={result.total_pages}
              total={result.total}
              onChange={setPage}
            />
          </>
        )
      ) : null}

      <motion.button
        className="fab"
        type="button"
        onClick={() => setPosting(true)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        transition={{ type: 'spring', stiffness: 500, damping: 28 }}
        aria-label="Post a gig"
      >
        <span className="fab__plus" aria-hidden="true">
          +
        </span>
        <span className="fab__text">Post a gig</span>
      </motion.button>

      <PostGigDialog
        open={posting}
        onClose={() => setPosting(false)}
        onCreated={(gig) => {
          setPosting(false);
          setNotice(`"${gig.title}" is live. Students can apply now.`);
          resetFilters();
          setReloadKey((key) => key + 1);
        }}
      />
    </div>
  );
}

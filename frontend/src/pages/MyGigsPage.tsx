import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { EmptyState } from '../components/ui/EmptyState';
import { Pagination } from '../components/gigs/Pagination';
import { Alert } from '../components/ui/Alert';
import { Spinner } from '../components/ui/Spinner';
import { formatBudget, formatCategory, formatDate, formatPostedAgo } from '../lib/format';
import { errorMessage } from '../services/apiClient';
import { gigApi } from '../services/gigApi';
import type { GigDetail, Page } from '../types/gig';

export function MyGigsPage() {
  const [result, setResult] = useState<Page<GigDetail> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    gigApi
      .mine({ page, page_size: 12 }, controller.signal)
      .then(setResult)
      .catch((caught: unknown) => {
        if (controller.signal.aborted) return;
        setError(errorMessage(caught));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [page]);

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div>
          <h1 className="dashboard__title">
            My <em>Gigs</em>
          </h1>
          <p className="dashboard__welcome">Gigs you have posted and their current status.</p>
        </div>
      </header>

      {error ? <Alert tone="error">{error}</Alert> : null}

      {loading && !error ? (
        <div className="dashboard__loading">
          <Spinner label="Loading your gigs" />
        </div>
      ) : null}

      {!loading && result?.total === 0 ? (
        <EmptyState
          title="You haven't posted any gigs yet"
          description="Post a gig and it will appear here for you to manage."
          action={
            <Link className="btn btn--primary" to="/gigs">
              Browse gigs
            </Link>
          }
        />
      ) : null}

      {!loading && result && result.items.length > 0 ? (
        <>
        <div className="gig-grid">
          {result.items.map((gig) => (
            <article className="gig-card" key={gig.id}>
              <div className="gig-card__top">
                <span className="tag">{formatCategory(gig.category)}</span>
                <span className={`tag ${gig.state === 'OPEN' ? 'tag--state' : 'tag--closed'}`}>
                  {gig.state}
                </span>
                {gig.duration_days ? (
                  <span className="tag tag--mine">{gig.duration_days}d effort</span>
                ) : null}
              </div>

              <h2 className="gig-card__title">
                <Link to={`/gigs/${gig.id}`}>{gig.title}</Link>
              </h2>
              <p className="gig-card__description">
                {gig.description.length > 160
                  ? `${gig.description.slice(0, 157).trimEnd()}...`
                  : gig.description}
              </p>

              <dl className="gig-card__facts">
                <div>
                  <dt>Pay</dt>
                  <dd className="gig-card__budget">{formatBudget(gig.budget)}</dd>
                </div>
                <div>
                  <dt>Deadline</dt>
                  <dd>{formatDate(gig.deadline)}</dd>
                </div>
              </dl>

              <footer className="gig-card__footer">
                <span>Posted {formatPostedAgo(gig.created_at)}</span>
              </footer>

              <Link className="btn btn--primary btn--full" to={`/gigs/${gig.id}`}>
                View gig and applicants
              </Link>
            </article>
          ))}
        </div>
        <Pagination page={result.page} totalPages={result.total_pages} total={result.total} onChange={setPage} />
        </>
      ) : null}
    </div>
  );
}

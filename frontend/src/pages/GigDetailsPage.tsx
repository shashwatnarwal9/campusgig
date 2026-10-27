import { motion } from 'framer-motion';
import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { ApplicantList } from '../components/applications/ApplicantList';
import { ApplyPanel } from '../components/applications/ApplyPanel';
import { Alert } from '../components/ui/Alert';
import { EmptyState } from '../components/ui/EmptyState';
import { Spinner } from '../components/ui/Spinner';
import { useAuth } from '../hooks/useAuth';
import {
  formatBudget,
  formatCategory,
  formatDate,
  formatPostedAgo,
  formatRelativeDays,
} from '../lib/format';
import { ApiError, errorMessage } from '../services/apiClient';
import { gigApi } from '../services/gigApi';
import type { GigDetail } from '../types/gig';

type Status = 'loading' | 'ready' | 'missing' | 'error';

export function GigDetailsPage() {
  const { gigId } = useParams<{ gigId: string }>();
  const { user } = useAuth();
  const [gig, setGig] = useState<GigDetail | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    (signal?: AbortSignal) => {
      if (!gigId) {
        setStatus('missing');
        return;
      }
      setStatus('loading');
      gigApi
        .get(gigId, signal)
        .then((detail) => {
          setGig(detail);
          setStatus('ready');
        })
        .catch((caught: unknown) => {
          if (signal?.aborted) return;
          // A malformed id comes back as a 422, which for the reader means the
          // same thing as a 404: there is no such gig.
          if (caught instanceof ApiError && (caught.status === 404 || caught.status === 422)) {
            setStatus('missing');
            return;
          }
          setError(errorMessage(caught));
          setStatus('error');
        });
    },
    [gigId],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  if (status === 'loading') {
    return (
      <div className="gig-details__loading">
        <Spinner label="Loading gig" />
      </div>
    );
  }

  if (status === 'missing') {
    return (
      <div className="gig-details">
        <EmptyState
          title="Gig not found"
          description="This gig may have been closed or the link is wrong."
          action={
            <Link className="btn btn--primary" to="/gigs">
              Back to gigs
            </Link>
          }
        />
      </div>
    );
  }

  if (status === 'error' || !gig) {
    return (
      <div className="gig-details">
        <Alert tone="error">{error ?? 'Could not load this gig.'}</Alert>
        <Link className="btn btn--secondary" to="/gigs">
          Back to gigs
        </Link>
      </div>
    );
  }

  const isMine = user?.id === gig.poster.id;

  return (
    <motion.article
      className="gig-details"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: 'easeOut' }}
    >
      <Link className="gig-details__back" to="/gigs">
        &larr; Back to gigs
      </Link>

      <header className="gig-details__header">
        <div className="gig-details__tags">
          <span className="tag">{formatCategory(gig.category)}</span>
          <span className={`tag tag--${gig.state === 'OPEN' ? 'state' : 'closed'}`}>
            {gig.state}
          </span>
          {isMine ? <span className="tag tag--mine">Your gig</span> : null}
        </div>
        <h1 className="gig-details__title">{gig.title}</h1>
        <p className="gig-details__meta">
          Posted {formatPostedAgo(gig.created_at)} on {formatDate(gig.created_at)}
        </p>
      </header>

      <div className="gig-details__body">
        <div className="gig-details__left">
          <section className="gig-details__scope">
            <h2>Scope</h2>
            {gig.description.split(/\n{2,}/).map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </section>

          {isMine ? <ApplicantList gigId={gig.id} onChange={() => load()} /> : null}
        </div>

        <aside className="gig-details__aside">
          <div className="summary-card">
            <h2 className="summary-card__title">Summary</h2>
            <dl className="summary-card__list">
              <div>
                <dt>Pay</dt>
                <dd className="summary-card__budget">{formatBudget(gig.budget)}</dd>
              </div>
              <div>
                <dt>Deadline</dt>
                <dd>
                  {formatDate(gig.deadline)}
                  <span className="summary-card__note"> ({formatRelativeDays(gig.deadline)})</span>
                </dd>
              </div>
              {gig.duration_days ? (
                <div>
                  <dt>Expected effort</dt>
                  <dd>
                    {gig.duration_days} day{gig.duration_days === 1 ? '' : 's'}
                  </dd>
                </div>
              ) : null}
              <div>
                <dt>Status</dt>
                <dd>{gig.state}</dd>
              </div>
            </dl>
          </div>

          <div className="summary-card">
            <h2 className="summary-card__title">Posted by</h2>
            <dl className="summary-card__list">
              <div>
                <dt>Roll number</dt>
                <dd>{gig.poster.roll_no}</dd>
              </div>
              <div>
                <dt>Department</dt>
                <dd>{gig.poster.dept}</dd>
              </div>
              <div>
                <dt>Batch</dt>
                <dd>{gig.poster.batch}</dd>
              </div>
            </dl>
          </div>

          {isMine ? null : <ApplyPanel gig={gig} />}
        </aside>
      </div>
    </motion.article>
  );
}

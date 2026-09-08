import { motion } from 'framer-motion';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { StatCard } from '../components/applications/StatCard';
import { StatusPill } from '../components/applications/StatusPill';
import { Alert } from '../components/ui/Alert';
import { EmptyState } from '../components/ui/EmptyState';
import { Spinner } from '../components/ui/Spinner';
import { formatBudget, formatCategory, formatDate, formatPostedAgo } from '../lib/format';
import { errorMessage } from '../services/apiClient';
import { applicationApi } from '../services/applicationApi';
import {
  APPLICATION_STATUSES,
  type ApplicationStatus,
  type MyApplications,
} from '../types/application';

type Filter = ApplicationStatus | 'ALL';

const FILTERS: Filter[] = ['ALL', ...APPLICATION_STATUSES];

export function AppliedGigsPage() {
  const [data, setData] = useState<MyApplications | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>('ALL');

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      setData(await applicationApi.mine(signal));
    } catch (caught) {
      if (signal?.aborted) return;
      setError(errorMessage(caught));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const visible = useMemo(
    () =>
      (data?.items ?? []).filter((item) => filter === 'ALL' || item.status === filter),
    [data, filter],
  );

  if (loading && !data) {
    return (
      <div className="dashboard__loading">
        <Spinner label="Loading your applications" />
      </div>
    );
  }

  if (error) {
    return <Alert tone="error">{error}</Alert>;
  }

  const summary = data?.summary;

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div>
          <h1 className="dashboard__title">
            Your <em>Applications</em>
          </h1>
          <p className="dashboard__welcome">
            Everything you have applied for, and how it is going.
          </p>
        </div>
      </header>

      {summary ? (
        <motion.div
          className="stat-row"
          initial="hidden"
          animate="visible"
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.05 } } }}
        >
          <StatCard
            label="Earned"
            value={formatBudget(summary.earned)}
            tone="success"
            note="Value of completed gigs"
          />
          <StatCard
            label="In progress"
            value={formatBudget(summary.in_progress_value)}
            note={`${summary.accepted} accepted`}
          />
          <StatCard label="Applications" value={String(summary.total)} note="All time" />
          <StatCard
            label="Awaiting reply"
            value={String(summary.applied)}
            note={`${summary.completed} completed`}
          />
        </motion.div>
      ) : null}

      <p className="payments-note">
        Earnings show the budget of gigs marked complete by the poster. Payments and escrow are
        not part of this release, so no money has actually moved.
      </p>

      <div className="section-head">
        <span className="section-head__bar" aria-hidden="true" />
        <h2 className="section-head__title">Applications</h2>
      </div>

      <div className="chip-row" role="tablist" aria-label="Filter applications">
        {FILTERS.map((option) => (
          <button
            key={option}
            role="tab"
            type="button"
            aria-selected={filter === option}
            className={`chip${filter === option ? ' chip--active' : ''}`}
            onClick={() => setFilter(option)}
          >
            {option === 'ALL' ? 'All' : formatCategory(option)}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <EmptyState
          title={filter === 'ALL' ? 'No applications yet' : 'Nothing in this state'}
          description={
            filter === 'ALL'
              ? 'Browse the gigs board and apply to something that fits your timetable.'
              : 'Try another filter to see the rest of your applications.'
          }
          action={
            <Link className="btn btn--primary" to="/gigs">
              Browse gigs
            </Link>
          }
        />
      ) : (
        <motion.ul
          className="application-list"
          initial="hidden"
          animate="visible"
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.04 } } }}
        >
          {visible.map((item) => (
            <motion.li
              key={item.id}
              className="application-row"
              variants={{ hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              <div className="application-row__main">
                <div className="application-row__top">
                  <span className="tag">{formatCategory(item.gig.category)}</span>
                  <StatusPill status={item.status} />
                </div>
                <h3 className="application-row__title">
                  <Link to={`/gigs/${item.gig.id}`}>{item.gig.title}</Link>
                </h3>
                <p className="application-row__description">{item.gig.short_description}</p>
                {item.message ? (
                  <p className="application-row__message">
                    <span>Your note:</span> {item.message}
                  </p>
                ) : null}
              </div>

              <dl className="application-row__facts">
                <div>
                  <dt>Pay</dt>
                  <dd className="gig-card__budget">{formatBudget(item.gig.budget)}</dd>
                </div>
                <div>
                  <dt>Deadline</dt>
                  <dd>{formatDate(item.gig.deadline)}</dd>
                </div>
                <div>
                  <dt>Applied</dt>
                  <dd>{formatPostedAgo(item.created_at)}</dd>
                </div>
              </dl>
            </motion.li>
          ))}
        </motion.ul>
      )}
    </div>
  );
}

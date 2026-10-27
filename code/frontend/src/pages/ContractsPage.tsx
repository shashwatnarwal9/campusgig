import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { ContractStatusPill } from '../components/contracts/ContractStatusPill';
import { Pagination } from '../components/gigs/Pagination';
import { Alert } from '../components/ui/Alert';
import { EmptyState } from '../components/ui/EmptyState';
import { Spinner } from '../components/ui/Spinner';
import { useAuth } from '../hooks/useAuth';
import { formatBudget, formatPostedAgo } from '../lib/format';
import { errorMessage } from '../services/apiClient';
import { contractApi } from '../services/contractApi';
import type { ContractSummary } from '../types/application';
import type { Page } from '../types/gig';

export function ContractsPage() {
  const { user } = useAuth();
  const [result, setResult] = useState<Page<ContractSummary> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    contractApi
      .list({ page, page_size: 12 }, controller.signal)
      .then(setResult)
      .catch((caught: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(caught));
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
            Your <em>Contracts</em>
          </h1>
          <p className="dashboard__welcome">
            Agreements created when a poster awards one of your applications.
          </p>
        </div>
      </header>

      <p className="payments-note">
        Contract terms are recorded at the agreed gig amount. Escrow and payments are not part of
        this milestone, so no money has moved.
      </p>

      {error ? <Alert tone="error">{error}</Alert> : null}
      {loading ? <Spinner label="Loading your contracts" /> : null}
      {!loading && !error && result?.total === 0 ? (
        <EmptyState
          title="No contracts yet"
          description="A contract appears here when a poster accepts your application."
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
            {result.items.map((contract) => {
              const isPoster = user?.id === contract.poster.id;
              const counterpart = isPoster ? contract.worker : contract.poster;
              return (
                <article className="gig-card" key={contract.id}>
                  <div className="gig-card__top">
                    <ContractStatusPill status={contract.status} />
                    <span className="tag">{isPoster ? 'Poster' : 'Worker'}</span>
                  </div>
                  <h2 className="gig-card__title">
                    <Link to={`/contracts/${contract.id}`}>{contract.gig_title}</Link>
                  </h2>
                  <p className="gig-card__description">
                    {isPoster ? 'Worker' : 'Poster'}: {counterpart.roll_no} · {counterpart.dept}
                  </p>
                  <dl className="gig-card__facts">
                    <div>
                      <dt>Agreed amount</dt>
                      <dd className="gig-card__budget">
                        {formatBudget((contract.amount_paise / 100).toFixed(2))}
                      </dd>
                    </div>
                    <div>
                      <dt>Created</dt>
                      <dd>{formatPostedAgo(contract.created_at)}</dd>
                    </div>
                  </dl>
                  <Link className="btn btn--primary btn--full" to={`/contracts/${contract.id}`}>
                    View contract
                  </Link>
                </article>
              );
            })}
          </div>
          <Pagination
            page={result.page}
            totalPages={result.total_pages}
            total={result.total}
            onChange={setPage}
            itemLabel="contract"
            ariaLabel="Contract pages"
          />
        </>
      ) : null}
    </div>
  );
}

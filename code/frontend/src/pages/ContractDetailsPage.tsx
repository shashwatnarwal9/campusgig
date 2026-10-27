import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { ContractStatusPill } from '../components/contracts/ContractStatusPill';
import { Alert } from '../components/ui/Alert';
import { EmptyState } from '../components/ui/EmptyState';
import { Spinner } from '../components/ui/Spinner';
import { formatBudget, formatCategory, formatDate, formatPostedAgo } from '../lib/format';
import { ApiError, errorMessage } from '../services/apiClient';
import { contractApi } from '../services/contractApi';
import type { ContractDetail } from '../types/application';

type LoadState = 'loading' | 'ready' | 'missing' | 'error';

export function ContractDetailsPage() {
  const { contractId } = useParams<{ contractId: string }>();
  const [contract, setContract] = useState<ContractDetail | null>(null);
  const [state, setState] = useState<LoadState>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    if (!contractId) {
      setState('missing');
      return () => controller.abort();
    }
    setState('loading');
    setError(null);
    contractApi
      .get(contractId, controller.signal)
      .then((value) => {
        setContract(value);
        setState('ready');
      })
      .catch((caught: unknown) => {
        if (controller.signal.aborted) return;
        if (caught instanceof ApiError && (caught.status === 404 || caught.status === 422)) {
          setState('missing');
          return;
        }
        setError(errorMessage(caught));
        setState('error');
      });
    return () => controller.abort();
  }, [contractId]);

  if (state === 'loading') {
    return <div className="dashboard__loading"><Spinner label="Loading contract" /></div>;
  }
  if (state === 'missing') {
    return (
      <EmptyState
        title="Contract not found"
        description="This contract may not exist or may not belong to your account."
        action={<Link className="btn btn--primary" to="/contracts">Back to contracts</Link>}
      />
    );
  }
  if (state === 'error' || !contract) {
    return (
      <div className="dashboard">
        <Alert tone="error">{error ?? 'Could not load this contract.'}</Alert>
        <Link className="btn btn--secondary" to="/contracts">Back to contracts</Link>
      </div>
    );
  }

  return (
    <article className="gig-details">
      <Link className="gig-details__back" to="/contracts">&larr; Back to contracts</Link>
      <header className="gig-details__header">
        <div className="gig-details__tags">
          <span className="tag">{formatCategory(contract.gig_category)}</span>
          <ContractStatusPill status={contract.status} />
        </div>
        <h1 className="gig-details__title">{contract.gig_title}</h1>
        <p className="gig-details__meta">Contract created {formatDate(contract.created_at)}</p>
      </header>

      <div className="gig-details__body">
        <div className="gig-details__left">
          <section className="gig-details__scope">
            <h2>Frozen gig terms</h2>
            {contract.gig_description.split(/\n{2,}/).map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </section>
          <section className="gig-details__scope">
            <h2>Status history</h2>
            <ol className="contract-history">
              {contract.history.map((event, index) => (
                <li key={`${event.created_at}-${index}`}>
                  <div>
                    <ContractStatusPill status={event.new_status} />
                    <span className="contract-history__change">
                      {event.previous_status} → {event.new_status}
                    </span>
                  </div>
                  <p className="field__hint">
                    By {event.actor.roll_no} · {formatPostedAgo(event.created_at)}
                  </p>
                </li>
              ))}
            </ol>
          </section>
        </div>
        <aside className="gig-details__aside">
          <div className="summary-card">
            <h2 className="summary-card__title">Agreement</h2>
            <dl className="summary-card__list">
              <div>
                <dt>Agreed amount</dt>
                <dd className="summary-card__budget">
                  {formatBudget((contract.amount_paise / 100).toFixed(2))}
                </dd>
              </div>
              <div><dt>Deadline</dt><dd>{formatDate(contract.deadline)}</dd></div>
              {contract.duration_days ? (
                <div><dt>Expected effort</dt><dd>{contract.duration_days} days</dd></div>
              ) : null}
              <div><dt>Poster</dt><dd>{contract.poster.roll_no} · {contract.poster.dept}</dd></div>
              <div><dt>Worker</dt><dd>{contract.worker.roll_no} · {contract.worker.dept}</dd></div>
            </dl>
          </div>
          <p className="payments-note">
            This contract records the agreed terms. Escrow, deliverables, and settlement actions
            are not available yet; no money has moved.
          </p>
        </aside>
      </div>
    </article>
  );
}

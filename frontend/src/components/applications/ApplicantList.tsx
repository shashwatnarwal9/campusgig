import { AnimatePresence, motion } from 'framer-motion';
import { useCallback, useEffect, useState } from 'react';

import { StatusPill } from './StatusPill';
import { Alert } from '../ui/Alert';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { formatPostedAgo } from '../../lib/format';
import { errorMessage } from '../../services/apiClient';
import { applicationApi } from '../../services/applicationApi';
import type { ApplicationStatus, GigApplicant } from '../../types/application';

interface ApplicantListProps {
  gigId: string;
  /** Accepting someone closes the gig, so the parent has to refetch it. */
  onChange: () => void;
}

export function ApplicantList({ gigId, onChange }: ApplicantListProps) {
  const [applicants, setApplicants] = useState<GigApplicant[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      try {
        setApplicants(await applicationApi.forGig(gigId, signal));
      } catch (caught) {
        if (signal?.aborted) return;
        setError(errorMessage(caught));
      }
    },
    [gigId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const decide = async (applicationId: string, status: ApplicationStatus) => {
    setError(null);
    setBusy(applicationId);
    try {
      await applicationApi.setStatus(applicationId, status);
      await load();
      onChange();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(null);
    }
  };

  if (!applicants) {
    return (
      <section className="gig-details__scope">
        <h2>Applicants</h2>
        <Spinner label="Loading applicants" />
      </section>
    );
  }

  return (
    <section className="gig-details__scope">
      <h2>Applicants ({applicants.length})</h2>
      {error ? <Alert tone="error">{error}</Alert> : null}

      {applicants.length === 0 ? (
        <p className="field__hint">Nobody has applied yet.</p>
      ) : (
        <ul className="applicant-list">
          <AnimatePresence initial={false}>
            {applicants.map((applicant) => (
              <motion.li
                key={applicant.id}
                className="applicant-row"
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <div className="applicant-row__who">
                  <strong>{applicant.applicant.roll_no}</strong>
                  <span className="field__hint">
                    {applicant.applicant.dept} &middot; Batch {applicant.applicant.batch} &middot;{' '}
                    {formatPostedAgo(applicant.created_at)}
                  </span>
                  {applicant.message ? (
                    <p className="applicant-row__message">{applicant.message}</p>
                  ) : null}
                </div>

                <div className="applicant-row__actions">
                  <StatusPill status={applicant.status} />
                  {applicant.status === 'APPLIED' ? (
                    <>
                      <Button
                        variant="secondary"
                        onClick={() => decide(applicant.id, 'REJECTED')}
                        loading={busy === applicant.id}
                      >
                        Decline
                      </Button>
                      <Button
                        onClick={() => decide(applicant.id, 'ACCEPTED')}
                        loading={busy === applicant.id}
                      >
                        Accept
                      </Button>
                    </>
                  ) : null}
                  {applicant.status === 'ACCEPTED' ? (
                    <Button
                      onClick={() => decide(applicant.id, 'COMPLETED')}
                      loading={busy === applicant.id}
                    >
                      Mark complete
                    </Button>
                  ) : null}
                </div>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      )}
    </section>
  );
}

import { motion } from 'framer-motion';
import { useState } from 'react';

import { Alert } from '../ui/Alert';
import { Button } from '../ui/Button';
import { ApiError, errorMessage } from '../../services/apiClient';
import { gigApi } from '../../services/gigApi';
import type { GigDetail } from '../../types/gig';

const MAX_MESSAGE = 1000;

export function ApplyPanel({ gig }: { gig: GigDetail }) {
  const [message, setMessage] = useState('');
  const [applied, setApplied] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apply = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await gigApi.apply(gig.id, message.trim() || null);
      setApplied(true);
    } catch (caught) {
      // Applying twice is a normal thing to try after a refresh, so treat the
      // server's "already applied" as the success state rather than an error.
      if (caught instanceof ApiError && caught.code === 'already_applied') {
        setApplied(true);
        return;
      }
      setError(errorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  if (gig.state !== 'OPEN') {
    return (
      <div className="summary-card">
        <h2 className="summary-card__title">Applications</h2>
        <p className="field__hint">This gig is closed and is no longer taking applications.</p>
      </div>
    );
  }

  if (applied) {
    return (
      <motion.div
        className="summary-card"
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      >
        <Alert tone="success">
          Application sent. Track it on the Applied page — the poster decides from here.
        </Alert>
      </motion.div>
    );
  }

  return (
    <div className="summary-card">
      <h2 className="summary-card__title">Apply</h2>
      {error ? <Alert tone="error">{error}</Alert> : null}
      <div className="field">
        <label className="field__label" htmlFor="apply-message">
          Message to the poster
        </label>
        <textarea
          id="apply-message"
          className="field__input field__textarea"
          rows={4}
          maxLength={MAX_MESSAGE}
          placeholder="Why you are a good fit and when you can start. Optional."
          value={message}
          onChange={(event) => setMessage(event.target.value)}
        />
      </div>
      <Button onClick={apply} loading={submitting} fullWidth>
        Apply for this gig
      </Button>
    </div>
  );
}

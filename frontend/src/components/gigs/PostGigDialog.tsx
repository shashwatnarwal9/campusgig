import { AnimatePresence, motion } from 'framer-motion';
import { type FormEvent, useEffect, useState } from 'react';

import { Alert } from '../ui/Alert';
import { Button } from '../ui/Button';
import { SelectField } from '../ui/SelectField';
import { TextField } from '../ui/TextField';
import { formatCategory } from '../../lib/format';
import { errorMessage } from '../../services/apiClient';
import { gigApi } from '../../services/gigApi';
import { GIG_CATEGORIES, type GigCategory, type GigDetail } from '../../types/gig';

interface PostGigDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: (gig: GigDetail) => void;
}

interface FormState {
  title: string;
  description: string;
  category: GigCategory;
  budget: string;
  deadline: string;
  durationDays: string;
}

const EMPTY: FormState = {
  title: '',
  description: '',
  category: 'DEVELOPMENT',
  budget: '',
  deadline: '',
  durationDays: '',
};

const CATEGORY_OPTIONS = GIG_CATEGORIES.map((category) => ({
  value: category,
  label: formatCategory(category),
}));

function validate(form: FormState): Partial<Record<keyof FormState, string>> {
  const errors: Partial<Record<keyof FormState, string>> = {};
  if (form.title.trim().length < 5) errors.title = 'Give the gig a title of at least 5 characters.';
  if (form.title.trim().length > 200) errors.title = 'Title is too long.';
  if (form.description.trim().length < 20) {
    errors.description = 'Describe the work in at least 20 characters.';
  }
  const budget = Number(form.budget);
  if (!form.budget.trim() || Number.isNaN(budget) || budget <= 0) {
    errors.budget = 'Enter the pay as a positive amount.';
  }
  if (!form.deadline) {
    errors.deadline = 'Pick a deadline.';
  } else if (new Date(form.deadline).getTime() <= Date.now()) {
    errors.deadline = 'The deadline must be in the future.';
  }
  if (form.durationDays.trim()) {
    const days = Number(form.durationDays);
    if (!Number.isInteger(days) || days < 1 || days > 365) {
      errors.durationDays = 'Duration must be between 1 and 365 days.';
    }
  }
  return errors;
}

export function PostGigDialog({ open, onClose, onCreated }: PostGigDialogProps) {
  const [form, setForm] = useState<FormState>(EMPTY);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Escape closes, and the page behind must not scroll while the sheet is up.
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  useEffect(() => {
    if (open) {
      setForm(EMPTY);
      setFieldErrors({});
      setFormError(null);
    }
  }, [open]);

  const update = (key: keyof FormState) => (event: { target: { value: string } }) => {
    setForm((current) => ({ ...current, [key]: event.target.value }));
    setFieldErrors((current) => ({ ...current, [key]: undefined }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setFormError(null);

    const errors = validate(form);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      const gig = await gigApi.create({
        title: form.title.trim(),
        description: form.description.trim(),
        category: form.category,
        budget: Number(form.budget).toFixed(2),
        // datetime-local gives a local wall time; toISOString sends the instant.
        deadline: new Date(form.deadline).toISOString(),
        duration_days: form.durationDays.trim() ? Number(form.durationDays) : null,
      });
      onCreated(gig);
    } catch (error) {
      setFormError(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="sheet-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          onClick={onClose}
        >
          <motion.div
            className="sheet"
            role="dialog"
            aria-modal="true"
            aria-labelledby="post-gig-title"
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 380, damping: 32 }}
            onClick={(event) => event.stopPropagation()}
          >
            <header className="sheet__header">
              <h2 className="sheet__title" id="post-gig-title">
                Post a gig
              </h2>
              <button
                className="sheet__close"
                type="button"
                onClick={onClose}
                aria-label="Close"
              >
                &times;
              </button>
            </header>

            <form className="form sheet__body" onSubmit={handleSubmit} noValidate>
              {formError ? <Alert tone="error">{formError}</Alert> : null}

              <TextField
                label="Title"
                name="title"
                placeholder="Build a landing page for our club"
                value={form.title}
                onChange={update('title')}
                error={fieldErrors.title}
                autoFocus
                required
              />

              <div className="field">
                <label className="field__label" htmlFor="gig-description">
                  What needs doing
                </label>
                <textarea
                  id="gig-description"
                  className={`field__input field__textarea${
                    fieldErrors.description ? ' field__input--error' : ''
                  }`}
                  rows={5}
                  placeholder="Scope, what you will provide, and what done looks like."
                  value={form.description}
                  onChange={update('description')}
                  aria-invalid={fieldErrors.description ? true : undefined}
                  required
                />
                {fieldErrors.description ? (
                  <p className="field__error" role="alert">
                    {fieldErrors.description}
                  </p>
                ) : (
                  <p className="field__hint">At least 20 characters.</p>
                )}
              </div>

              <SelectField
                label="Category"
                value={form.category}
                onChange={update('category')}
                options={CATEGORY_OPTIONS}
              />

              <div className="form__row">
                <TextField
                  label="Pay (₹)"
                  name="budget"
                  inputMode="decimal"
                  placeholder="4500"
                  value={form.budget}
                  onChange={update('budget')}
                  error={fieldErrors.budget}
                  required
                />
                <TextField
                  label="Duration (days)"
                  name="durationDays"
                  inputMode="numeric"
                  placeholder="5"
                  value={form.durationDays}
                  onChange={update('durationDays')}
                  error={fieldErrors.durationDays}
                  hint="Optional. Effort, not the deadline."
                />
              </div>

              <TextField
                label="Deadline"
                name="deadline"
                type="datetime-local"
                value={form.deadline}
                onChange={update('deadline')}
                error={fieldErrors.deadline}
                required
              />

              <div className="sheet__actions">
                <Button type="button" variant="secondary" onClick={onClose}>
                  Cancel
                </Button>
                <Button type="submit" loading={submitting}>
                  Post gig
                </Button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

import { type FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Alert } from '../components/ui/Alert';
import { Button } from '../components/ui/Button';
import { TextField } from '../components/ui/TextField';
import { AuthLayout } from '../layouts/AuthLayout';
import {
  batchError,
  deptError,
  emailError,
  passwordError,
  rollNoError,
} from '../lib/validation';
import { errorMessage } from '../services/apiClient';
import { authApi } from '../services/authApi';

interface FormState {
  email: string;
  password: string;
  rollNo: string;
  dept: string;
  batch: string;
}

const EMPTY: FormState = { email: '', password: '', rollNo: '', dept: '', batch: '' };

export function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const update = (key: keyof FormState) => (event: { target: { value: string } }) => {
    setForm((current) => ({ ...current, [key]: event.target.value }));
    setFieldErrors((current) => ({ ...current, [key]: undefined }));
  };

  const validate = () => {
    const errors = {
      email: emailError(form.email),
      password: passwordError(form.password),
      rollNo: rollNoError(form.rollNo),
      dept: deptError(form.dept),
      batch: batchError(form.batch),
    };
    const cleaned = Object.fromEntries(
      Object.entries(errors).filter(([, message]) => message !== null),
    ) as Partial<Record<keyof FormState, string>>;
    setFieldErrors(cleaned);
    return Object.keys(cleaned).length === 0;
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setFormError(null);
    if (!validate()) return;

    setSubmitting(true);
    try {
      await authApi.register({
        email: form.email.trim().toLowerCase(),
        password: form.password,
        roll_no: form.rollNo.trim(),
        dept: form.dept.trim(),
        batch: Number(form.batch),
      });
      // Straight to login. The email travels in router state, not the URL, so it
      // does not sit in browser history or server logs.
      navigate('/login', {
        replace: true,
        state: { email: form.email.trim().toLowerCase(), justRegistered: true },
      });
    } catch (error) {
      setFormError(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Sign up with your Thapar institutional email."
      footer={
        <p>
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      }
    >
      <form className="form" onSubmit={handleSubmit} noValidate>
        {formError ? <Alert tone="error">{formError}</Alert> : null}

        <TextField
          label="Institutional email"
          type="email"
          name="email"
          autoComplete="email"
          placeholder="you@thapar.edu"
          value={form.email}
          onChange={update('email')}
          error={fieldErrors.email}
          hint="Only @thapar.edu addresses can register."
          required
        />

        <TextField
          label="Password"
          type="password"
          name="password"
          autoComplete="new-password"
          value={form.password}
          onChange={update('password')}
          error={fieldErrors.password}
          hint="At least 8 characters, with a letter and a digit."
          required
        />

        <div className="form__row">
          <TextField
            label="Roll number"
            name="rollNo"
            value={form.rollNo}
            onChange={update('rollNo')}
            error={fieldErrors.rollNo}
            required
          />
          <TextField
            label="Batch year"
            name="batch"
            inputMode="numeric"
            placeholder="2026"
            value={form.batch}
            onChange={update('batch')}
            error={fieldErrors.batch}
            required
          />
        </div>

        <TextField
          label="Department"
          name="dept"
          placeholder="Computer Science"
          value={form.dept}
          onChange={update('dept')}
          error={fieldErrors.dept}
          required
        />

        <Button type="submit" loading={submitting} fullWidth>
          Create account
        </Button>
      </form>
    </AuthLayout>
  );
}

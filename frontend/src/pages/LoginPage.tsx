import { type FormEvent, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { Alert } from '../components/ui/Alert';
import { Button } from '../components/ui/Button';
import { TextField } from '../components/ui/TextField';
import { AuthLayout } from '../layouts/AuthLayout';
import { useAuth } from '../hooks/useAuth';
import { emailError } from '../lib/validation';
import { errorMessage } from '../services/apiClient';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as
    | { email?: string; from?: string; justRegistered?: boolean }
    | null;

  const [email, setEmail] = useState(state?.email ?? '');
  const [password, setPassword] = useState('');
  const [emailFieldError, setEmailFieldError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setFormError(null);

    const emailProblem = emailError(email);
    setEmailFieldError(emailProblem);
    if (emailProblem) return;
    if (!password) {
      setFormError('Enter your password.');
      return;
    }

    setSubmitting(true);
    try {
      await login(email.trim().toLowerCase(), password);
      navigate(state?.from ?? '/gigs', { replace: true });
    } catch (error) {
      setFormError(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Log in"
      subtitle="Use your Thapar institutional account."
      footer={
        <p>
          New to CampusGig? <Link to="/signup">Create an account</Link>
        </p>
      }
    >
      <form className="form" onSubmit={handleSubmit} noValidate>
        {state?.justRegistered && !formError ? (
          <Alert tone="success">Account created. Log in to continue.</Alert>
        ) : null}

        {formError ? <Alert tone="error">{formError}</Alert> : null}

        <TextField
          label="Institutional email"
          type="email"
          name="email"
          autoComplete="email"
          placeholder="you@thapar.edu"
          value={email}
          onChange={(event) => {
            setEmail(event.target.value);
            setEmailFieldError(null);
          }}
          error={emailFieldError}
          required
        />

        <TextField
          label="Password"
          type="password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        <Button type="submit" loading={submitting} fullWidth>
          Log in
        </Button>
      </form>
    </AuthLayout>
  );
}

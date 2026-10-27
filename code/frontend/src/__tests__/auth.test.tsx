import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AuthProvider } from '../context/AuthProvider';
import { GigsPage } from '../pages/GigsPage';
import { LoginPage } from '../pages/LoginPage';
import { ProfileProvider } from '../context/ProfileProvider';
import { SignupPage } from '../pages/SignupPage';
import { ProtectedRoute } from '../routes/ProtectedRoute';

/** Stands in for the network only. The real request/response shapes are covered
 *  by the backend suite; these tests are about the UI's own behaviour. */
function mockFetch(handler: (url: string, init?: RequestInit) => Response) {
  const spy = vi.fn((input: RequestInfo | URL, init?: RequestInit) =>
    Promise.resolve(handler(String(input), init)),
  );
  vi.stubGlobal('fetch', spy);
  return spy;
}

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

const unauthenticated = () => json(401, { detail: { code: 'not_authenticated', message: 'nope' } });

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('signup form', () => {
  it('rejects a non-institutional email before calling the API', async () => {
    const fetchSpy = mockFetch(unauthenticated);
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/signup']}>
        <AuthProvider>
          <Routes>
            <Route path="/signup" element={<SignupPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/institutional email/i), 'student@gmail.com');
    await user.type(screen.getByLabelText(/password/i), 'CampusGig123');
    await user.type(screen.getByLabelText(/roll number/i), '102103999');
    await user.type(screen.getByLabelText(/batch year/i), '2026');
    await user.type(screen.getByLabelText(/department/i), 'Computer Science');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText(/ending in @thapar\.edu/i)).toBeInTheDocument();
    const registerCalls = fetchSpy.mock.calls.filter(([url]) =>
      String(url).includes('/auth/register'),
    );
    expect(registerCalls).toHaveLength(0);
  });
});

describe('login form', () => {
  it('surfaces the backend error for bad credentials', async () => {
    mockFetch((url) => {
      if (url.includes('/auth/login')) {
        return json(401, {
          detail: { code: 'invalid_credentials', message: 'Invalid email or password.' },
        });
      }
      return unauthenticated();
    });
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/institutional email/i), 'student@thapar.edu');
    await user.type(screen.getByLabelText(/password/i), 'CampusGig123');
    await user.click(screen.getByRole('button', { name: /^log in$/i }));

    expect(await screen.findByText(/invalid email or password/i)).toBeInTheDocument();
  });
});

describe('protected route', () => {
  const renderDashboardAt = () =>
    render(
      <MemoryRouter initialEntries={['/gigs']}>
        <AuthProvider>
          <ProfileProvider>
            <Routes>
              <Route path="/login" element={<p>Login screen</p>} />
              <Route element={<ProtectedRoute />}>
                <Route path="/gigs" element={<GigsPage />} />
              </Route>
            </Routes>
          </ProfileProvider>
        </AuthProvider>
      </MemoryRouter>,
    );

  it('redirects an unauthenticated visitor to /login', async () => {
    mockFetch(unauthenticated);
    renderDashboardAt();
    expect(await screen.findByText('Login screen')).toBeInTheDocument();
  });

  it('renders the dashboard for an authenticated user', async () => {
    mockFetch((url) => {
      if (url.includes('/auth/me')) {
        return json(200, {
          id: '2f6a1c2e-0000-4000-8000-000000000000',
          email: 'student@thapar.edu',
          roll_no: '102103999',
          dept: 'Computer Science',
          batch: 2026,
          role: 'STUDENT',
          created_at: new Date().toISOString(),
        });
      }
      if (url.includes('/profile')) {
        return json(200, {
          id: '2f6a1c2e-0000-4000-8000-000000000000',
          email: 'student@thapar.edu',
          roll_no: '102103999',
          dept: 'Computer Science',
          batch: 2026,
          role: 'STUDENT',
          created_at: new Date().toISOString(),
          bio: null,
          avatar_url: null,
          resume_url: null,
        });
      }
      if (url.includes('/gigs')) {
        return json(200, { items: [], page: 1, page_size: 12, total: 0, total_pages: 1 });
      }
      return unauthenticated();
    });

    renderDashboardAt();

    expect(await screen.findByRole('heading', { name: /available gigs/i })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText(/no gigs match your search/i)).toBeInTheDocument(),
    );
  });
});

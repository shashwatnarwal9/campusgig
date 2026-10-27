import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AuthProvider } from '../context/AuthProvider';
import { ContractDetailsPage } from '../pages/ContractDetailsPage';
import { ContractsPage } from '../pages/ContractsPage';

const poster = { id: 'poster-id', roll_no: '102100001', dept: 'Design', batch: 2026 };
const worker = { id: 'worker-id', roll_no: '102100002', dept: 'Computer Science', batch: 2025 };
const summary = {
  id: 'contract-id',
  gig_id: 'gig-id',
  status: 'ACCEPTED',
  gig_title: 'Build a student portfolio',
  amount_paise: 123456,
  created_at: '2026-10-20T00:00:00Z',
  poster,
  worker,
};
const detail = {
  ...summary,
  application_id: 'application-id',
  gig_description: 'Create a responsive portfolio from the approved fictional project brief.',
  gig_category: 'DEVELOPMENT',
  deadline: '2026-11-20T00:00:00Z',
  duration_days: 4,
  confirmation_deadline: null,
  revisions_used: 0,
  updated_at: '2026-10-20T00:00:00Z',
  history: [
    {
      previous_status: 'OPEN',
      new_status: 'ACCEPTED',
      actor: poster,
      created_at: '2026-10-20T00:00:00Z',
    },
  ],
};

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

function mockFetch(handler: (url: string) => Response) {
  const fetchMock = vi.fn((input: RequestInfo | URL) =>
    Promise.resolve(handler(String(input))),
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function renderContractRoutes(initialEntry = '/contracts') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AuthProvider>
        <Routes>
          <Route path="/contracts" element={<ContractsPage />} />
          <Route path="/contracts/:contractId" element={<ContractDetailsPage />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('contracts UI', () => {
  it('renders participant context, frozen terms, and award history without future actions', async () => {
    mockFetch((url) => {
      if (url.includes('/auth/me')) {
        return json(200, {
          ...poster,
          email: 'poster@thapar.edu',
          role: 'STUDENT',
          created_at: '2026-10-01T00:00:00Z',
        });
      }
      if (new URL(url).pathname === '/api/v1/contracts') {
        return json(200, { items: [summary], page: 1, page_size: 12, total: 1, total_pages: 1 });
      }
      if (new URL(url).pathname === '/api/v1/contracts/contract-id') return json(200, detail);
      return json(404, { detail: { code: 'not_found', message: 'Not found.' } });
    });

    renderContractRoutes();
    fireEvent.click(await screen.findByRole('link', { name: 'View contract' }));

    expect(await screen.findByRole('heading', { name: 'Build a student portfolio' })).toBeInTheDocument();
    expect(screen.getByText('Frozen gig terms')).toBeInTheDocument();
    expect(screen.getByText(/₹1,235/)).toBeInTheDocument();
    expect(screen.getByText(/OPEN → ACCEPTED/)).toBeInTheDocument();
    expect(screen.getByText(/no money has moved/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /confirm|deliver|revision|release/i })).toBeNull();
  });

  it('shows the empty state and list API errors', async () => {
    const fetchMock = mockFetch((url) => {
      if (url.includes('/auth/me')) {
        return json(200, {
          ...poster,
          email: 'poster@thapar.edu',
          role: 'STUDENT',
          created_at: '2026-10-01T00:00:00Z',
        });
      }
      return json(200, { items: [], page: 1, page_size: 12, total: 0, total_pages: 1 });
    });
    const { unmount } = renderContractRoutes();
    expect(await screen.findByText('No contracts yet')).toBeInTheDocument();
    unmount();

    fetchMock.mockImplementation((input: RequestInfo | URL) =>
      Promise.resolve(
        String(input).includes('/auth/me')
          ? json(200, {
              ...poster,
              email: 'poster@thapar.edu',
              role: 'STUDENT',
              created_at: '2026-10-01T00:00:00Z',
            })
          : json(500, {
              detail: { code: 'server_error', message: 'Could not load contracts.' },
            }),
      ),
    );
    renderContractRoutes();
    expect(await screen.findByText('Could not load contracts.')).toBeInTheDocument();
  });

  it('shows a contract detail error', async () => {
    mockFetch((url) =>
      url.includes('/auth/me')
        ? json(401, { detail: { code: 'not_authenticated', message: 'Sign in.' } })
        : json(500, {
            detail: { code: 'server_error', message: 'Could not load this contract.' },
          }),
    );
    renderContractRoutes('/contracts/contract-id');
    expect(await screen.findByText('Could not load this contract.')).toBeInTheDocument();
  });
});

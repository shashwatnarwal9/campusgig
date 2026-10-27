import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AppliedGigsPage } from '../pages/AppliedGigsPage';
import { MyGigsPage } from '../pages/MyGigsPage';

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

const gig = {
  id: 'gig-1',
  title: 'Design a poster',
  category: 'DESIGN',
  description: 'A sufficiently detailed description for this design gig.',
  short_description: 'A sufficiently detailed description',
  budget: '1200.00',
  deadline: '2027-01-15T00:00:00Z',
  duration_days: 2,
  state: 'OPEN',
  created_at: '2026-10-20T00:00:00Z',
  updated_at: '2026-10-20T00:00:00Z',
  poster: { id: 'poster-1', roll_no: '102103999', dept: 'Design', batch: 2026 },
};

const page = (items: unknown[], current: number, total: number, totalPages: number) => ({
  items,
  page: current,
  page_size: 1,
  total,
  total_pages: totalPages,
});

const application = {
  id: 'application-1',
  status: 'APPLIED',
  message: null,
  created_at: '2026-10-20T00:00:00Z',
  updated_at: '2026-10-20T00:00:00Z',
  gig,
};

function mockFetch(handler: (url: string) => Response) {
  const fetchMock = vi.fn((input: RequestInfo | URL) =>
    Promise.resolve(handler(String(input))),
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => vi.unstubAllGlobals());

describe('My Gigs pagination', () => {
  it('requests the next page and shows its results', async () => {
    const fetchMock = mockFetch((url) => {
      const requestedPage = new URL(url).searchParams.get('page');
      return json(
        200,
        page([{ ...gig, id: `gig-${requestedPage}`, title: `Gig page ${requestedPage}` }], Number(requestedPage), 2, 2),
      );
    });
    render(<MemoryRouter><MyGigsPage /></MemoryRouter>);

    expect(await screen.findByRole('link', { name: 'Gig page 1' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    expect(await screen.findByRole('link', { name: 'Gig page 2' })).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(fetchMock.mock.calls[1]?.[0]).toContain('page=2');
    expect(fetchMock.mock.calls[1]?.[0]).toContain('page_size=12');
  });

  it('shows the empty state and API errors', async () => {
    mockFetch(() => json(200, page([], 1, 0, 1)));
    const { unmount } = render(<MemoryRouter><MyGigsPage /></MemoryRouter>);
    expect(await screen.findByText(/haven't posted any gigs yet/i)).toBeInTheDocument();
    unmount();

    mockFetch(() => json(500, { detail: { code: 'server_error', message: 'Could not load gigs.' } }));
    render(<MemoryRouter><MyGigsPage /></MemoryRouter>);
    expect(await screen.findByText('Could not load gigs.')).toBeInTheDocument();
  });
});

describe('Applied Gigs pagination', () => {
  it('requests the next page and keeps the summary visible', async () => {
    const fetchMock = mockFetch((url) => {
      const requestedPage = Number(new URL(url).searchParams.get('page'));
      return json(200, {
        ...page([{ ...application, id: `application-${requestedPage}`, gig: { ...gig, title: `Applied gig ${requestedPage}` } }], requestedPage, 2, 2),
        summary: { total: 2, applied: 2, accepted: 0, rejected: 0, completed: 0, earned: '0', in_progress_value: '0' },
      });
    });
    render(<MemoryRouter><AppliedGigsPage /></MemoryRouter>);

    expect(await screen.findByRole('link', { name: 'Applied gig 1' })).toBeInTheDocument();
    expect(screen.getAllByText('2', { selector: '.stat-card__value' })).toHaveLength(2);
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    expect(await screen.findByRole('link', { name: 'Applied gig 2' })).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(fetchMock.mock.calls[1]?.[0]).toContain('page=2');
  });

  it('shows the empty state and API errors', async () => {
    mockFetch(() => json(200, {
      ...page([], 1, 0, 1),
      summary: { total: 0, applied: 0, accepted: 0, rejected: 0, completed: 0, earned: '0', in_progress_value: '0' },
    }));
    const { unmount } = render(<MemoryRouter><AppliedGigsPage /></MemoryRouter>);
    expect(await screen.findByText('No applications yet')).toBeInTheDocument();
    unmount();

    mockFetch(() => json(500, { detail: { code: 'server_error', message: 'Could not load applications.' } }));
    render(<MemoryRouter><AppliedGigsPage /></MemoryRouter>);
    expect(await screen.findByText('Could not load applications.')).toBeInTheDocument();
  });
});

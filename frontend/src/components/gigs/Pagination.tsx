interface PaginationProps {
  page: number;
  totalPages: number;
  total: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, totalPages, total, onChange }: PaginationProps) {
  if (total === 0) return null;

  return (
    <nav className="pagination" aria-label="Gig pages">
      <button
        className="btn btn--secondary"
        type="button"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        Previous
      </button>
      <span className="pagination__status" aria-live="polite">
        Page {page} of {totalPages} &middot; {total} gig{total === 1 ? '' : 's'}
      </span>
      <button
        className="btn btn--secondary"
        type="button"
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
      >
        Next
      </button>
    </nav>
  );
}

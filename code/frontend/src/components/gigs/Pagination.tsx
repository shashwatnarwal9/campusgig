interface PaginationProps {
  page: number;
  totalPages: number;
  total: number;
  onChange: (page: number) => void;
  itemLabel?: string;
  ariaLabel?: string;
}

export function Pagination({
  page,
  totalPages,
  total,
  onChange,
  itemLabel = 'gig',
  ariaLabel = 'Gig pages',
}: PaginationProps) {
  if (total === 0) return null;

  return (
    <nav className="pagination" aria-label={ariaLabel}>
      <button
        className="btn btn--secondary"
        type="button"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        Previous
      </button>
      <span className="pagination__status" aria-live="polite">
        Page {page} of {totalPages} &middot; {total} {itemLabel}{total === 1 ? '' : 's'}
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

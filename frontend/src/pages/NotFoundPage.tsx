import { Link } from 'react-router-dom';

import { EmptyState } from '../components/ui/EmptyState';

export function NotFoundPage() {
  return (
    <div className="route-loading">
      <EmptyState
        title="Page not found"
        description="That link does not lead anywhere on CampusGig."
        action={
          <Link className="btn btn--primary" to="/gigs">
            Go to gigs
          </Link>
        }
      />
    </div>
  );
}

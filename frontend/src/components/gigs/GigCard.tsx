import { Link } from 'react-router-dom';

import {
  formatBudget,
  formatCategory,
  formatDate,
  formatPostedAgo,
  formatRelativeDays,
} from '../../lib/format';
import type { GigSummary } from '../../types/gig';

export function GigCard({ gig }: { gig: GigSummary }) {
  return (
    <article className="gig-card">
      <div className="gig-card__top">
        <span className="tag">{formatCategory(gig.category)}</span>
        <span className="tag tag--state">{gig.state}</span>
        {gig.duration_days ? (
          <span className="tag tag--mine">
            {gig.duration_days}d effort
          </span>
        ) : null}
      </div>

      <h3 className="gig-card__title">
        <Link to={`/gigs/${gig.id}`}>{gig.title}</Link>
      </h3>

      <p className="gig-card__description">{gig.short_description}</p>

      <dl className="gig-card__facts">
        <div>
          <dt>Pay</dt>
          <dd className="gig-card__budget">{formatBudget(gig.budget)}</dd>
        </div>
        <div>
          <dt>Deadline</dt>
          <dd>
            {formatDate(gig.deadline)}
            <span className="gig-card__countdown"> &middot; {formatRelativeDays(gig.deadline)}</span>
          </dd>
        </div>
      </dl>

      <footer className="gig-card__footer">
        <span className="gig-card__poster">
          {gig.poster.roll_no} &middot; {gig.poster.dept}
        </span>
        <span className="gig-card__posted">{formatPostedAgo(gig.created_at)}</span>
      </footer>

      <Link className="btn btn--primary btn--full" to={`/gigs/${gig.id}`}>
        View details
      </Link>
    </article>
  );
}

import type { ApplicationStatus } from '../../types/application';

const LABELS: Record<ApplicationStatus, string> = {
  APPLIED: 'Awaiting reply',
  ACCEPTED: 'Accepted',
  REJECTED: 'Not selected',
  COMPLETED: 'Completed',
};

export function StatusPill({ status }: { status: ApplicationStatus }) {
  return <span className={`pill pill--${status.toLowerCase()}`}>{LABELS[status]}</span>;
}

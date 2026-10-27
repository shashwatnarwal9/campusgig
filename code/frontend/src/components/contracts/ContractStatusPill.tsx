import type { ContractStatus } from '../../types/application';

const LABELS: Record<ContractStatus, string> = {
  OPEN: 'Open',
  ACCEPTED: 'Awarded',
  DELIVERED: 'Delivered',
  REVISION: 'Revision requested',
  DISPUTED: 'Disputed',
  RELEASED: 'Released',
  REFUNDED: 'Refunded',
  SPLIT: 'Split',
};

export function ContractStatusPill({ status }: { status: ContractStatus }) {
  return (
    <span className={`pill pill--contract-${status.toLowerCase()}`}>
      {LABELS[status]}
    </span>
  );
}

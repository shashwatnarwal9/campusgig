import { SelectField } from '../ui/SelectField';
import { TextField } from '../ui/TextField';
import type { GigQuery } from '../../types/gig';

interface FilterControlsProps {
  filters: GigQuery;
  onChange: (patch: Partial<GigQuery>) => void;
  onReset: () => void;
}

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest first' },
  { value: 'deadline', label: 'Deadline soonest' },
  { value: 'budget_desc', label: 'Budget: high to low' },
  { value: 'budget_asc', label: 'Budget: low to high' },
];

export function FilterControls({ filters, onChange, onReset }: FilterControlsProps) {
  return (
    <section className="filters" aria-label="Filter gigs">
      <TextField
        label="Min budget"
        inputMode="numeric"
        placeholder="0"
        value={filters.min_budget ?? ''}
        onChange={(event) => onChange({ min_budget: event.target.value.replace(/[^\d.]/g, '') })}
      />

      <TextField
        label="Max budget"
        inputMode="numeric"
        placeholder="10000"
        value={filters.max_budget ?? ''}
        onChange={(event) => onChange({ max_budget: event.target.value.replace(/[^\d.]/g, '') })}
      />

      <TextField
        label="Deadline before"
        type="date"
        value={filters.deadline_before?.slice(0, 10) ?? ''}
        onChange={(event) =>
          onChange({
            deadline_before: event.target.value
              ? new Date(`${event.target.value}T23:59:59`).toISOString()
              : '',
          })
        }
      />

      <SelectField
        label="Sort by"
        value={filters.sort ?? 'newest'}
        onChange={(event) => onChange({ sort: event.target.value as GigQuery['sort'] })}
        options={SORT_OPTIONS}
      />

      <button className="btn btn--ghost filters__reset" type="button" onClick={onReset}>
        Clear filters
      </button>
    </section>
  );
}

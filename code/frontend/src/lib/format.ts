const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

const fullDate = new Intl.DateTimeFormat('en-IN', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});

export function formatBudget(value: string): string {
  const amount = Number(value);
  return Number.isNaN(amount) ? value : currency.format(amount);
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : fullDate.format(date);
}

export function formatRelativeDays(iso: string): string {
  const target = new Date(iso).getTime();
  if (Number.isNaN(target)) return iso;
  const days = Math.round((target - Date.now()) / 86_400_000);
  if (days < 0) return `${Math.abs(days)}d overdue`;
  if (days === 0) return 'due today';
  if (days === 1) return 'due tomorrow';
  return `${days}d left`;
}

export function formatPostedAgo(iso: string): string {
  const posted = new Date(iso).getTime();
  if (Number.isNaN(posted)) return iso;
  const hours = Math.round((Date.now() - posted) / 3_600_000);
  if (hours < 1) return 'just now';
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? 'yesterday' : `${days} days ago`;
}

export function formatCategory(category: string): string {
  return category
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

import type { ReactNode } from 'react';

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
}

/** Inline strokes rather than an icon package: four glyphs is not a dependency. */
const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.7,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

export const NAV_ITEMS: NavItem[] = [
  {
    to: '/gigs',
    label: 'Gigs',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" {...stroke}>
        <rect x="3" y="7" width="18" height="13" rx="2.5" />
        <path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7" />
        <path d="M3 12h18" />
      </svg>
    ),
  },
  {
    to: '/applied',
    label: 'Applied',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" {...stroke}>
        <path d="M6 3.5h9l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 5 20V5A1.5 1.5 0 0 1 6 3.5Z" />
        <path d="M14.5 3.5V8H19" />
        <path d="m8.5 14 2.2 2.2 4.3-4.3" />
      </svg>
    ),
  },
  {
    to: '/profile',
    label: 'Profile',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" {...stroke}>
        <circle cx="12" cy="8.5" r="3.75" />
        <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
      </svg>
    ),
  },
];

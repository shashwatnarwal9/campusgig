import { motion } from 'framer-motion';
import { type CSSProperties, useRef } from 'react';

import { formatCategory } from '../../lib/format';
import { GIG_CATEGORIES, type GigCategory } from '../../types/gig';

interface CategoryStripProps {
  active: GigCategory | '';
  onSelect: (category: GigCategory | '') => void;
}

// Dropped in by hand at frontend/public/categories/ — see that folder's
// README for the file list. Missing files just fall back to the flat
// violet-tint background under the gradient scrim.
const IMAGE: Record<GigCategory, string> = {
  ACADEMIC_HELP: '/categories/academic-help.jpg',
  DESIGN: '/categories/design.jpg',
  DEVELOPMENT: '/categories/development.jpg',
  WRITING: '/categories/writing.jpg',
  TUTORING: '/categories/tutoring.jpg',
  EVENTS: '/categories/events.jpg',
  PHOTOGRAPHY: '/categories/photography.jpg',
  OTHER: '/categories/others.jpg',
};

const CARDS: Array<{ value: GigCategory | ''; label: string; image: string }> = [
  { value: '', label: 'All gigs', image: '/categories/all.jpg' },
  ...GIG_CATEGORIES.map((category) => ({
    value: category,
    label: formatCategory(category),
    image: IMAGE[category],
  })),
];

export function CategoryStrip({ active, onSelect }: CategoryStripProps) {
  const track = useRef<HTMLDivElement>(null);

  const scroll = (direction: -1 | 1) => {
    // Roughly one card-and-a-bit per press, so nothing lands half cut off.
    track.current?.scrollBy({ left: direction * 320, behavior: 'smooth' });
  };

  return (
    <div className="strip">
      <button
        className="strip__arrow strip__arrow--prev"
        type="button"
        onClick={() => scroll(-1)}
        aria-label="Scroll categories left"
      >
        &lsaquo;
      </button>

      <motion.div
        className="strip__track"
        ref={track}
        initial="hidden"
        animate="visible"
        variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.035 } } }}
      >
        {CARDS.map((card) => (
          <motion.button
            key={card.value || 'all'}
            type="button"
            className={`category-card${active === card.value ? ' category-card--active' : ''}`}
            style={{ '--category-image': `url(${card.image})` } as CSSProperties}
            onClick={() => onSelect(card.value)}
            aria-pressed={active === card.value}
            variants={{ hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0 } }}
            whileHover={{ y: -4 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
          >
            <span className="category-card__label">{card.label}</span>
          </motion.button>
        ))}
      </motion.div>

      <button
        className="strip__arrow strip__arrow--next"
        type="button"
        onClick={() => scroll(1)}
        aria-label="Scroll categories right"
      >
        &rsaquo;
      </button>
    </div>
  );
}

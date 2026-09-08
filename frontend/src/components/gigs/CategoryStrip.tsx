import { motion } from 'framer-motion';
import { useRef } from 'react';

import { formatCategory } from '../../lib/format';
import { GIG_CATEGORIES, type GigCategory } from '../../types/gig';

interface CategoryStripProps {
  active: GigCategory | '';
  onSelect: (category: GigCategory | '') => void;
}

const EMOJI: Record<GigCategory, string> = {
  ACADEMIC_HELP: '📚',
  DESIGN: '🎨',
  DEVELOPMENT: '💻',
  WRITING: '✍️',
  TUTORING: '🧑‍🏫',
  EVENTS: '🎪',
  PHOTOGRAPHY: '📷',
  OTHER: '✨',
};

const CARDS: Array<{ value: GigCategory | ''; label: string; emoji: string }> = [
  { value: '', label: 'All gigs', emoji: '🌐' },
  ...GIG_CATEGORIES.map((category) => ({
    value: category,
    label: formatCategory(category),
    emoji: EMOJI[category],
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
            onClick={() => onSelect(card.value)}
            aria-pressed={active === card.value}
            variants={{ hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0 } }}
            whileHover={{ y: -4 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
          >
            <span className="category-card__emoji" aria-hidden="true">
              {card.emoji}
            </span>
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

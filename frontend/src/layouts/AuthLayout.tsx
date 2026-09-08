import { AnimatePresence, motion } from 'framer-motion';
import { type ReactNode, useCallback, useEffect, useState } from 'react';

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}

/**
 * What the showcase card rotates through.
 *
 * These are statements about how CampusGig works, not testimonials. Inventing
 * quotes from named students at named employers would be fabricating reviews,
 * so the slot carries real product claims instead.
 */
const SLIDES = [
  {
    text: 'Every account is tied to a @thapar.edu address, so the person on the other side of a gig is a student here — not an anonymous stranger.',
    label: 'Campus only',
    sub: 'Institutional email required',
  },
  {
    text: 'Post what you need done in about a minute: the scope, what it pays, how long it should take and when you need it by.',
    label: 'Post in a minute',
    sub: 'Pay, duration and deadline',
  },
  {
    text: 'Apply with a note, then watch it move from awaiting reply to accepted to complete. Your totals update as it goes.',
    label: 'Track every application',
    sub: 'One page, all your work',
  },
];

const AVATARS = [
  { initials: 'AM', background: 'linear-gradient(135deg,#6d3bf5,#a855f7)' },
  { initials: 'IK', background: 'linear-gradient(135deg,#d946ef,#f2836b)' },
  { initials: 'RG', background: 'linear-gradient(135deg,#f2836b,#fbb69e)' },
  { initials: '+5', background: '#16141f' },
];

export function AuthLayout({ title, subtitle, children, footer }: AuthLayoutProps) {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);

  const move = useCallback((step: number) => {
    setDirection(step);
    setIndex((current) => (current + step + SLIDES.length) % SLIDES.length);
  }, []);

  // Advances on its own, but the arrows still work; each click restarts the clock.
  useEffect(() => {
    const timer = window.setTimeout(() => move(1), 7000);
    return () => window.clearTimeout(timer);
  }, [index, move]);

  const slide = SLIDES[index];

  return (
    <div className="auth-stage">
      <motion.div
        className="auth-shell"
        initial={{ opacity: 0, y: 18, scale: 0.985 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="auth-form-side">
          <div className="brand">
            <span className="brand__mark" aria-hidden="true">
              CG
            </span>
            <span className="brand__name">CampusGig</span>
          </div>

          <div>
            <h1 className="auth-card__title">{title}</h1>
            <p className="auth-card__subtitle">{subtitle}</p>
          </div>

          {children}

          {footer ? <div className="auth-card__footer">{footer}</div> : null}
        </div>

        <aside className="showcase">
          <Starburst />

          <h2 className="showcase__heading">Campus work, campus people.</h2>

          <div className="showcase__body">
            <p className="showcase__quote-mark" aria-hidden="true">
              &ldquo;
            </p>
            {/* mode="wait" so one slide clears before the next arrives. */}
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={index}
                custom={direction}
                initial={{ opacity: 0, x: direction * 28 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: direction * -28 }}
                transition={{ duration: 0.32, ease: 'easeOut' }}
              >
                <p className="showcase__text">{slide.text}</p>
                <p className="showcase__label">{slide.label}</p>
                <p className="showcase__sub">{slide.sub}</p>
              </motion.div>
            </AnimatePresence>
          </div>

          <div className="showcase__controls">
            <button
              className="showcase__arrow"
              type="button"
              onClick={() => move(-1)}
              aria-label="Previous"
            >
              &larr;
            </button>
            <button
              className="showcase__arrow showcase__arrow--dark"
              type="button"
              onClick={() => move(1)}
              aria-label="Next"
            >
              &rarr;
            </button>
          </div>

          <motion.div
            className="showcase__float"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          >
            <h3>Find the right gig, on your own timetable</h3>
            <p>
              Browse what the campus needs help with, apply to what fits around your classes, and
              keep everything in one place.
            </p>
            <div className="avatar-stack" aria-hidden="true">
              {AVATARS.map((avatar) => (
                <span
                  key={avatar.initials}
                  className="avatar-stack__dot"
                  style={{ background: avatar.background }}
                >
                  {avatar.initials}
                </span>
              ))}
            </div>
          </motion.div>
        </aside>
      </motion.div>
    </div>
  );
}

/** The decorative burst behind the showcase card. */
function Starburst() {
  return (
    <svg className="showcase__star" viewBox="0 0 200 200" aria-hidden="true">
      <g stroke="rgba(196,181,253,0.85)" strokeWidth="1" fill="none">
        {[0, 30, 60, 90, 120, 150].map((angle) => (
          <g key={angle} transform={`rotate(${angle} 100 100)`}>
            <path d="M100 6 L104 100 L100 194 L96 100 Z" fill="rgba(167,139,250,0.35)" />
          </g>
        ))}
        <circle cx="100" cy="100" r="26" fill="rgba(129,140,248,0.35)" stroke="none" />
      </g>
    </svg>
  );
}

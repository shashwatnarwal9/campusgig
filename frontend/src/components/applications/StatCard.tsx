import { motion } from 'framer-motion';

interface StatCardProps {
  label: string;
  value: string;
  note?: string;
  tone?: 'default' | 'success';
}

export function StatCard({ label, value, note, tone = 'default' }: StatCardProps) {
  return (
    <motion.div
      className={`stat-card stat-card--${tone}`}
      variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}
      transition={{ duration: 0.24, ease: 'easeOut' }}
    >
      <p className="stat-card__label">{label}</p>
      <p className="stat-card__value">{value}</p>
      {note ? <p className="stat-card__note">{note}</p> : null}
    </motion.div>
  );
}

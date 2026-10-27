import { AnimatePresence, motion } from 'framer-motion';
import { Link, NavLink } from 'react-router-dom';

import { NAV_ITEMS } from './navItems';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onPost: () => void;
}

export function Sidebar({ collapsed, onToggle, onPost }: SidebarProps) {
  return (
    <motion.aside
      className="sidebar"
      animate={{ width: collapsed ? 78 : 264 }}
      initial={false}
      transition={{ type: 'spring', stiffness: 420, damping: 38 }}
    >
      <div className="sidebar__top">
        <Link className="brand" to="/gigs" aria-label="CampusGig home">
          <span className="brand__mark" aria-hidden="true">
            CG
          </span>
          <AnimatePresence initial={false}>
            {collapsed ? null : (
              <motion.span
                className="brand__name"
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.16 }}
              >
                CampusGig
              </motion.span>
            )}
          </AnimatePresence>
        </Link>

        {collapsed ? null : (
          <button
            className="sidebar__collapse"
            type="button"
            onClick={onToggle}
            aria-label="Collapse sidebar"
          >
            &laquo;
          </button>
        )}
      </div>

      {collapsed ? (
        <button
          className="sidebar__collapse"
          type="button"
          onClick={onToggle}
          aria-label="Expand sidebar"
          style={{ alignSelf: 'center' }}
        >
          &raquo;
        </button>
      ) : null}

      <button className="post-button" type="button" onClick={onPost}>
        <span className="post-button__plus" aria-hidden="true">
          +
        </span>
        {collapsed ? <span className="sr-only">Post a gig</span> : <span>Post a gig</span>}
      </button>

      <nav className="sidebar__nav" aria-label="Main">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) => `side-link${isActive ? ' side-link--active' : ''}`}
          >
            {({ isActive }) => (
              <>
                {isActive ? (
                  // One pill slides between items rather than each fading its own.
                  <motion.span
                    className="side-link__pill"
                    layoutId="side-pill"
                    transition={{ type: 'spring', stiffness: 480, damping: 40 }}
                  />
                ) : null}
                <span className="side-link__icon" aria-hidden="true">
                  {item.icon}
                </span>
                {collapsed ? (
                  <span className="sr-only">{item.label}</span>
                ) : (
                  <span className="side-link__label">{item.label}</span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {collapsed ? null : (
        <div className="sidebar__foot">
          <Link className="side-promo" to="/gigs">
            <strong>Need something done?</strong>
            <span>Post a gig and let the campus come to you.</span>
          </Link>
          <Link className="side-promo" to="/profile">
            <strong>Complete your profile</strong>
            <span>A picture and a resume make applications land better.</span>
          </Link>
        </div>
      )}
    </motion.aside>
  );
}

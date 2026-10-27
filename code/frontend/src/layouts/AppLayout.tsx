import { AnimatePresence, motion } from 'framer-motion';
import { type FormEvent, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { PostGigDialog } from '../components/gigs/PostGigDialog';
import { NAV_ITEMS } from '../components/layout/navItems';
import { Sidebar } from '../components/layout/Sidebar';
import { Button } from '../components/ui/Button';
import { useAuth } from '../hooks/useAuth';
import { useProfile } from '../hooks/useProfile';
import { mediaUrl } from '../services/apiClient';

export function AppLayout() {
  const { user, logout } = useAuth();
  const { profile } = useProfile();
  const navigate = useNavigate();
  const location = useLocation();

  const [collapsed, setCollapsed] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [posting, setPosting] = useState(false);
  const [term, setTerm] = useState('');

  const handleLogout = async () => {
    setLoggingOut(true);
    await logout();
    navigate('/login', { replace: true });
  };

  // Search lives in the topbar but the results live on the gigs board, so it
  // navigates there with the term in the URL rather than holding its own state.
  const search = (event: FormEvent) => {
    event.preventDefault();
    const query = term.trim();
    navigate(query ? `/gigs?q=${encodeURIComponent(query)}` : '/gigs');
  };

  const initials = (user?.roll_no ?? 'CG').slice(-2);

  return (
    <div className="app-shell">
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
        onPost={() => setPosting(true)}
      />

      <div className="app-body">
        <header className="topbar">
          <Link className="brand topbar__brand" to="/gigs">
            <span className="brand__mark" aria-hidden="true">
              CG
            </span>
          </Link>

          <form className="topbar__search" onSubmit={search} role="search">
            <div className="search-bar">
              <span className="search-bar__icon" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round">
                  <circle cx="11" cy="11" r="7" />
                  <path d="m20 20-3.2-3.2" />
                </svg>
              </span>
              <label className="sr-only" htmlFor="topbar-search">
                Search gigs
              </label>
              <input
                id="topbar-search"
                className="search-bar__input"
                type="search"
                placeholder="Search gigs by title or description..."
                value={term}
                maxLength={100}
                onChange={(event) => setTerm(event.target.value)}
              />
              <button className="search-bar__submit" type="submit">
                Search
              </button>
            </div>
          </form>

          <div className="topbar__account">
            <Link className="avatar-chip" to="/profile" title="Your profile">
              {profile?.avatar_url ? (
                <img
                  className="avatar-chip__image"
                  src={mediaUrl(profile.avatar_url)}
                  alt=""
                  width={32}
                  height={32}
                />
              ) : (
                <span className="avatar-chip__initials" aria-hidden="true">
                  {initials}
                </span>
              )}
              <span className="app-header__identity">
                <span className="app-header__roll">{user?.roll_no}</span>
                <span className="app-header__dept">{user?.dept}</span>
              </span>
            </Link>
            <Button variant="secondary" onClick={handleLogout} loading={loggingOut}>
              Log out
            </Button>
          </div>
        </header>

        <main className="app-main">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname.split('/')[1] || 'root'}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>

        <footer className="app-footer">
          <p>CampusGig &middot; Thapar Institute students only</p>
        </footer>
      </div>

      {/* Below the sidebar breakpoint the same destinations become a tab bar. */}
      <nav className="tabbar" aria-label="Main">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `tabbar__link${isActive ? ' tabbar__link--active' : ''}`}
          >
            <span aria-hidden="true">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <PostGigDialog
        open={posting}
        onClose={() => setPosting(false)}
        onCreated={() => {
          setPosting(false);
          navigate('/gigs?posted=1');
        }}
      />
    </div>
  );
}

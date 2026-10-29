import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { GraduationCap, LayoutDashboard, LogOut, Menu, Moon, Sun } from 'lucide-react';
import { useAuth } from '../auth/AuthContext.jsx';
import { navSections } from '../registry.js';
import { IconButton } from '../ui/index.js';
import { initials } from '../utils/format.js';
import { applyTheme, currentTheme } from '../utils/theme.js';

function BadgeHost({ useBadge }) {
  const count = useBadge();
  return count ? <span className="nav-badge" aria-label={`${count} pending`}>{count}</span> : null;
}

function NavItem({ route, onNavigate }) {
  const { nav } = route;
  const Icon = nav.icon;
  return (
    <NavLink to={nav.to || route.path} end={nav.end ?? true} className="nav-link" onClick={onNavigate}>
      {Icon && <Icon size={18} aria-hidden />}
      <span>{nav.label}</span>
      {nav.useBadge && <BadgeHost useBadge={nav.useBadge} />}
    </NavLink>
  );
}

export function AppShell() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState(currentTheme());
  const location = useLocation();

  useEffect(() => setOpen(false), [location.pathname]);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    setTheme(next);
  };

  const sections = navSections(user.role);

  return (
    <div className="app-shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <aside className={`sidebar ${open ? 'open' : ''}`} aria-label="Primary">
        <div className="sidebar__brand">
          <span className="brand-mark">
            <GraduationCap size={20} aria-hidden />
          </span>
          Student Records
        </div>
        <nav className="sidebar__nav">
          <NavLink to="/" end className="nav-link">
            <LayoutDashboard size={18} aria-hidden />
            <span>Dashboard</span>
          </NavLink>
          {sections.map((section) => (
            <div key={section.name}>
              <div className="nav-section">{section.name}</div>
              {section.items.map((route) => (
                <NavItem key={route.path} route={route} />
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar__footer">
          <button type="button" className="nav-link" style={{ width: '100%', border: 0, background: 'none' }} onClick={logout}>
            <LogOut size={18} aria-hidden />
            <span>Sign out</span>
          </button>
        </div>
      </aside>
      <div className={`scrim ${open ? 'open' : ''}`} onClick={() => setOpen(false)} aria-hidden />

      <div className="main">
        <header className="topbar">
          <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={() => setOpen(true)} />
          <div className="topbar__spacer" />
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'} onClick={toggleTheme} />
          <div className="user-chip">
            <span className="avatar" aria-hidden>{initials(user.full_name)}</span>
            <span className="user-chip__meta">
              <div className="user-chip__name">{user.full_name}</div>
              <div className="user-chip__role">{user.role} · {user.institutional_id}</div>
            </span>
          </div>
        </header>
        <main id="main" className="content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

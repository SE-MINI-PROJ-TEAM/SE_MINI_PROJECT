import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '../auth/AuthContext.jsx';
import { navSections } from '../registry.js';
import { Slot } from '../Slot.jsx';
import { PageHeader } from '../ui/index.js';

function greeting() {
  const hour = new Date().getHours();
  return hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
}

/** Role dashboards are assembled from the widgets each feature contributes to `<role>-dashboard`. */
export default function DashboardPage() {
  const { user } = useAuth();
  const quick = navSections(user.role).flatMap((s) => s.items).filter((r) => r.nav.quick);

  return (
    <>
      <PageHeader title={`${greeting()}, ${user.full_name.split(' ')[0]}`} subtitle={`${user.role} dashboard`} />
      {quick.length > 0 && (
        <div className="stat-grid" style={{ marginBottom: 18 }}>
          {quick.map((route) => {
            const Icon = route.nav.icon;
            return (
              <Link key={route.path} to={route.nav.to || route.path} className="card" style={{ padding: '14px 16px', textDecoration: 'none', color: 'inherit' }}>
                <div className="row row--between">
                  <span className="row">{Icon && <Icon size={18} style={{ color: 'var(--primary)' }} aria-hidden />}<strong>{route.nav.label}</strong></span>
                  <ArrowRight size={16} className="faint" aria-hidden />
                </div>
              </Link>
            );
          })}
        </div>
      )}
      <div className="dash-grid">
        <Slot name={`${user.role.toLowerCase()}-dashboard`} wrap />
      </div>
    </>
  );
}

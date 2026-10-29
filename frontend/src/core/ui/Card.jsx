export function Card({ title, icon: Icon, actions, footer, flush, children, className = '' }) {
  return (
    <section className={`card ${flush ? 'card--flush' : ''} ${className}`}>
      {(title || actions) && (
        <header className="card__header">
          <h2 className="card__title">
            {Icon && <Icon size={18} aria-hidden />}
            {title}
          </h2>
          {actions}
        </header>
      )}
      <div className="card__body">{children}</div>
      {footer && <footer className="card__footer">{footer}</footer>}
    </section>
  );
}

export function Badge({ tone = 'neutral', icon: Icon, children }) {
  return (
    <span className={`badge ${tone !== 'neutral' ? `badge--${tone}` : ''}`}>
      {Icon && <Icon size={12} aria-hidden />}
      {children}
    </span>
  );
}

export function ProgressBar({ value, tone, label }) {
  const pct = Math.max(0, Math.min(100, value ?? 0));
  return (
    <div className={`progress ${tone ? `progress--${tone}` : ''}`} role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
      <span style={{ width: `${pct}%` }} />
    </div>
  );
}

export function Stat({ label, value }) {
  return (
    <div className="stat">
      <div className="stat__value">{value}</div>
      <div className="stat__label">{label}</div>
    </div>
  );
}

const GRADE_TONES = { Draft: 'warning', Submitted: 'info', Published: 'success', 'Under Review': 'violet', Pending: 'neutral', 'Not started': 'neutral' };
export const GradeStateBadge = ({ state }) => <Badge tone={GRADE_TONES[state] || 'neutral'}>{state}</Badge>;

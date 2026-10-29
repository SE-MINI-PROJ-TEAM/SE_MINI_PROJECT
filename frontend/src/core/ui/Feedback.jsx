import { AlertCircle, AlertTriangle, CheckCircle2, Info, Inbox } from 'lucide-react';
import { Button } from './Button.jsx';

export const Spinner = ({ label = 'Loading' }) => <span className="spinner" role="status" aria-label={label} />;

export function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="state" aria-busy="true">
      <Spinner label={label} />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({ title = 'Nothing here yet', children, icon: Icon = Inbox }) {
  return (
    <div className="state">
      <Icon size={30} aria-hidden />
      <strong>{title}</strong>
      {children && <span>{children}</span>}
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="state" role="alert">
      <AlertCircle size={30} aria-hidden style={{ color: 'var(--danger)' }} />
      <strong>Something went wrong</strong>
      <span>{error?.message || 'Unexpected error.'}</span>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

const ICONS = { info: Info, warning: AlertTriangle, danger: AlertCircle, success: CheckCircle2 };

export function Alert({ tone = 'info', title, children }) {
  const Icon = ICONS[tone];
  return (
    <div className={`alert alert--${tone}`} role={tone === 'danger' ? 'alert' : 'status'}>
      <Icon size={18} aria-hidden />
      <div>
        {title && <strong>{title}</strong>}
        {title && children && <br />}
        {children}
      </div>
    </div>
  );
}

/** Render loading / error / content for a useAsync() result. */
export function AsyncBoundary({ state, children, empty }) {
  if (state.loading && !state.data) return <LoadingState />;
  if (state.error && !state.data) return <ErrorState error={state.error} onRetry={state.reload} />;
  if (empty && empty(state.data)) return null;
  return children(state.data);
}

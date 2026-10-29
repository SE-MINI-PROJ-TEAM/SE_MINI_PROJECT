import { Loader2 } from 'lucide-react';

export function Button({ variant = 'primary', size, block, loading, icon: Icon, children, className = '', disabled, type = 'button', ...rest }) {
  const classes = ['btn', `btn--${variant}`, size && `btn--${size}`, block && 'btn--block', className].filter(Boolean).join(' ');
  return (
    <button type={type} className={classes} disabled={disabled || loading} {...rest}>
      {loading ? <Loader2 size={16} className="spin-icon" style={{ animation: 'spin 0.8s linear infinite' }} aria-hidden /> : Icon ? <Icon size={16} aria-hidden /> : null}
      {children}
    </button>
  );
}

export function IconButton({ icon: Icon, label, variant = 'ghost', ...rest }) {
  return (
    <button type="button" className={`btn btn--${variant} btn--icon`} aria-label={label} title={label} {...rest}>
      <Icon size={18} aria-hidden />
    </button>
  );
}

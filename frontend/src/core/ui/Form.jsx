import { Children, cloneElement, forwardRef, isValidElement, useId } from 'react';
import { Search } from 'lucide-react';

/** Label + control + hint/error wiring (id, aria-invalid, aria-describedby). Pass exactly one control as child. */
export function Field({ label, error, hint, children, className = '' }) {
  const id = useId();
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(' ') || undefined;
  const child = Children.only(children);
  const control = isValidElement(child)
    ? cloneElement(child, { id, 'aria-invalid': error ? 'true' : undefined, 'aria-describedby': describedBy })
    : child;
  return (
    <div className={`field ${className}`}>
      {label && <label htmlFor={id}>{label}</label>}
      {control}
      {hint && !error && <span id={`${id}-hint`} className="field__hint">{hint}</span>}
      {error && <span id={`${id}-error`} className="field__error" role="alert">{error}</span>}
    </div>
  );
}

export const Input = forwardRef(function Input({ className = '', small, ...rest }, ref) {
  return <input ref={ref} className={`input ${small ? 'input--sm' : ''} ${className}`} {...rest} />;
});

export const Select = forwardRef(function Select({ className = '', children, ...rest }, ref) {
  return (
    <select ref={ref} className={`select ${className}`} {...rest}>
      {children}
    </select>
  );
});

export const Textarea = forwardRef(function Textarea({ className = '', ...rest }, ref) {
  return <textarea ref={ref} className={`textarea ${className}`} {...rest} />;
});

export function SearchInput({ value, onChange, placeholder = 'Search…', label = 'Search' }) {
  return (
    <div className="search-wrap">
      <Search size={16} aria-hidden />
      <input className="input" type="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} aria-label={label} />
    </div>
  );
}

export function Toggle({ checked, onChange, label, disabled }) {
  return (
    <span className="toggle">
      <input type="checkbox" role="switch" checked={checked} onChange={(e) => onChange(e.target.checked)} aria-label={label} disabled={disabled} />
      <span className="toggle__track" />
      <span className="toggle__thumb" />
    </span>
  );
}

/** Present / Absent switch used by roll-call and the admin override. value: true | false | null */
export function PresenceToggle({ value, onChange, disabled, name }) {
  return (
    <div className="segmented" role="group" aria-label={`Attendance for ${name}`}>
      <button type="button" className="is-present" aria-pressed={value === true} disabled={disabled} onClick={() => onChange(true)}>
        Present
      </button>
      <button type="button" className="is-absent" aria-pressed={value === false} disabled={disabled} onClick={() => onChange(false)}>
        Absent
      </button>
    </div>
  );
}

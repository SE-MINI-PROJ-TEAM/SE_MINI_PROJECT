import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Circle, LockKeyhole } from 'lucide-react';
import { useAuth } from '../../../core/auth/AuthContext.jsx';
import { Alert, Button, Card, Field, Input } from '../../../core/ui/index.js';
import { checkPassword, isStrongPassword } from '../../../core/utils/passwordPolicy.js';
import { changePassword } from '../api.js';

export default function ChangePasswordPage() {
  const { user, setUser, logout } = useAuth();
  const navigate = useNavigate();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const rules = checkPassword(next);
  const mismatch = confirm && next !== confirm ? 'Passwords do not match.' : '';
  const canSubmit = current && isStrongPassword(next) && next === confirm && next !== current;

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const { user: updated } = await changePassword(current, next);
      setUser(updated);
      navigate('/', { replace: true }); // routed to the role dashboard
    } catch (err) {
      setError(err.details?.length ? `${err.message} ${err.details.join(', ')}.` : err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bare-page">
      <div className="bare-card">
        <Card title={user?.must_change_password ? 'Set a new password' : 'Change password'} icon={LockKeyhole}>
          {user?.must_change_password && (
            <Alert tone="info">You signed in with a temporary password. Choose a new password to continue.</Alert>
          )}
          {error && <Alert tone="danger">{error}</Alert>}
          <form onSubmit={submit} noValidate>
            <Field label={user?.must_change_password ? 'Temporary password' : 'Current password'}>
              <Input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} autoComplete="current-password" autoFocus />
            </Field>
            <Field label="New password">
              <Input type="password" value={next} onChange={(e) => setNext(e.target.value)} autoComplete="new-password" />
            </Field>
            <ul className="rule-list" aria-label="Password requirements">
              {rules.map((rule) => (
                <li key={rule.id} className={rule.ok ? 'ok' : ''}>
                  {rule.ok ? <Check size={14} aria-hidden /> : <Circle size={14} aria-hidden />}
                  {rule.label}
                  <span className="sr-only">{rule.ok ? ' (met)' : ' (not met)'}</span>
                </li>
              ))}
            </ul>
            <Field label="Confirm new password" error={mismatch}>
              <Input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" />
            </Field>
            <div className="row row--between">
              <Button type="submit" loading={busy} disabled={!canSubmit}>
                Update password
              </Button>
              {user?.must_change_password ? (
                <Button variant="ghost" onClick={logout}>Sign out</Button>
              ) : (
                <Button variant="ghost" onClick={() => navigate(-1)}>Cancel</Button>
              )}
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}

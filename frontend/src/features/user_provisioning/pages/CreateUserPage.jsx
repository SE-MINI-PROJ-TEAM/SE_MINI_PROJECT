import { useState } from 'react';
import { Check, Copy, KeyRound, UserPlus } from 'lucide-react';
import { Alert, Button, Card, Field, Input, PageHeader, Select } from '../../../core/ui/index.js';
import { createUser } from '../api.js';

const EMPTY = { full_name: '', email: '', institutional_id: '', role: 'Student' };
const FIELD_FOR_CODE = { DUPLICATE_EMAIL: 'email', DUPLICATE_INSTITUTIONAL_ID: 'institutional_id', INVALID_EMAIL: 'email' };

function CredentialsScreen({ result, onAnother }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(result.temporary_password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable: the password is still visible for manual copy */
    }
  };
  const { user } = result;
  return (
    <Card title="Account created" icon={KeyRound}>
      <Alert tone="warning" title="Share these credentials now">
        The temporary password is shown only once and is stored hashed. The user must change it on first sign-in.
      </Alert>
      <dl className="stack" style={{ margin: '0 0 18px' }}>
        <div><dt className="small muted">Name</dt><dd style={{ margin: 0 }} className="cell-main">{user.full_name}</dd></div>
        <div><dt className="small muted">Institutional ID · Role</dt><dd style={{ margin: 0 }}>{user.institutional_id} · {user.role}</dd></div>
        <div><dt className="small muted">Login email</dt><dd style={{ margin: 0 }}>{user.email}</dd></div>
        <div>
          <dt className="small muted">Temporary password</dt>
          <dd style={{ margin: '6px 0 0' }}>
            <div className="cred-box">
              <span className="grow" data-testid="temp-password">{result.temporary_password}</span>
              <Button variant="secondary" size="sm" icon={copied ? Check : Copy} onClick={copy}>{copied ? 'Copied' : 'Copy'}</Button>
            </div>
          </dd>
        </div>
      </dl>
      <Button icon={UserPlus} onClick={onAnother}>Create another account</Button>
    </Card>
  );
}

export default function CreateUserPage() {
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    const next = {};
    if (!form.full_name.trim()) next.full_name = 'Full name is required.';
    if (!form.email.trim()) next.email = 'Email is required.';
    if (!form.institutional_id.trim()) next.institutional_id = 'Institutional ID is required.';
    setErrors(next);
    setFormError('');
    if (Object.keys(next).length) return;

    setBusy(true);
    try {
      setResult(await createUser(form));
    } catch (err) {
      const field = FIELD_FOR_CODE[err.code];
      if (field) setErrors({ [field]: err.message });
      else setFormError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    setForm(EMPTY);
    setErrors({});
    setResult(null);
  };

  return (
    <>
      <PageHeader title="Create user account" subtitle="Provision a student, faculty or admin account with a generated temporary password." />
      <div style={{ maxWidth: 640 }}>
        {result ? (
          <CredentialsScreen result={result} onAnother={reset} />
        ) : (
          <Card>
            <form onSubmit={submit} noValidate>
              {formError && <Alert tone="danger">{formError}</Alert>}
              <Field label="Full name" error={errors.full_name}>
                <Input value={form.full_name} onChange={set('full_name')} autoFocus />
              </Field>
              <div className="form-row">
                <Field label="Email" error={errors.email}>
                  <Input type="email" value={form.email} onChange={set('email')} />
                </Field>
                <Field label="Institutional ID" error={errors.institutional_id} hint="e.g. PES1UG26CS101">
                  <Input value={form.institutional_id} onChange={set('institutional_id')} />
                </Field>
              </div>
              <Field label="Role">
                <Select value={form.role} onChange={set('role')}>
                  <option>Student</option>
                  <option>Faculty</option>
                  <option>Admin</option>
                </Select>
              </Field>
              <Button type="submit" icon={UserPlus} loading={busy}>Create account</Button>
            </form>
          </Card>
        )}
      </div>
    </>
  );
}

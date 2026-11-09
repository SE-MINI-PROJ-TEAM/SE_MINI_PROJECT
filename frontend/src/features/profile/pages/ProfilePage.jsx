import { useEffect, useState } from 'react';
import { Lock, Save } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Badge, Button, Card, Field, Input, PageHeader, Textarea, useToast } from '../../../core/ui/index.js';
import { getProfile, updateProfile } from '../api.js';
import { validateContact } from '../validation.js';

const EDITABLE = ['phone', 'personal_email', 'home_address', 'emergency_contact'];

function ReadOnly({ label, value }) {
  return (
    <div>
      <dt className="small muted row" style={{ gap: 5 }}><Lock size={12} aria-hidden /> {label}</dt>
      <dd style={{ margin: '2px 0 0' }} className="cell-main">{value}</dd>
    </div>
  );
}

function ProfileForm({ profile }) {
  const toast = useToast();
  const [form, setForm] = useState(() => Object.fromEntries(EDITABLE.map((k) => [k, profile[k] || ''])));
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);

  useEffect(() => setForm(Object.fromEntries(EDITABLE.map((k) => [k, profile[k] || '']))), [profile]);
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    const found = validateContact(form);
    setErrors(found);
    if (Object.keys(found).length) return;
    setBusy(true);
    try {
      await updateProfile(form);
      toast.success('Profile updated.');
    } catch (err) {
      setErrors(err.details && !Array.isArray(err.details) ? err.details : {});
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Contact details">
      <form onSubmit={submit} noValidate>
        <div className="form-row">
          <Field label="Phone number" error={errors.phone}>
            <Input value={form.phone} onChange={set('phone')} inputMode="tel" autoComplete="tel" />
          </Field>
          <Field label="Personal email" error={errors.personal_email}>
            <Input type="email" value={form.personal_email} onChange={set('personal_email')} autoComplete="email" />
          </Field>
        </div>
        <Field label="Home address">
          <Textarea value={form.home_address} onChange={set('home_address')} rows={2} maxLength={255} />
        </Field>
        <Field label="Emergency contact" hint="Name and phone number of someone we can reach in an emergency.">
          <Input value={form.emergency_contact} onChange={set('emergency_contact')} maxLength={255} />
        </Field>
        <Button type="submit" icon={Save} loading={busy}>Save changes</Button>
      </form>
    </Card>
  );
}

export default function ProfilePage() {
  const state = useAsync(getProfile, []);
  return (
    <>
      <PageHeader title="My profile" subtitle="Keep your contact details up to date." actions={<Link to="/change-password" className="btn btn--secondary">Change password</Link>} />
      <AsyncBoundary state={state}>
        {({ profile }) => (
          <div className="grid" style={{ maxWidth: 760 }}>
            <Card title="Institutional record" footer="These fields are managed by an administrator and cannot be edited.">
              <dl className="form-row" style={{ margin: 0, rowGap: 14 }}>
                <ReadOnly label="Full name" value={profile.full_name} />
                <ReadOnly label="Institutional ID" value={profile.institutional_id} />
                <ReadOnly label="Institutional email" value={profile.email} />
                <ReadOnly label="Role" value={<Badge tone="primary">{profile.role}</Badge>} />
              </dl>
            </Card>
            <ProfileForm profile={profile} />
          </div>
        )}
      </AsyncBoundary>
    </>
  );
}

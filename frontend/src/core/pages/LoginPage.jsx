import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { CalendarCheck, GraduationCap, LineChart, ShieldCheck } from 'lucide-react';
import { useAuth } from '../auth/AuthContext.jsx';
import { Alert, Button, Field, Input } from '../ui/index.js';

// Convenience chips for the seeded demo accounts. Compiled out of production builds.
const DEMO = [
  ['Admin', 'admin001@srs.edu'],
  ['Faculty', 'faculty001@srs.edu'],
  ['Student', 'student001@srs.edu'],
  ['New user', 'new.student@srs.edu'],
];

export default function LoginPage() {
  const { user, login, notice } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={user.must_change_password ? '/change-password' : location.state?.from?.pathname || '/'} replace />;

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const me = await login(identifier.trim(), password);
      navigate(me.must_change_password ? '/change-password' : location.state?.from?.pathname || '/', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const fill = (email) => {
    setIdentifier(email);
    setPassword(email.startsWith('new.') ? 'Temp@12345' : 'Password@123');
  };

  return (
    <div className="login-page">
      <section className="login-hero" aria-hidden="true">
        <div className="row" style={{ fontWeight: 700, fontSize: '1.1rem' }}>
          <span className="brand-mark"><GraduationCap size={20} /></span> Student Record System
        </div>
        <div>
          <h1>Academic records, without the paperwork.</h1>
          <p>Enrollment, attendance, grading and analytics in one secure workspace for students, faculty and administrators.</p>
          <ul>
            <li><CalendarCheck size={18} /> Roll-call in three clicks, locked automatically after 48 hours</li>
            <li><LineChart size={18} /> Live GPA, attendance and grade distributions</li>
            <li><ShieldCheck size={18} /> Role-based access with audited administrative actions</li>
          </ul>
        </div>
        <span style={{ opacity: 0.7, fontSize: '0.85rem' }}>Software Engineering mini project</span>
      </section>

      <section className="login-panel">
        <form className="login-box" onSubmit={submit} noValidate>
          <h1>Welcome back</h1>
          <p className="muted" style={{ margin: '6px 0 24px' }}>Sign in with your email or institutional ID.</p>
          {notice && <Alert tone="warning">{notice}</Alert>}
          {error && <Alert tone="danger">{error}</Alert>}
          <Field label="Email or institutional ID">
            <Input value={identifier} onChange={(e) => setIdentifier(e.target.value)} autoComplete="username" autoFocus required />
          </Field>
          <Field label="Password">
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
          </Field>
          <Button type="submit" block loading={busy} disabled={!identifier || !password}>
            Sign in
          </Button>
          {import.meta.env.DEV && (
            <div style={{ marginTop: 24 }}>
              <span className="small faint">Demo accounts (development only)</span>
              <div className="demo-chips">
                {DEMO.map(([label, email]) => (
                  <button type="button" key={email} className="chip" onClick={() => fill(email)}>
                    {label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </form>
      </section>
    </div>
  );
}

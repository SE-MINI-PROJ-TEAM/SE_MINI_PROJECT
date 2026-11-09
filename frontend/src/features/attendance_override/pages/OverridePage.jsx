import { useEffect, useMemo, useState } from 'react';
import { Lock, ShieldCheck } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtDateTime } from '../../../core/utils/format.js';
import { Alert, AsyncBoundary, Badge, Button, Card, EmptyState, Field, PageHeader, PresenceToggle, Select, Textarea, useToast } from '../../../core/ui/index.js';
import { overrideCourses, overrideSession, overrideSessions, saveOverride } from '../api.js';

function Editor({ sessionId, onSaved }) {
  const toast = useToast();
  const state = useAsync(() => overrideSession(sessionId), [sessionId]);
  const [marks, setMarks] = useState({});
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (state.data) setMarks(Object.fromEntries(state.data.students.map((s) => [s.student_id, s.is_present])));
    setReason('');
    setError('');
  }, [state.data]);

  const changes = useMemo(
    () => (state.data ? state.data.students.filter((s) => marks[s.student_id] !== undefined && marks[s.student_id] !== null && marks[s.student_id] !== s.is_present) : []),
    [state.data, marks],
  );

  const submit = async () => {
    if (reason.trim().length < 5) return setError('A justification of at least 5 characters is required.');
    setError('');
    setBusy(true);
    try {
      const result = await saveOverride(sessionId, changes.map((s) => ({ student_id: s.student_id, is_present: marks[s.student_id] })), reason);
      toast.success(result.message);
      await state.reload({ silent: true });
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AsyncBoundary state={state}>
      {({ session, students }) => (
        <Card
          flush
          title={`${session.course_code}-${session.section} · ${fmtDateTime(session.start_time)}`}
          actions={session.frozen ? <Badge tone="danger" icon={Lock}>Frozen for faculty</Badge> : <Badge tone="success">Faculty can still edit</Badge>}
        >
          <div className="table-wrap" style={{ maxHeight: 420, overflowY: 'auto' }}>
            <table className="table">
              <thead><tr><th>Student</th><th>Recorded</th><th>Set to</th></tr></thead>
              <tbody>
                {students.map((s) => (
                  <tr key={s.student_id}>
                    <td><div className="cell-main">{s.full_name}</div><div className="cell-sub mono">{s.student_id}</div></td>
                    <td>{s.is_present === null ? <Badge>Unmarked</Badge> : <Badge tone={s.is_present ? 'success' : 'danger'}>{s.is_present ? 'Present' : 'Absent'}</Badge>}</td>
                    <td><PresenceToggle name={s.full_name} value={marks[s.student_id] ?? null} onChange={(v) => setMarks((m) => ({ ...m, [s.student_id]: v }))} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
            {error && <Alert tone="danger">{error}</Alert>}
            <Field label="Justification (required)" hint="Recorded in the immutable audit log together with the old and new values.">
              <Textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} maxLength={500} placeholder="e.g. Medical leave certificate verified by the department office" />
            </Field>
            <div className="row row--between">
              <span className="small muted">{changes.length} change{changes.length === 1 ? '' : 's'} pending</span>
              <Button icon={ShieldCheck} loading={busy} disabled={changes.length === 0} onClick={submit}>Apply override</Button>
            </div>
          </div>
        </Card>
      )}
    </AsyncBoundary>
  );
}

export default function OverridePage() {
  const courses = useAsync(overrideCourses, []);
  const [courseId, setCourseId] = useState('');
  const [sessionId, setSessionId] = useState('');
  const sessions = useAsync(() => (courseId ? overrideSessions(courseId) : Promise.resolve({ sessions: [] })), [courseId]);

  return (
    <>
      <PageHeader title="Attendance override" subtitle="Correct attendance records at any time, including after the 48-hour faculty freeze. Every change is audited." />
      <div className="toolbar">
        <Select aria-label="Course" value={courseId} onChange={(e) => { setCourseId(e.target.value); setSessionId(''); }} style={{ minWidth: 280 }}>
          <option value="">Select a course…</option>
          {courses.data?.courses.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
        </Select>
        <Select aria-label="Session" value={sessionId} onChange={(e) => setSessionId(e.target.value)} disabled={!courseId} style={{ minWidth: 280 }}>
          <option value="">Select a session…</option>
          {sessions.data?.sessions.map((s) => (
            <option key={s.id} value={s.id}>{fmtDateTime(s.start_time)} · {s.marked_count} marked{s.frozen ? ' · frozen' : ''}</option>
          ))}
        </Select>
      </div>
      {sessionId ? <Editor key={sessionId} sessionId={sessionId} onSaved={() => sessions.reload({ silent: true })} /> : (
        <Card><EmptyState title="Choose a course and session to review its attendance" icon={ShieldCheck} /></Card>
      )}
    </>
  );
}

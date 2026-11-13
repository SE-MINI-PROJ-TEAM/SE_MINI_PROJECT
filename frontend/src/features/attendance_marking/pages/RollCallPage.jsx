import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Check, Save } from 'lucide-react';
import { useAuth } from '../../../core/auth/AuthContext.jsx';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtDateTime, fmtRange } from '../../../core/utils/format.js';
import { Alert, AsyncBoundary, Button, Card, PageHeader, PresenceToggle, Stat, useToast } from '../../../core/ui/index.js';
import SessionStatus from '../components/SessionStatus.jsx';
import { getSession, saveAttendance } from '../api.js';

function RollCall({ data, reload }) {
  const { user } = useAuth();
  const toast = useToast();
  const { session } = data;
  const editable = session.status === 'open' && user.role === 'Faculty';

  // Unmarked students default to Present so a roll-call is "toggle the absentees, then Save".
  const initial = useMemo(() => Object.fromEntries(data.students.map((s) => [s.student_id, s.is_present ?? true])), [data]);
  const [marks, setMarks] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  useEffect(() => setMarks(initial), [initial]);

  const set = (id, value) => {
    setSaved(false);
    setMarks((m) => ({ ...m, [id]: value }));
  };
  const setAll = (value) => {
    setSaved(false);
    setMarks(Object.fromEntries(data.students.map((s) => [s.student_id, value])));
  };

  const present = Object.values(marks).filter(Boolean).length;
  const dirty = data.students.some((s) => s.is_present === null || marks[s.student_id] !== s.is_present);

  const save = async () => {
    setBusy(true);
    try {
      const result = await saveAttendance(session.id, data.students.map((s) => ({ student_id: s.student_id, is_present: marks[s.student_id] })));
      toast.success(result.message);
      setSaved(true);
      await reload({ silent: true });
    } catch (err) {
      toast.error(err.message);
      if (err.code === 'ATTENDANCE_FROZEN') reload({ silent: true });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        title={`${session.course_code}-${session.section} roll-call`}
        subtitle={`${session.course_title} · ${fmtDateTime(session.start_time)} (${fmtRange(session.start_time, session.end_time)}) · Room ${session.room}`}
        actions={<SessionStatus status={session.status} frozenAt={session.frozen_at} />}
      />
      {session.status === 'frozen' && (
        <Alert tone="warning" title="This session is frozen">
          Attendance became read-only at {fmtDateTime(session.frozen_at)}. Contact an administrator to request a correction.
        </Alert>
      )}
      {session.status === 'upcoming' && <Alert tone="info">This session has not started yet. Attendance opens when it begins.</Alert>}

      <div className="stat-grid" style={{ marginBottom: 18 }}>
        <Stat label="Enrolled" value={data.students.length} />
        <Stat label="Present" value={present} />
        <Stat label="Absent" value={data.students.length - present} />
      </div>

      <Card
        flush
        title="Roster"
        actions={editable && (
          <div className="row">
            <Button variant="secondary" size="sm" onClick={() => setAll(true)}>Mark all present</Button>
            <Button variant="secondary" size="sm" onClick={() => setAll(false)}>Mark all absent</Button>
          </div>
        )}
        footer={
          <>
            <span>{saved ? <span className="row" style={{ color: 'var(--success)' }}><Check size={16} aria-hidden /> Saved</span> : dirty && editable ? 'Unsaved changes' : ''}</span>
            {editable && <Button icon={Save} loading={busy} onClick={save} disabled={!data.students.length}>Save attendance</Button>}
          </>
        }
      >
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Institutional ID</th><th>Student</th><th>Attendance</th></tr></thead>
            <tbody>
              {data.students.map((s) => (
                <tr key={s.student_id}>
                  <td className="mono">{s.student_id}</td>
                  <td className="cell-main">{s.full_name}</td>
                  <td><PresenceToggle name={s.full_name} value={marks[s.student_id]} disabled={!editable} onChange={(v) => set(s.student_id, v)} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

export default function RollCallPage() {
  const { sessionId } = useParams();
  const state = useAsync(() => getSession(sessionId), [sessionId]);
  return (
    <>
      <Link to="/attendance" className="small row" style={{ marginBottom: 12 }}><ArrowLeft size={14} aria-hidden /> All sessions</Link>
      <AsyncBoundary state={state}>{(data) => <RollCall data={data} reload={state.reload} />}</AsyncBoundary>
    </>
  );
}

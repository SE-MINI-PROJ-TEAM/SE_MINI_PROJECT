import { useState } from 'react';
import { CalendarPlus, Trash2 } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtDateTime, fmtTime } from '../../../core/utils/format.js';
import {
  Alert, AsyncBoundary, Button, Card, ConfirmDialog, EmptyState, Field, IconButton, Input, PageHeader, Pagination, Select, useToast,
} from '../../../core/ui/index.js';
import { courseOptions, createSessions, deleteSession, listSessions } from '../api.js';

const today = () => {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10); // local date
};

function SessionForm({ courses, onCreated }) {
  const toast = useToast();
  const [form, setForm] = useState({ course_id: '', date: today(), start: '09:00', end: '10:00', room: '', repeat: 1 });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    // Date/time inputs are local wall-clock; the API stores UTC.
    const start = new Date(`${form.date}T${form.start}`);
    const end = new Date(`${form.date}T${form.end}`);
    if (!form.course_id || !form.room.trim()) return setError('Choose a course and enter a room.');
    if (!(end > start)) return setError('End time must be after the start time.');
    setBusy(true);
    try {
      const result = await createSessions({
        course_id: Number(form.course_id), room: form.room, start_time: start.toISOString(), end_time: end.toISOString(), repeat_weeks: Number(form.repeat),
      });
      toast.success(result.message);
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Schedule a session" icon={CalendarPlus}>
      <form onSubmit={submit} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}
        <Field label="Course section">
          <Select value={form.course_id} onChange={set('course_id')}>
            <option value="">Select a course…</option>
            {courses.map((c) => <option key={c.id} value={c.id}>{c.label}{c.faculty_name ? ` — ${c.faculty_name}` : ''}</option>)}
          </Select>
        </Field>
        <div className="form-row">
          <Field label="Date"><Input type="date" value={form.date} onChange={set('date')} /></Field>
          <Field label="Room"><Input value={form.room} onChange={set('room')} placeholder="e.g. LH-204" /></Field>
        </div>
        <div className="form-row">
          <Field label="Start time"><Input type="time" value={form.start} onChange={set('start')} /></Field>
          <Field label="End time"><Input type="time" value={form.end} onChange={set('end')} /></Field>
        </div>
        <Field label="Repeat weekly for" hint="Creates one session per week at the same time and room.">
          <Select value={form.repeat} onChange={set('repeat')}>
            {[1, 2, 4, 8, 12, 16].map((n) => <option key={n} value={n}>{n === 1 ? 'Just this once' : `${n} weeks`}</option>)}
          </Select>
        </Field>
        <Button type="submit" icon={CalendarPlus} loading={busy}>Publish session</Button>
      </form>
    </Card>
  );
}

export default function ManageSchedulePage() {
  const toast = useToast();
  const options = useAsync(courseOptions, []);
  const [courseFilter, setCourseFilter] = useState('');
  const [page, setPage] = useState(1);
  const [removing, setRemoving] = useState(null);
  const sessions = useAsync(() => listSessions({ course_id: courseFilter, page, per_page: 12 }), [courseFilter, page]);

  const remove = async () => {
    try {
      await deleteSession(removing.id);
      toast.success('Session removed.');
      sessions.reload({ silent: true });
    } catch (err) {
      toast.error(err.message);
    } finally {
      setRemoving(null);
    }
  };

  return (
    <>
      <PageHeader title="Manage schedule" subtitle="Assign date, time slot and room for course sessions. They appear on student and faculty calendars immediately." />
      <div className="dash-grid">
        <AsyncBoundary state={options}>{({ courses }) => <SessionForm courses={courses} onCreated={() => sessions.reload({ silent: true })} />}</AsyncBoundary>
        <Card title="Scheduled sessions" flush actions={
          <Select aria-label="Filter sessions by course" value={courseFilter} onChange={(e) => { setCourseFilter(e.target.value); setPage(1); }} style={{ width: 'auto' }}>
            <option value="">All courses</option>
            {options.data?.courses.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
          </Select>
        }>
          <AsyncBoundary state={sessions}>
            {(data) =>
              data.sessions.length === 0 ? (
                <EmptyState title="No sessions yet" />
              ) : (
                <>
                  <div className="table-wrap">
                    <table className="table">
                      <thead><tr><th>Course</th><th>When</th><th>Room</th><th><span className="sr-only">Remove</span></th></tr></thead>
                      <tbody>
                        {data.sessions.map((s) => (
                          <tr key={s.id}>
                            <td><div className="cell-main">{s.course_code}-{s.section}</div><div className="cell-sub">{s.faculty_name}</div></td>
                            <td>{fmtDateTime(s.start_time)} <span className="faint">– {fmtTime(s.end_time)}</span></td>
                            <td>{s.room}</td>
                            <td><IconButton icon={Trash2} label={`Remove ${s.course_code} session`} onClick={() => setRemoving(s)} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
                </>
              )
            }
          </AsyncBoundary>
        </Card>
      </div>
      {removing && (
        <ConfirmDialog danger title="Remove session?" confirmLabel="Remove" message={`Remove ${removing.course_code} on ${fmtDateTime(removing.start_time)}? Sessions with recorded attendance cannot be removed.`} onCancel={() => setRemoving(null)} onConfirm={remove} />
      )}
    </>
  );
}

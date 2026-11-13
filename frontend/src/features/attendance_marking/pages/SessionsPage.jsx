import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtDate, fmtRange } from '../../../core/utils/format.js';
import { AsyncBoundary, Card, EmptyState, PageHeader, Tabs } from '../../../core/ui/index.js';
import SessionStatus from '../components/SessionStatus.jsx';
import { listSessions } from '../api.js';

const TABS = [
  { id: 'open', label: 'Open' },
  { id: 'upcoming', label: 'Upcoming' },
  { id: 'frozen', label: 'Frozen (read-only)' },
];

export default function SessionsPage() {
  const [tab, setTab] = useState('open');
  const state = useAsync(listSessions, []);

  return (
    <>
      <PageHeader title="Attendance sessions" subtitle="Mark Present / Absent for your sections. Records lock automatically 48 hours after a session starts." />
      <Tabs tabs={TABS} active={tab} onChange={setTab} label="Session status" />
      <Card flush>
        <AsyncBoundary state={state}>
          {({ sessions }) => {
            const rows = sessions.filter((s) => s.status === tab).sort((a, b) => (tab === 'upcoming' ? a.start_time.localeCompare(b.start_time) : b.start_time.localeCompare(a.start_time)));
            return rows.length === 0 ? (
              <EmptyState title={`No ${tab} sessions`} />
            ) : (
              <div className="table-wrap">
                <table className="table">
                  <thead><tr><th>Course</th><th>When</th><th>Room</th><th>Marked</th><th>Status</th><th><span className="sr-only">Action</span></th></tr></thead>
                  <tbody>
                    {rows.map((s) => (
                      <tr key={s.id}>
                        <td><div className="cell-main">{s.course_code}-{s.section}</div><div className="cell-sub">{s.course_title}</div></td>
                        <td>{fmtDate(s.start_time)}<div className="cell-sub">{fmtRange(s.start_time, s.end_time)}</div></td>
                        <td>{s.room}</td>
                        <td className="num">{s.marked_count} / {s.enrolled_count}</td>
                        <td><SessionStatus status={s.status} frozenAt={s.frozen_at} /></td>
                        <td>
                          {s.status !== 'upcoming' && (
                            <Link to={`/attendance/${s.id}`} className={`btn btn--sm ${s.status === 'open' ? 'btn--primary' : 'btn--secondary'}`}>
                              {s.status === 'open' ? (s.marked_count ? 'Edit' : 'Take attendance') : 'View'}
                            </Link>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }}
        </AsyncBoundary>
      </Card>
    </>
  );
}

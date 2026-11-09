import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtDateTime, fmtPercent } from '../../../core/utils/format.js';
import { Alert, AsyncBoundary, Badge, Card, EmptyState, PageHeader, Stat } from '../../../core/ui/index.js';
import { getCourseDetail } from '../api.js';

const TONES = { Present: 'success', Absent: 'danger', 'Not marked': 'neutral' };

export default function CourseAttendancePage() {
  const { courseId } = useParams();
  const state = useAsync(() => getCourseDetail(courseId), [courseId]);
  return (
    <>
      <Link to="/my-attendance" className="small row" style={{ marginBottom: 12 }}><ArrowLeft size={14} aria-hidden /> All courses</Link>
      <AsyncBoundary state={state}>
        {(d) => (
          <>
            <PageHeader title={`${d.course.code} · ${d.course.title}`} subtitle="Session-by-session attendance" />
            {d.below_threshold && <Alert tone="danger" title={`Attendance is below ${d.threshold}%`}>Attend upcoming sessions to get back above the requirement.</Alert>}
            <div className="stat-grid" style={{ marginBottom: 18 }}>
              <Stat label="Attendance" value={fmtPercent(d.percentage)} />
              <Stat label="Sessions held" value={d.sessions_held} />
              <Stat label="Attended" value={d.sessions_attended} />
              <Stat label="Missed" value={d.sessions_missed} />
            </div>
            <Card flush title="Sessions">
              {d.sessions.length === 0 ? <EmptyState title="No sessions held yet" /> : (
                <div className="table-wrap">
                  <table className="table">
                    <thead><tr><th>Date</th><th>Room</th><th>Status</th></tr></thead>
                    <tbody>{d.sessions.map((s) => <tr key={s.session_id}><td>{fmtDateTime(s.start_time)}</td><td>{s.room}</td><td><Badge tone={TONES[s.status]}>{s.status}</Badge></td></tr>)}</tbody>
                  </table>
                </div>
              )}
            </Card>
          </>
        )}
      </AsyncBoundary>
    </>
  );
}

import { Alert, AsyncBoundary, Card, EmptyState, PageHeader, Stat } from '../../../core/ui/index.js';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtPercent } from '../../../core/utils/format.js';
import AttendanceRow from '../components/AttendanceRow.jsx';
import { getSummary } from '../api.js';

export default function AttendancePage() {
  const state = useAsync(getSummary, []);
  return (
    <>
      <PageHeader title="My attendance" subtitle="Percentages are based on sessions your faculty has already marked." />
      <AsyncBoundary state={state}>
        {(data) => {
          const low = data.courses.filter((c) => c.below_threshold);
          return (
            <>
              {low.length > 0 && (
                <Alert tone="danger" title={`Attendance below ${data.threshold}% in ${low.length} course${low.length > 1 ? 's' : ''}`}>
                  {low.map((c) => c.code).join(', ')} — you may be at risk of not meeting attendance requirements.
                </Alert>
              )}
              <div className="stat-grid" style={{ marginBottom: 18 }}>
                <Stat label="Overall attendance" value={fmtPercent(data.overall_percentage)} />
                <Stat label="Courses" value={data.courses.length} />
                <Stat label="Courses at risk" value={low.length} />
              </div>
              <Card title="By course">
                {data.courses.length === 0 ? <EmptyState title="You are not enrolled in any course" /> : <ul className="list">{data.courses.map((c) => <AttendanceRow key={c.course_id} course={c} threshold={data.threshold} />)}</ul>}
              </Card>
            </>
          );
        }}
      </AsyncBoundary>
    </>
  );
}

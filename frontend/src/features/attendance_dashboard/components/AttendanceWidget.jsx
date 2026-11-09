import { Link } from 'react-router-dom';
import { PieChart } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtPercent } from '../../../core/utils/format.js';
import { AsyncBoundary, Card, EmptyState } from '../../../core/ui/index.js';
import { getSummary } from '../api.js';
import AttendanceRow from './AttendanceRow.jsx';

export default function AttendanceWidget() {
  const state = useAsync(getSummary, []);
  return (
    <Card title="Attendance" icon={PieChart} actions={<Link to="/my-attendance" className="btn btn--secondary btn--sm">Details</Link>}>
      <AsyncBoundary state={state}>
        {(data) =>
          data.courses.length === 0 ? (
            <EmptyState title="No enrolled courses" />
          ) : (
            <>
              <p className="small muted" style={{ marginBottom: 12 }}>Overall: <strong>{fmtPercent(data.overall_percentage)}</strong></p>
              <ul className="list">{data.courses.map((c) => <AttendanceRow key={c.course_id} course={c} threshold={data.threshold} />)}</ul>
            </>
          )
        }
      </AsyncBoundary>
    </Card>
  );
}

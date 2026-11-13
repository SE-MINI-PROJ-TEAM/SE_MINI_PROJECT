import { Link } from 'react-router-dom';
import { BarChart3 } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtNumber, fmtPercent } from '../../../core/utils/format.js';
import { AsyncBoundary, Card, EmptyState } from '../../../core/ui/index.js';
import { facultySections } from '../api.js';

export default function SectionSummaryWidget() {
  const state = useAsync(facultySections, []);
  return (
    <Card title="Section overview" icon={BarChart3} actions={<Link to="/analytics" className="btn btn--secondary btn--sm">Distributions</Link>}>
      <AsyncBoundary state={state}>
        {({ sections }) =>
          sections.length === 0 ? (
            <EmptyState title="No sections assigned" />
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>Section</th><th className="num">Enrolled</th><th className="num">Graded</th><th className="num">Mean</th><th className="num">Attendance</th></tr></thead>
                <tbody>
                  {sections.map((s) => (
                    <tr key={s.course_id}>
                      <td><span className="cell-main">{s.code}-{s.section}</span> <span className="cell-sub">{s.title}</span></td>
                      <td className="num">{s.enrolled}</td><td className="num">{s.graded}</td>
                      <td className="num">{fmtNumber(s.mean, 1)}</td><td className="num">{fmtPercent(s.attendance_rate)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
      </AsyncBoundary>
    </Card>
  );
}

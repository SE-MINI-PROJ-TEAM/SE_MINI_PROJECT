import { Link } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { Badge, ProgressBar } from '../../../core/ui/index.js';
import { fmtPercent } from '../../../core/utils/format.js';

/** One course's attendance percentage with a visual alert below the compliance threshold. */
export default function AttendanceRow({ course, threshold = 75 }) {
  const pct = course.percentage;
  return (
    <li className="list__item" style={{ alignItems: 'stretch', flexDirection: 'column', gap: 6 }}>
      <div className="row row--between">
        <Link to={`/my-attendance/${course.course_id}`} className="cell-main">{course.code} · {course.title}</Link>
        <span className="row">
          {course.below_threshold && <Badge tone="danger" icon={AlertTriangle}>Below {threshold}%</Badge>}
          <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{fmtPercent(pct)}</strong>
        </span>
      </div>
      <ProgressBar value={pct ?? 0} tone={pct === null ? undefined : course.below_threshold ? 'danger' : 'success'} label={`${course.code} attendance`} />
      <div className="small muted">{course.sessions_attended} attended · {course.sessions_missed} missed · {course.sessions_held} held</div>
    </li>
  );
}

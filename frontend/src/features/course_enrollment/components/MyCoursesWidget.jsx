import { Link } from 'react-router-dom';
import { BookOpen, Plus } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Badge, Card, EmptyState } from '../../../core/ui/index.js';
import { myEnrollments } from '../api.js';

export default function MyCoursesWidget() {
  const state = useAsync(myEnrollments, []);
  return (
    <Card
      title="My courses"
      icon={BookOpen}
      actions={<Link to="/catalog" className="btn btn--secondary btn--sm"><Plus size={14} aria-hidden /> Browse catalog</Link>}
    >
      <AsyncBoundary state={state}>
        {({ enrollments }) =>
          enrollments.length === 0 ? (
            <EmptyState title="You are not enrolled in any course yet">Open the catalog to pick your sections.</EmptyState>
          ) : (
            <div className="grid grid--auto" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: 12 }}>
              {enrollments.map((e) => (
                <div key={e.enrollment_id} className="stat">
                  <div className="course-card__code">{e.code}-{e.section}</div>
                  <div className="cell-main">{e.title}</div>
                  <div className="row small muted" style={{ marginTop: 6 }}>
                    <Badge>{e.credits} credits</Badge> {e.faculty_name}
                  </div>
                </div>
              ))}
            </div>
          )
        }
      </AsyncBoundary>
    </Card>
  );
}

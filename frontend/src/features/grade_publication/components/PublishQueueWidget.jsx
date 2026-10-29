import { Link } from 'react-router-dom';
import { BadgeCheck } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Card, EmptyState } from '../../../core/ui/index.js';
import { publicationQueue } from '../api.js';

export default function PublishQueueWidget() {
  const state = useAsync(publicationQueue, []);
  return (
    <Card title="Awaiting publication" icon={BadgeCheck} actions={<Link to="/admin/publish" className="btn btn--primary btn--sm">Review &amp; publish</Link>}>
      <AsyncBoundary state={state}>
        {({ courses }) =>
          courses.length === 0 ? (
            <EmptyState title="Nothing waiting">Faculty-submitted grades will appear here.</EmptyState>
          ) : (
            <>
              <p className="small muted" style={{ marginBottom: 10 }}>{courses.length} course{courses.length > 1 ? 's' : ''} · {courses.reduce((n, c) => n + c.submitted_count, 0)} grades submitted</p>
              <ul className="list">
                {courses.slice(0, 4).map((c) => (
                  <li key={c.course_id} className="list__item"><span className="grow cell-main">{c.code}-{c.section} · {c.title}</span><span className="muted small">{c.submitted_count} grades</span></li>
                ))}
              </ul>
            </>
          )
        }
      </AsyncBoundary>
    </Card>
  );
}

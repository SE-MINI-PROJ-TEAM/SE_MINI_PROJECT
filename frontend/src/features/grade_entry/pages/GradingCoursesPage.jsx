import { Link } from 'react-router-dom';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Card, EmptyState, GradeStateBadge, PageHeader } from '../../../core/ui/index.js';
import { gradingCourses } from '../api.js';

export default function GradingCoursesPage() {
  const state = useAsync(gradingCourses, []);
  return (
    <>
      <PageHeader title="Grade entry" subtitle="Enter rubric scores progressively in Draft, then submit for administrative publication." />
      <AsyncBoundary state={state}>
        {({ courses }) =>
          courses.length === 0 ? (
            <Card><EmptyState title="No sections are assigned to you" /></Card>
          ) : (
            <div className="grid grid--auto">
              {courses.map((c) => (
                <article key={c.id} className="card course-card">
                  <div className="course-card__code">{c.code}-{c.section} · {c.term}</div>
                  <h3>{c.title}</h3>
                  <div className="row" style={{ gap: 6 }}>
                    {Object.entries(c.states).map(([state, n]) => (
                      <span key={state} className="row" style={{ gap: 4 }}><GradeStateBadge state={state} /><span className="small muted">{n}</span></span>
                    ))}
                  </div>
                  <Link to={`/grading/${c.id}`} className="btn btn--primary btn--sm">Open grade sheet</Link>
                </article>
              ))}
            </div>
          )
        }
      </AsyncBoundary>
    </>
  );
}

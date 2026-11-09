import { useState } from 'react';
import { Users } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Badge, Card, EmptyState, Modal, PageHeader } from '../../../core/ui/index.js';
import { getRoster, myCourses } from '../api.js';

function RosterModal({ course, onClose }) {
  const state = useAsync(() => getRoster(course.id), [course.id]);
  return (
    <Modal wide title={`${course.code}-${course.section} roster`} onClose={onClose}>
      <AsyncBoundary state={state}>
        {({ students }) =>
          students.length === 0 ? (
            <EmptyState title="No students enrolled yet" />
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>Institutional ID</th><th>Name</th><th>Email</th></tr></thead>
                <tbody>{students.map((s) => <tr key={s.id}><td className="mono">{s.institutional_id}</td><td className="cell-main">{s.full_name}</td><td className="cell-sub">{s.email}</td></tr>)}</tbody>
              </table>
            </div>
          )
        }
      </AsyncBoundary>
    </Modal>
  );
}

export default function SectionsPage() {
  const state = useAsync(myCourses, []);
  const [open, setOpen] = useState(null);
  return (
    <>
      <PageHeader title="My sections" subtitle="Only the sections assigned to you are visible. Rosters are never shown for other faculty's courses." />
      <AsyncBoundary state={state}>
        {({ courses }) =>
          courses.length === 0 ? (
            <Card><EmptyState title="No sections are assigned to you">An administrator assigns sections in Course offerings.</EmptyState></Card>
          ) : (
            <div className="grid grid--auto">
              {courses.map((c) => (
                <article key={c.id} className="card course-card">
                  <div className="row row--between"><span className="course-card__code">{c.code}-{c.section}</span><Badge>{c.term}</Badge></div>
                  <h3>{c.title}</h3>
                  <div className="small muted">{c.enrolled} of {c.capacity} seats filled · {c.credits} credits</div>
                  <button type="button" className="btn btn--secondary btn--sm" onClick={() => setOpen(c)}><Users size={15} aria-hidden /> View roster</button>
                </article>
              ))}
            </div>
          )
        }
      </AsyncBoundary>
      {open && <RosterModal course={open} onClose={() => setOpen(null)} />}
    </>
  );
}

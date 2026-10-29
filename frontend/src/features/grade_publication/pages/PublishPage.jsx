import { useState } from 'react';
import { BadgeCheck } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Button, Card, ConfirmDialog, EmptyState, PageHeader, useToast } from '../../../core/ui/index.js';
import { publicationQueue, publish } from '../api.js';

export default function PublishPage() {
  const toast = useToast();
  const state = useAsync(publicationQueue, []);
  const [selected, setSelected] = useState(new Set());
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  const toggle = (id) => setSelected((s) => { const next = new Set(s); next.has(id) ? next.delete(id) : next.add(id); return next; });

  const run = async () => {
    setBusy(true);
    try {
      const result = await publish([...selected]);
      toast.success(result.message);
      setSelected(new Set());
      await state.reload({ silent: true });
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Publish grades"
        subtitle="Batch-publish submitted grades. Students see them on their dashboards immediately."
        actions={<Button icon={BadgeCheck} disabled={selected.size === 0} onClick={() => setConfirming(true)}>Publish selected ({selected.size})</Button>}
      />
      <Card flush>
        <AsyncBoundary state={state}>
          {({ courses }) =>
            courses.length === 0 ? (
              <EmptyState title="No courses are waiting for publication" icon={BadgeCheck}>Grades appear here once faculty submit them.</EmptyState>
            ) : (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th style={{ width: 44 }}>
                        <input type="checkbox" aria-label="Select all courses" checked={selected.size === courses.length} onChange={(e) => setSelected(e.target.checked ? new Set(courses.map((c) => c.course_id)) : new Set())} />
                      </th>
                      <th>Course</th><th>Faculty</th><th className="num">Submitted grades</th>
                    </tr>
                  </thead>
                  <tbody>
                    {courses.map((c) => (
                      <tr key={c.course_id}>
                        <td><input type="checkbox" aria-label={`Select ${c.code}`} checked={selected.has(c.course_id)} onChange={() => toggle(c.course_id)} /></td>
                        <td><div className="cell-main">{c.code}-{c.section}</div><div className="cell-sub">{c.title} · {c.term}</div></td>
                        <td>{c.faculty_name}</td>
                        <td className="num">{c.submitted_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          }
        </AsyncBoundary>
      </Card>
      {confirming && (
        <ConfirmDialog
          title="Publish selected grades?"
          message={`Grades for ${selected.size} course(s) will become visible to students immediately and an audit entry will be recorded.`}
          confirmLabel="Publish"
          loading={busy}
          onCancel={() => setConfirming(false)}
          onConfirm={run}
        />
      )}
    </>
  );
}

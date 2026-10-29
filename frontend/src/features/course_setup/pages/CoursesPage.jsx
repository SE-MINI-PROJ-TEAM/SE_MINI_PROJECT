import { useState } from 'react';
import { Pencil, Plus } from 'lucide-react';
import { useAsync, useDebounced } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Badge, Button, Card, EmptyState, IconButton, PageHeader, Pagination, ProgressBar, SearchInput } from '../../../core/ui/index.js';
import CourseForm from '../components/CourseForm.jsx';
import { listCourses } from '../api.js';

export default function CoursesPage() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState(null); // course object | 'new' | null
  const debounced = useDebounced(search);
  const state = useAsync(() => listCourses({ search: debounced, page, per_page: 15 }), [debounced, page]);

  return (
    <>
      <PageHeader
        title="Course offerings"
        subtitle="Register sections, set seat capacity, assign faculty and define rubric weights."
        actions={<Button icon={Plus} onClick={() => setEditing('new')}>New course</Button>}
      />
      <div className="toolbar">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search by code or title" label="Search courses" />
      </div>
      <Card flush>
        <AsyncBoundary state={state}>
          {(data) =>
            data.courses.length === 0 ? (
              <EmptyState title="No courses found" />
            ) : (
              <>
                <div className="table-wrap">
                  <table className="table">
                    <thead><tr><th>Course</th><th>Term</th><th>Faculty</th><th>Seats</th><th>Rubric (normalized)</th><th><span className="sr-only">Actions</span></th></tr></thead>
                    <tbody>
                      {data.courses.map((c) => {
                        const fill = (c.enrolled / c.capacity) * 100;
                        return (
                          <tr key={c.id}>
                            <td><div className="cell-main">{c.code}-{c.section}</div><div className="cell-sub">{c.title} · {c.credits} cr</div></td>
                            <td>{c.term}</td>
                            <td>{c.faculty_name || <span className="faint">Unassigned</span>}</td>
                            <td style={{ minWidth: 130 }}>
                              <div className="small">{c.enrolled} / {c.capacity}</div>
                              <ProgressBar value={fill} tone={fill >= 100 ? 'danger' : fill >= 85 ? 'warning' : undefined} label={`${c.code} seats filled`} />
                            </td>
                            <td>
                              <div className="row" style={{ gap: 6 }}>
                                {c.rubric.map((r) => <Badge key={r.id} tone="primary">{r.name} {r.weight}%</Badge>)}
                              </div>
                            </td>
                            <td><IconButton icon={Pencil} label={`Edit ${c.code}`} onClick={() => setEditing(c)} /></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
              </>
            )
          }
        </AsyncBoundary>
      </Card>
      {editing && (
        <CourseForm
          course={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); state.reload({ silent: true }); }}
        />
      )}
    </>
  );
}

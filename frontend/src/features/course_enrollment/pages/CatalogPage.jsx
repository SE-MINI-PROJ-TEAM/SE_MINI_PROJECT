import { useState } from 'react';
import { CheckCircle2, Lock, UserRound } from 'lucide-react';
import { useAuth } from '../../../core/auth/AuthContext.jsx';
import { useAsync, useDebounced } from '../../../core/hooks/useAsync.js';
import { Alert, AsyncBoundary, Badge, Button, Card, EmptyState, PageHeader, ProgressBar, SearchInput, Toggle, useToast } from '../../../core/ui/index.js';
import { enroll, getCatalog, setWindow } from '../api.js';

function CourseCard({ course, canEnroll, blockedReason, onEnroll, busy }) {
  const full = course.seats_available === 0;
  const fill = (course.enrolled / course.capacity) * 100;
  return (
    <article className="card course-card" aria-label={`${course.code} ${course.title}`}>
      <div className="row row--between">
        <span className="course-card__code">{course.code}-{course.section}</span>
        <Badge>{course.credits} credits</Badge>
      </div>
      <div>
        <h3>{course.title}</h3>
        <div className="small muted row" style={{ gap: 5, marginTop: 4 }}><UserRound size={13} aria-hidden /> {course.faculty_name || 'Faculty TBA'}</div>
      </div>
      <div className="seat-meter">
        <div className="row row--between">
          <span><strong data-testid={`seats-${course.id}`}>{course.seats_available}</strong> of {course.capacity} seats open</span>
          {full && <Badge tone="danger">Full</Badge>}
        </div>
        <ProgressBar value={fill} tone={full ? 'danger' : fill >= 85 ? 'warning' : undefined} label="Seats filled" />
      </div>
      {course.is_enrolled ? (
        <Badge tone="success" icon={CheckCircle2}>Enrolled</Badge>
      ) : canEnroll ? (
        // Not disabled at the cap / when closed on purpose: the server rejects the attempt and the error is shown (US-06).
        <Button size="sm" disabled={full} loading={busy} title={blockedReason || undefined} onClick={() => onEnroll(course)}>
          {full ? 'Section full' : 'Enroll'}
        </Button>
      ) : null}
    </article>
  );
}

export default function CatalogPage() {
  const { user } = useAuth();
  const toast = useToast();
  const [search, setSearch] = useState('');
  const [busyId, setBusyId] = useState(null);
  const debounced = useDebounced(search);
  const state = useAsync(() => getCatalog(debounced), [debounced]);
  const isStudent = user.role === 'Student';

  const onEnroll = async (course) => {
    setBusyId(course.id);
    try {
      const result = await enroll(course.id);
      toast.success(result.message);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusyId(null);
      state.reload({ silent: true }); // refresh seat counts either way (someone else may have taken the last seat)
    }
  };

  const onWindow = async (open) => {
    try {
      await setWindow(open);
      toast.success(`Enrollment ${open ? 'opened' : 'closed'}.`);
      state.reload({ silent: true });
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <>
      <AsyncBoundary state={state}>
        {(data) => {
          const atLimit = data.my_course_count >= data.max_courses;
          const blocked = !data.window_open ? 'Enrollment is closed' : atLimit ? `Limit of ${data.max_courses} courses reached` : '';
          return (
            <>
              <PageHeader
                title="Course catalog"
                subtitle={`${data.term} · live seat availability`}
                actions={
                  isStudent ? (
                    <div style={{ minWidth: 200 }}>
                      <div className="row row--between small"><strong>{data.my_course_count} / {data.max_courses}</strong><span className="muted">courses this term</span></div>
                      <ProgressBar value={(data.my_course_count / data.max_courses) * 100} tone={atLimit ? 'danger' : undefined} label="Courses enrolled this term" />
                    </div>
                  ) : (
                    <label className="row small"><strong>Enrollment window</strong>
                      <Toggle checked={data.window_open} onChange={onWindow} label="Enrollment window open" />
                      <Badge tone={data.window_open ? 'success' : 'danger'}>{data.window_open ? 'Open' : 'Closed'}</Badge>
                    </label>
                  )
                }
              />
              {isStudent && !data.window_open && <Alert tone="warning" title="Enrollment is closed">An administrator has closed the enrollment window.</Alert>}
              {isStudent && atLimit && data.window_open && <Alert tone="info" title="Course limit reached">You are enrolled in the maximum of {data.max_courses} courses this term.</Alert>}
              <div className="toolbar">
                <SearchInput value={search} onChange={setSearch} placeholder="Search by code or title" label="Search catalog" />
              </div>
              {data.courses.length === 0 ? (
                <Card><EmptyState title="No sections match your search" icon={Lock} /></Card>
              ) : (
                <div className="grid grid--auto">
                  {data.courses.map((c) => (
                    <CourseCard key={c.id} course={c} canEnroll={isStudent} blockedReason={blocked} onEnroll={onEnroll} busy={busyId === c.id} />
                  ))}
                </div>
              )}
            </>
          );
        }}
      </AsyncBoundary>
    </>
  );
}

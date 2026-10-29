import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { Slot } from '../../../core/Slot.jsx';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtNumber } from '../../../core/utils/format.js';
import { Alert, AsyncBoundary, Button, Card, GradeStateBadge, Input, PageHeader, useToast } from '../../../core/ui/index.js';
import { gradeGrid, saveDrafts } from '../api.js';

const valid = (v) => v !== '' && !Number.isNaN(Number(v)) && Number(v) >= 0 && Number(v) <= 100;

function Grid({ data, reload, courseId }) {
  const toast = useToast();
  const { rubric, students, course } = data;
  // edits[enrollmentId][rubricId] = string typed by the user (only for cells that differ from the server value)
  const [edits, setEdits] = useState({});
  const [busy, setBusy] = useState(false);

  const valueOf = (s, r) => edits[s.enrollment_id]?.[r.id] ?? (s.scores[r.id] !== undefined ? String(s.scores[r.id]) : '');
  const setCell = (s, r, value) => setEdits((e) => ({ ...e, [s.enrollment_id]: { ...e[s.enrollment_id], [r.id]: value } }));

  const preview = (s) => {
    const values = rubric.map((r) => valueOf(s, r));
    if (!values.every(valid)) return null;
    return rubric.reduce((sum, r, i) => sum + (Number(values[i]) * r.weight) / 100, 0);
  };

  const dirtyStudents = useMemo(
    () => students.filter((s) => s.editable && s.enrollment_id in edits && Object.keys(edits[s.enrollment_id]).length),
    [students, edits],
  );
  const invalid = dirtyStudents.some((s) => Object.entries(edits[s.enrollment_id]).some(([, v]) => v !== '' && !valid(v)));

  const save = async () => {
    const payload = dirtyStudents
      .map((s) => ({
        student_id: s.student_id,
        rubric_scores: rubric.filter((r) => valid(valueOf(s, r))).map((r) => ({ rubric_id: r.id, score: Number(valueOf(s, r)) })),
      }))
      .filter((p) => p.rubric_scores.length);
    if (!payload.length) return;
    setBusy(true);
    try {
      const result = await saveDrafts(courseId, payload);
      toast.success(result.message);
      setEdits({});
      await reload({ silent: true });
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  };

  const onChanged = async () => {
    setEdits({});
    await reload({ silent: true });
  };

  const editableCount = students.filter((s) => s.editable).length;

  return (
    <>
      <PageHeader
        title={`${course.code}-${course.section} grade sheet`}
        subtitle={`${course.title} · scores out of 100 per component; weighted using the course rubric`}
        actions={<Slot name="grade-entry-actions" props={{ courseId, students, onChanged, hasUnsaved: dirtyStudents.length > 0 }} />}
      />
      <Alert tone="info">Marks stay hidden from students while a grade is in <strong>Draft</strong>. Partial entries are fine — save as you go.</Alert>
      <Card
        flush
        footer={
          <>
            <span>{dirtyStudents.length ? `${dirtyStudents.length} student(s) with unsaved changes` : `${editableCount} of ${students.length} editable`}</span>
            <Button icon={Save} loading={busy} disabled={!dirtyStudents.length || invalid} onClick={save}>Save drafts</Button>
          </>
        }
      >
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Student</th>
                {rubric.map((r) => <th key={r.id} className="num">{r.name}<div className="faint" style={{ fontWeight: 500, textTransform: 'none' }}>{r.weight}%</div></th>)}
                <th className="num">Weighted total</th>
                <th>State</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => {
                const total = s.editable ? preview(s) : s.weighted_total;
                return (
                  <tr key={s.enrollment_id}>
                    <td><div className="cell-main">{s.full_name}</div><div className="cell-sub mono">{s.student_id}</div></td>
                    {rubric.map((r) => {
                      const value = valueOf(s, r);
                      const dirty = edits[s.enrollment_id]?.[r.id] !== undefined;
                      return (
                        <td key={r.id} className="num">
                          <Input
                            small
                            className={`score-input ${dirty ? 'dirty' : ''}`}
                            type="number" min={0} max={100} step="1" inputMode="decimal"
                            aria-label={`${r.name} score for ${s.full_name}`}
                            aria-invalid={value !== '' && !valid(value) ? 'true' : undefined}
                            value={value}
                            disabled={!s.editable}
                            onChange={(e) => setCell(s, r, e.target.value)}
                          />
                        </td>
                      );
                    })}
                    <td className="num cell-main">{total === null || total === undefined ? <span className="faint">—</span> : fmtNumber(total, 2)}</td>
                    <td><GradeStateBadge state={s.state} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

export default function GradeEntryPage() {
  const { courseId } = useParams();
  const state = useAsync(() => gradeGrid(courseId), [courseId]);
  return (
    <>
      <Link to="/grading" className="small row" style={{ marginBottom: 12 }}><ArrowLeft size={14} aria-hidden /> All sections</Link>
      <AsyncBoundary state={state}>{(data) => <Grid data={data} reload={state.reload} courseId={courseId} />}</AsyncBoundary>
    </>
  );
}

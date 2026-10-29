import { useMemo, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { Alert, Badge, Button, Field, IconButton, Input, Modal, Select, useToast } from '../../../core/ui/index.js';
import { createCourse, facultyOptions, updateCourse } from '../api.js';
import { previewNormalized } from '../normalize.js';

const CATEGORIES = ['Assignments', 'Exams', 'Projects', 'Other'];
const blankRow = (category = 'Assignments') => ({ name: '', category, weight: '' });

function initialState(course) {
  if (!course) {
    return {
      code: '', title: '', section: 'A', credits: 3, capacity: 60, assigned_faculty_id: '',
      rubric: [{ name: 'Assignments', category: 'Assignments', weight: 30 }, { name: 'Mid-term Exam', category: 'Exams', weight: 30 }, { name: 'Final Exam', category: 'Exams', weight: 40 }],
    };
  }
  return {
    code: course.code, title: course.title, section: course.section, credits: course.credits, capacity: course.capacity,
    assigned_faculty_id: course.assigned_faculty_id ?? '',
    rubric: course.rubric.map((r) => ({ name: r.name, category: r.category, weight: r.raw_weight })),
  };
}

export default function CourseForm({ course, onClose, onSaved }) {
  const toast = useToast();
  const faculty = useAsync(facultyOptions, []);
  const [form, setForm] = useState(() => initialState(course));
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const setRow = (i, key, value) => setForm((f) => ({ ...f, rubric: f.rubric.map((r, idx) => (idx === i ? { ...r, [key]: value } : r)) }));
  const addRow = () => setForm((f) => ({ ...f, rubric: [...f.rubric, blankRow()] }));
  const removeRow = (i) => setForm((f) => ({ ...f, rubric: f.rubric.filter((_, idx) => idx !== i) }));

  const normalized = useMemo(() => previewNormalized(form.rubric.map((r) => r.weight)), [form.rubric]);
  const rawTotal = form.rubric.reduce((sum, r) => sum + (Number(r.weight) || 0), 0);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!normalized || form.rubric.some((r) => !r.name.trim())) {
      setError('Every rubric component needs a name and a weight greater than zero.');
      return;
    }
    const payload = {
      ...form,
      credits: Number(form.credits),
      capacity: Number(form.capacity),
      assigned_faculty_id: Number(form.assigned_faculty_id),
      rubric: form.rubric.map((r) => ({ ...r, weight: Number(r.weight) })),
    };
    // Marks lock the rubric server-side, so only send it when it was actually edited.
    const rubricUnchanged =
      course &&
      JSON.stringify(payload.rubric) === JSON.stringify(course.rubric.map((r) => ({ name: r.name, category: r.category, weight: r.raw_weight })));
    if (rubricUnchanged) delete payload.rubric;
    setBusy(true);
    try {
      course ? await updateCourse(course.id, payload) : await createCourse(payload);
      toast.success(course ? 'Course updated.' : 'Course created. Rubric weights were normalized to 100%.');
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      wide
      title={course ? `Edit ${course.code}-${course.section}` : 'New course offering'}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" form="course-form" loading={busy}>{course ? 'Save changes' : 'Create course'}</Button>
        </>
      }
    >
      <form id="course-form" onSubmit={submit} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}
        <div className="form-row">
          <Field label="Course code"><Input value={form.code} onChange={set('code')} placeholder="CS501" required /></Field>
          <Field label="Section"><Input value={form.section} onChange={set('section')} maxLength={10} /></Field>
        </div>
        <Field label="Title"><Input value={form.title} onChange={set('title')} required /></Field>
        <div className="form-row">
          <Field label="Credits"><Input type="number" min={1} max={6} value={form.credits} onChange={set('credits')} /></Field>
          <Field label="Seat capacity"><Input type="number" min={1} value={form.capacity} onChange={set('capacity')} /></Field>
        </div>
        <Field label="Primary faculty">
          <Select value={form.assigned_faculty_id} onChange={set('assigned_faculty_id')} required>
            <option value="">Select faculty…</option>
            {faculty.data?.faculty.map((f) => <option key={f.id} value={f.id}>{f.full_name} ({f.institutional_id})</option>)}
          </Select>
        </Field>

        <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="field__label" style={{ marginBottom: 8 }}>Evaluation rubric</legend>
          <Alert tone="info">Enter any relative weights — the server normalizes them so they total exactly 100%.</Alert>
          {form.rubric.map((row, i) => (
            <div className="rubric-row" key={i}>
              <Input aria-label={`Component ${i + 1} name`} placeholder="Component name" value={row.name} onChange={(e) => setRow(i, 'name', e.target.value)} />
              <Select aria-label={`Component ${i + 1} category`} value={row.category} onChange={(e) => setRow(i, 'category', e.target.value)}>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </Select>
              <Input aria-label={`Component ${i + 1} raw weight`} type="number" min="0" step="any" placeholder="Weight" value={row.weight} onChange={(e) => setRow(i, 'weight', e.target.value)} />
              <Badge tone={normalized ? 'primary' : 'neutral'}>{normalized ? `${normalized[i].toFixed(2)}%` : '—'}</Badge>
              <IconButton icon={Trash2} label={`Remove component ${i + 1}`} onClick={() => removeRow(i)} disabled={form.rubric.length <= 1} />
            </div>
          ))}
          <div className="row row--between">
            <Button variant="secondary" size="sm" icon={Plus} onClick={addRow}>Add component</Button>
            <span className="small muted">Raw total {rawTotal || 0} → <strong>{normalized ? '100.00%' : '—'}</strong></span>
          </div>
        </fieldset>
      </form>
    </Modal>
  );
}

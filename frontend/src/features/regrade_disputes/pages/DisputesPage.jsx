import { useState } from 'react';
import { CheckCheck } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtDateTime, fmtNumber } from '../../../core/utils/format.js';
import { Alert, AsyncBoundary, Badge, Button, Card, EmptyState, Field, Input, PageHeader, Tabs, Textarea, useToast } from '../../../core/ui/index.js';
import { listDisputes, resolveDispute } from '../api.js';

const valid = (v) => v !== '' && !Number.isNaN(Number(v)) && Number(v) >= 0 && Number(v) <= 100;

function DisputeCard({ dispute, onResolved }) {
  const toast = useToast();
  const open = dispute.status === 'Open';
  const [scores, setScores] = useState(() => Object.fromEntries(dispute.rubric.map((r) => [r.id, r.score ?? ''])));
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const total = dispute.rubric.every((r) => valid(String(scores[r.id]))) ? dispute.rubric.reduce((sum, r) => sum + (Number(scores[r.id]) * r.weight) / 100, 0) : null;

  const resolve = async () => {
    if (!note.trim()) return setError('Add a short resolution note for the student.');
    if (total === null) return setError('Every rubric score must be a number between 0 and 100.');
    setError('');
    setBusy(true);
    try {
      const result = await resolveDispute(dispute.id, {
        resolution_note: note,
        rubric_scores: dispute.rubric.map((r) => ({ rubric_id: r.id, score: Number(scores[r.id]) })),
      });
      toast.success(result.message);
      window.dispatchEvent(new Event('srs:disputes-changed'));
      onResolved();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      title={`${dispute.course.code}-${dispute.course.section} · ${dispute.student.full_name}`}
      actions={<Badge tone={open ? 'violet' : 'success'}>{open ? 'Under Review' : 'Resolved'}</Badge>}
    >
      <p className="small muted">{dispute.student.institutional_id} · filed {fmtDateTime(dispute.filed_at)} · published total {fmtNumber(dispute.previous_total, 2)}</p>
      <blockquote style={{ margin: '12px 0', padding: '10px 14px', borderLeft: '3px solid var(--violet)', background: 'var(--surface-2)', borderRadius: 8 }}>{dispute.reason}</blockquote>

      {open ? (
        <>
          {error && <Alert tone="danger">{error}</Alert>}
          <div className="form-row">
            {dispute.rubric.map((r) => (
              <Field key={r.id} label={`${r.name} (${r.weight}%)`}>
                <Input type="number" min={0} max={100} step="1" value={scores[r.id]} onChange={(e) => setScores((s) => ({ ...s, [r.id]: e.target.value }))} />
              </Field>
            ))}
          </div>
          <Field label="Resolution note" hint="Visible to the student.">
            <Textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} maxLength={1000} />
          </Field>
          <div className="row row--between">
            <span className="small muted">New weighted total: <strong>{total === null ? '—' : fmtNumber(total, 2)}</strong></span>
            <Button icon={CheckCheck} loading={busy} onClick={resolve}>Re-evaluate &amp; re-publish</Button>
          </div>
        </>
      ) : (
        <p className="small"><strong>Resolution:</strong> {dispute.resolution_note} — total now {fmtNumber(dispute.current_total, 2)}</p>
      )}
    </Card>
  );
}

export default function DisputesPage() {
  const [tab, setTab] = useState('Open');
  const state = useAsync(() => listDisputes(tab), [tab]);
  return (
    <>
      <PageHeader title="Regrade requests" subtitle="Re-evaluate disputed scores. Resolving a request re-publishes the grade to the student." />
      <Tabs tabs={[{ id: 'Open', label: 'Open' }, { id: 'Resolved', label: 'Resolved' }]} active={tab} onChange={setTab} label="Request status" />
      <AsyncBoundary state={state}>
        {({ disputes }) =>
          disputes.length === 0 ? (
            <Card><EmptyState title={tab === 'Open' ? 'No open regrade requests' : 'No resolved requests yet'} /></Card>
          ) : (
            <div className="stack">
              {disputes.map((d) => <DisputeCard key={d.id} dispute={d} onResolved={() => state.reload({ silent: true })} />)}
            </div>
          )
        }
      </AsyncBoundary>
    </>
  );
}

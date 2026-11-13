import { useState } from 'react';
import { Flag, Lock } from 'lucide-react';
import { Alert, Badge, Button, Field, Modal, Textarea, useToast } from '../../../core/ui/index.js';
import { fileDispute } from '../api.js';

const MIN = 10;

/** Shown next to a published grade. Requires a written justification before the grade moves to Under Review. */
export default function DisputeButton({ grade, onChanged }) {
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  // Only one regrade per grade: the server decides (can_dispute) and enforces it again on submit.
  if (grade.dispute && !grade.dispute.open) return <Badge tone="neutral" icon={Lock}>Regrade used · final</Badge>;
  if (!grade.can_dispute) return null;

  const close = () => { setOpen(false); setReason(''); setError(''); };

  const submit = async (e) => {
    e.preventDefault();
    if (reason.trim().length < MIN) return setError(`Please explain your request in at least ${MIN} characters.`);
    setBusy(true);
    try {
      const result = await fileDispute(grade.enrollment_id, reason);
      toast.success(result.message);
      close();
      await onChanged();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Button size="sm" variant="secondary" icon={Flag} onClick={() => setOpen(true)} aria-label={`Dispute grade for ${grade.code}`}>Dispute</Button>
      {open && (
        <Modal
          title={`Request a regrade — ${grade.code}`}
          onClose={close}
          footer={<><Button variant="secondary" onClick={close}>Cancel</Button><Button type="submit" form="dispute-form" loading={busy}>Submit request</Button></>}
        >
          <form id="dispute-form" onSubmit={submit} noValidate>
            <p className="muted" style={{ marginBottom: 14 }}>Your faculty will re-evaluate your marks. While under review the grade is marked <strong>Under Review</strong>.</p>
            {error && <Alert tone="danger">{error}</Alert>}
            <Field label="Why should this grade be re-evaluated?" hint={`${reason.trim().length}/${MIN} characters minimum`}>
              <Textarea data-autofocus value={reason} onChange={(e) => setReason(e.target.value)} rows={5} maxLength={1000} />
            </Field>
          </form>
        </Modal>
      )}
    </>
  );
}

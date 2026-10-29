import { useState } from 'react';
import { Send } from 'lucide-react';
import { Button, ConfirmDialog, useToast } from '../../../core/ui/index.js';
import { submitCourse } from '../api.js';

/** Rendered in the grade sheet's 'grade-entry-actions' slot. */
export default function SubmitGradesButton({ courseId, students, onChanged, hasUnsaved }) {
  const toast = useToast();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const drafts = students.filter((s) => s.state === 'Draft').length;

  const submit = async () => {
    setBusy(true);
    try {
      const result = await submitCourse(courseId);
      toast.success(result.message);
      if (result.skipped.length) {
        toast.info(`${result.skipped.length} student(s) skipped - incomplete marks: ${result.skipped.slice(0, 3).map((s) => s.student_id).join(', ')}${result.skipped.length > 3 ? '…' : ''}`);
      }
      await onChanged();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  };

  return (
    <>
      <Button icon={Send} variant="secondary" disabled={drafts === 0 || hasUnsaved} title={hasUnsaved ? 'Save your drafts first' : undefined} onClick={() => setConfirming(true)}>
        Submit grades ({drafts})
      </Button>
      {confirming && (
        <ConfirmDialog
          title="Submit grades for publication?"
          message={`Weighted totals will be calculated for every complete Draft (${drafts} student${drafts === 1 ? '' : 's'}) and sent to the administrator. Students with incomplete marks stay in Draft. Submitted marks can no longer be edited.`}
          confirmLabel="Submit"
          loading={busy}
          onCancel={() => setConfirming(false)}
          onConfirm={submit}
        />
      )}
    </>
  );
}

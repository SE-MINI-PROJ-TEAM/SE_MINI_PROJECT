import { useState } from 'react';
import { Download, Gauge } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtPercent } from '../../../core/utils/format.js';
import { AsyncBoundary, Button, Card, Stat, useToast } from '../../../core/ui/index.js';
import { exportCsv, getMetrics } from '../api.js';

export default function MetricsWidget() {
  const toast = useToast();
  const state = useAsync(getMetrics, []);
  const [busy, setBusy] = useState(false);

  const onExport = async () => {
    setBusy(true);
    try {
      const name = await exportCsv();
      toast.success(`Exported ${name}`);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card
      title="Institution metrics"
      icon={Gauge}
      actions={<Button icon={Download} loading={busy} onClick={onExport}>Export CSV</Button>}
    >
      <AsyncBoundary state={state}>
        {({ metrics: m }) => (
          <div className="stat-grid">
            <Stat label="Students" value={m.students} />
            <Stat label="Faculty" value={m.faculty} />
            <Stat label="Courses" value={m.courses} />
            <Stat label="Enrollments" value={m.total_enrollments} />
            <Stat label="Unsubmitted grades" value={m.unsubmitted_grades} />
            <Stat label="Open regrade requests" value={m.open_disputes} />
            <Stat label="Attendance rate" value={fmtPercent(m.attendance_rate_pct)} />
          </div>
        )}
      </AsyncBoundary>
    </Card>
  );
}

import { useState } from 'react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Badge, Card, EmptyState, PageHeader, Pagination, Select } from '../../../core/ui/index.js';
import { fmtDateTime } from '../../../core/utils/format.js';
import { listAuditLogs } from '../api.js';

const ACTIONS = [
  'USER_CREATED', 'USER_STATUS_CHANGED', 'USER_ROLE_CHANGED', 'ATTENDANCE_OVERRIDE',
  'GRADES_PUBLISHED', 'DISPUTE_RESOLVED', 'SETTING_CHANGED',
];
const TONES = { ATTENDANCE_OVERRIDE: 'warning', USER_STATUS_CHANGED: 'danger', GRADES_PUBLISHED: 'success', DISPUTE_RESOLVED: 'violet' };

const label = (action) => action.replaceAll('_', ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

function Details({ details }) {
  const entries = Object.entries(details || {});
  if (!entries.length) return <span className="faint">—</span>;
  return (
    <div className="row" style={{ gap: 6 }}>
      {entries.map(([key, value]) => (
        <span key={key} className="badge" title={key}>
          <span className="faint">{key.replaceAll('_', ' ')}:</span> {String(value)}
        </span>
      ))}
    </div>
  );
}

export default function AuditLogPage() {
  const [action, setAction] = useState('');
  const [page, setPage] = useState(1);
  const state = useAsync(() => listAuditLogs({ action, page, per_page: 20 }), [action, page]);

  return (
    <>
      <PageHeader title="Audit log" subtitle="Immutable record of administrative actions." />
      <div className="toolbar">
        <Select aria-label="Filter by action" value={action} onChange={(e) => { setAction(e.target.value); setPage(1); }}>
          <option value="">All actions</option>
          {ACTIONS.map((a) => <option key={a} value={a}>{label(a)}</option>)}
        </Select>
      </div>
      <Card flush>
        <AsyncBoundary state={state}>
          {(data) =>
            data.logs.length === 0 ? (
              <EmptyState title="No audit entries yet" />
            ) : (
              <>
                <div className="table-wrap">
                  <table className="table">
                    <thead><tr><th>When</th><th>Action</th><th>Performed by</th><th>Details</th></tr></thead>
                    <tbody>
                      {data.logs.map((log) => (
                        <tr key={log.id}>
                          <td className="cell-sub" style={{ whiteSpace: 'nowrap' }}>{fmtDateTime(log.created_at)}</td>
                          <td><Badge tone={TONES[log.action] || 'primary'}>{label(log.action)}</Badge></td>
                          <td><div className="cell-main">{log.actor.name}</div><div className="cell-sub">{log.actor.institutional_id}</div></td>
                          <td><Details details={log.details} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
              </>
            )
          }
        </AsyncBoundary>
      </Card>
    </>
  );
}

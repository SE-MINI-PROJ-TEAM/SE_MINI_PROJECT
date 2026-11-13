import { Link } from 'react-router-dom';
import { MessageSquareWarning } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtDateTime } from '../../../core/utils/format.js';
import { AsyncBoundary, Badge, Card, EmptyState } from '../../../core/ui/index.js';
import { listDisputes } from '../api.js';

export default function PendingDisputesWidget() {
  const state = useAsync(() => listDisputes('Open'), []);
  return (
    <Card title="Regrade requests" icon={MessageSquareWarning} actions={<Link to="/disputes" className="btn btn--secondary btn--sm">Review</Link>}>
      <AsyncBoundary state={state}>
        {({ disputes }) =>
          disputes.length === 0 ? (
            <EmptyState title="No open requests" />
          ) : (
            <>
              <p style={{ marginBottom: 10 }}><Badge tone="danger">{disputes.length} awaiting review</Badge></p>
              <ul className="list">
                {disputes.slice(0, 3).map((d) => (
                  <li key={d.id} className="list__item">
                    <div className="grow"><div className="cell-main">{d.student.full_name}</div><div className="cell-sub">{d.course.code} · {fmtDateTime(d.filed_at)}</div></div>
                  </li>
                ))}
              </ul>
            </>
          )
        }
      </AsyncBoundary>
    </Card>
  );
}

import { Link } from 'react-router-dom';
import { ClipboardCheck } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtDate, fmtTime } from '../../../core/utils/format.js';
import { AsyncBoundary, Card, EmptyState } from '../../../core/ui/index.js';
import { listSessions } from '../api.js';
import SessionStatus from './SessionStatus.jsx';

/** Faculty dashboard: open sessions that still need (or can still amend) roll-call - one click to the roster. */
export default function OpenRollCallsWidget() {
  const state = useAsync(listSessions, []);
  return (
    <Card title="Roll-call needed" icon={ClipboardCheck} actions={<Link to="/attendance" className="btn btn--secondary btn--sm">All sessions</Link>}>
      <AsyncBoundary state={state}>
        {({ sessions }) => {
          const open = sessions.filter((s) => s.status === 'open');
          return open.length === 0 ? (
            <EmptyState title="No open sessions">Sessions are editable until 48 hours after they start.</EmptyState>
          ) : (
            <ul className="list">
              {open.map((s) => (
                <li key={s.id} className="list__item">
                  <div className="grow">
                    <div className="cell-main">{s.course_code}-{s.section} · {s.course_title}</div>
                    <div className="cell-sub">{fmtDate(s.start_time)} {fmtTime(s.start_time)} · {s.marked_count}/{s.enrolled_count} marked</div>
                  </div>
                  <SessionStatus status={s.status} frozenAt={s.frozen_at} />
                  <Link to={`/attendance/${s.id}`} className="btn btn--primary btn--sm">{s.marked_count ? 'Review' : 'Take attendance'}</Link>
                </li>
              ))}
            </ul>
          );
        }}
      </AsyncBoundary>
    </Card>
  );
}

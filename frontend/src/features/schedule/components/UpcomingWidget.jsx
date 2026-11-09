import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { CalendarDays } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtDate, fmtRange } from '../../../core/utils/format.js';
import { AsyncBoundary, Badge, Card, EmptyState } from '../../../core/ui/index.js';
import { getCalendar } from '../api.js';

/** Dashboard widget: sessions in the next 7 days (a compact weekly view). */
export default function UpcomingWidget() {
  const range = useMemo(() => {
    const from = new Date();
    from.setHours(0, 0, 0, 0);
    const to = new Date(from);
    to.setDate(to.getDate() + 7);
    return [from.toISOString(), to.toISOString()];
  }, []);
  const state = useAsync(() => getCalendar(...range), []);

  return (
    <Card title="This week" icon={CalendarDays} actions={<Link to="/schedule" className="btn btn--secondary btn--sm">Full calendar</Link>}>
      <AsyncBoundary state={state}>
        {({ sessions }) =>
          sessions.length === 0 ? (
            <EmptyState title="No sessions scheduled for the next 7 days" />
          ) : (
            <ul className="list">
              {sessions.slice(0, 7).map((s) => {
                const live = new Date(s.start_time) <= new Date() && new Date(s.end_time) >= new Date();
                return (
                  <li key={s.id} className="list__item">
                    <div className="grow">
                      <div className="cell-main">{s.course_code}-{s.section} · {s.course_title}</div>
                      <div className="cell-sub">{fmtDate(s.start_time)} · {fmtRange(s.start_time, s.end_time)} · Room {s.room}</div>
                    </div>
                    {live && <Badge tone="success">Now</Badge>}
                  </li>
                );
              })}
              {sessions.length > 7 && <li className="small muted">+ {sessions.length - 7} more this week</li>}
            </ul>
          )
        }
      </AsyncBoundary>
    </Card>
  );
}

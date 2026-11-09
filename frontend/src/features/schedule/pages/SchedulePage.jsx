import { useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '../../../core/auth/AuthContext.jsx';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { addDays, startOfWeek } from '../../../core/utils/format.js';
import { AsyncBoundary, Button, PageHeader } from '../../../core/ui/index.js';
import WeekCalendar from '../components/WeekCalendar.jsx';
import { getCalendar } from '../api.js';

const label = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' });

export default function SchedulePage() {
  const { user } = useAuth();
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const end = useMemo(() => addDays(weekStart, 7), [weekStart]);
  const state = useAsync(() => getCalendar(weekStart.toISOString(), end.toISOString()), [weekStart]);

  return (
    <>
      <PageHeader
        title="Weekly schedule"
        subtitle={`${label.format(weekStart)} – ${label.format(addDays(weekStart, 6))}`}
        actions={
          <div className="row">
            <Button variant="secondary" size="sm" icon={ChevronLeft} onClick={() => setWeekStart(addDays(weekStart, -7))}>Previous</Button>
            <Button variant="secondary" size="sm" onClick={() => setWeekStart(startOfWeek(new Date()))}>This week</Button>
            <Button variant="secondary" size="sm" onClick={() => setWeekStart(addDays(weekStart, 7))}>Next <ChevronRight size={16} aria-hidden /></Button>
          </div>
        }
      />
      <AsyncBoundary state={state}>
        {({ sessions }) => <WeekCalendar weekStart={weekStart} sessions={sessions} showFaculty={user.role !== 'Faculty'} />}
      </AsyncBoundary>
    </>
  );
}

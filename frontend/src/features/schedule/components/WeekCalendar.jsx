import { addDays, fmtRange, sameDay } from '../../../core/utils/format.js';

const dayName = new Intl.DateTimeFormat(undefined, { weekday: 'short' });
const dayNum = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' });

/** Seven day columns (stacks on small screens) populated with the sessions that start on each local day. */
export default function WeekCalendar({ weekStart, sessions, showFaculty }) {
  const now = new Date();
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  return (
    <div className="calendar" role="list" aria-label="Weekly timetable">
      {days.map((day) => {
        const items = sessions.filter((s) => sameDay(new Date(s.start_time), day));
        return (
          <section key={day.toISOString()} className={`cal-day ${sameDay(day, now) ? 'today' : ''}`} role="listitem" aria-label={`${dayName.format(day)} ${dayNum.format(day)}`}>
            <div className="cal-day__head">{dayName.format(day)} <span>{dayNum.format(day)}</span></div>
            {items.length === 0 && <span className="faint small">No sessions</span>}
            {items.map((s) => (
              <div key={s.id} className={`cal-event ${new Date(s.end_time) < now ? 'past' : ''}`}>
                <strong>{s.course_code}-{s.section}</strong>
                {fmtRange(s.start_time, s.end_time)} · {s.room}
                {showFaculty && s.faculty_name && <div className="faint">{s.faculty_name}</div>}
              </div>
            ))}
          </section>
        );
      })}
    </div>
  );
}

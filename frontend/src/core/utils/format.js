const dateTime = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });
const dateOnly = new Intl.DateTimeFormat(undefined, { weekday: 'short', day: 'numeric', month: 'short' });
const timeOnly = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' });

export const fmtDateTime = (iso) => (iso ? dateTime.format(new Date(iso)) : '—');
export const fmtDate = (iso) => (iso ? dateOnly.format(new Date(iso)) : '—');
export const fmtTime = (iso) => (iso ? timeOnly.format(new Date(iso)) : '—');
export const fmtRange = (start, end) => `${fmtTime(start)} – ${fmtTime(end)}`;
export const fmtNumber = (n, digits = 1) => (n === null || n === undefined ? '—' : Number(n).toFixed(digits));
export const fmtPercent = (n) => (n === null || n === undefined ? '—' : `${Number(n).toFixed(1)}%`);

export function initials(name = '') {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join('');
}

/** "5h 12m" style countdown to an ISO instant (empty when already past). */
export function timeUntil(iso, now = Date.now()) {
  const ms = new Date(iso).getTime() - now;
  if (ms <= 0) return '';
  const minutes = Math.floor(ms / 60000);
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  if (days) return `${days}d ${hours}h`;
  return hours ? `${hours}h ${minutes % 60}m` : `${minutes % 60}m`;
}

/** Monday 00:00 (local) of the week containing `date`. */
export function startOfWeek(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d;
}

export const addDays = (date, n) => {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
};

export const sameDay = (a, b) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

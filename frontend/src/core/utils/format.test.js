import { describe, expect, it } from 'vitest';
import { addDays, initials, startOfWeek, timeUntil } from './format.js';

describe('format helpers', () => {
  it('initials', () => {
    expect(initials('Asha Rao')).toBe('AR');
    expect(initials('')).toBe('');
  });

  it('timeUntil renders a countdown and empties once past', () => {
    const now = Date.UTC(2026, 0, 1);
    expect(timeUntil(new Date(now + (5 * 3600 + 12 * 60) * 1000).toISOString(), now)).toBe('5h 12m');
    expect(timeUntil(new Date(now + 26 * 3600 * 1000).toISOString(), now)).toBe('1d 2h');
    expect(timeUntil(new Date(now - 1000).toISOString(), now)).toBe('');
  });

  it('startOfWeek returns Monday 00:00', () => {
    const monday = startOfWeek(new Date(2026, 9, 29, 15, 30)); // Thu 29 Oct 2026
    expect([monday.getDay(), monday.getDate(), monday.getHours()]).toEqual([1, 26, 0]);
    expect(addDays(monday, 7).getDate()).toBe(2);
  });
});

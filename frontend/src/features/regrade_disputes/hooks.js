import { useEffect, useState } from 'react';
import { pendingCount } from './api.js';

/** Notification indicator: open regrade requests, refreshed every minute and when the tab regains focus. */
export function usePendingDisputes() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let alive = true;
    const load = () => pendingCount().then((r) => alive && setCount(r.count)).catch(() => {});
    load();
    const timer = setInterval(load, 60000);
    window.addEventListener('focus', load);
    window.addEventListener('srs:disputes-changed', load);
    return () => {
      alive = false;
      clearInterval(timer);
      window.removeEventListener('focus', load);
      window.removeEventListener('srs:disputes-changed', load);
    };
  }, []);
  return count;
}

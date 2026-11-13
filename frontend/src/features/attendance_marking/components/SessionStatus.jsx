import { Lock, Radio, Clock } from 'lucide-react';
import { Badge } from '../../../core/ui/index.js';
import { timeUntil } from '../../../core/utils/format.js';

/** open = editable now; upcoming = not started; frozen = locked 48h after start. */
export default function SessionStatus({ status, frozenAt }) {
  if (status === 'open') {
    const left = timeUntil(frozenAt);
    return <Badge tone="success" icon={Radio}>Open{left ? ` · locks in ${left}` : ''}</Badge>;
  }
  if (status === 'upcoming') return <Badge tone="info" icon={Clock}>Upcoming</Badge>;
  return <Badge tone="danger" icon={Lock}>Frozen</Badge>;
}

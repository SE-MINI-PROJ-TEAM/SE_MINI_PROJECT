import { TrendingUp } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Badge, Card, EmptyState } from '../../../core/ui/index.js';

import { studentSummary } from '../api.js';

const TONE = { A: 'success', B: 'success', C: 'info', D: 'warning', F: 'danger' };

export default function GpaWidget() {
  const state = useAsync(studentSummary, []);
  return (
    <Card title="Term GPA" icon={TrendingUp} footer={state.data ? <><span>Credit-weighted, 10-point scale</span><span>Loaded in {state.data.query_ms} ms</span></> : null}>
      <AsyncBoundary state={state}>
        {(d) =>
          d.term_gpa === null && d.cumulative_gpa === null ? (
            <EmptyState title="No published grades yet">Your GPA appears once grades are published.</EmptyState>
          ) : (
            <>
              <div className="row" style={{ alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontSize: '2.6rem', fontWeight: 700, letterSpacing: '-0.03em', fontVariantNumeric: 'tabular-nums' }} data-testid="term-gpa">{d.term_gpa?.toFixed(2) ?? '—'}</span>
                <span className="muted">/ 10.00 · {d.term}</span>
              </div>
              <p className="small muted" style={{ margin: '4px 0 14px' }}>{d.term_credits} credits this term · cumulative GPA <strong>{d.cumulative_gpa?.toFixed(2) ?? '—'}</strong> over {d.cumulative_credits} credits</p>
              <div className="row" style={{ gap: 8 }}>
                {d.courses.filter((c) => c.term === d.term).map((c) => (
                  <Badge key={c.course_id} tone={TONE[c.letter]}>{c.code} · {c.letter}</Badge>
                ))}
              </div>
            </>
          )
        }
      </AsyncBoundary>
    </Card>
  );
}

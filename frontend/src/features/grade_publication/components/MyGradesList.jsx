import { Slot } from '../../../core/Slot.jsx';
import { Badge, EmptyState, GradeStateBadge } from '../../../core/ui/index.js';
import { fmtNumber } from '../../../core/utils/format.js';

const LETTER_TONE = { A: 'success', B: 'success', C: 'info', D: 'warning', F: 'danger' };

/**
 * Student grade rows. Marks are only present in the payload once a grade is Published / Under Review.
 * Other stories attach per-row actions (e.g. the regrade dispute button) through the 'grade-row-actions' slot.
 */
export default function MyGradesList({ grades, onChanged }) {
  if (!grades.length) return <EmptyState title="You are not enrolled in any course" />;
  return (
    <ul className="list">
      {grades.map((g) => {
        const visible = g.weighted_total !== undefined;
        return (
          <li key={g.enrollment_id} className="list__item" style={{ alignItems: 'flex-start', flexWrap: 'wrap' }}>
            <div className="grow" style={{ minWidth: 200 }}>
              <div className="cell-main">{g.code}-{g.section} · {g.title}</div>
              <div className="cell-sub">{g.credits} credits</div>
              {visible ? (
                <details style={{ marginTop: 6 }}>
                  <summary className="small" style={{ cursor: 'pointer', color: 'var(--primary)' }}>Rubric breakdown</summary>
                  <table className="table" style={{ marginTop: 6 }}>
                    <tbody>
                      {g.components.map((c) => (
                        <tr key={c.name}><td className="small">{c.name} <span className="faint">({c.weight}%)</span></td><td className="num small">{fmtNumber(c.score, 2)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              ) : (
                <div className="small muted" style={{ marginTop: 4 }}>Marks will appear here once published.</div>
              )}
              {g.dispute?.resolution_note && !g.dispute.open && (
                <div className="small muted" style={{ marginTop: 6 }}>Regrade outcome: “{g.dispute.resolution_note}”</div>
              )}
            </div>
            <div className="row" style={{ gap: 12 }}>
              {visible && (
                <div style={{ textAlign: 'right' }}>
                  <div className="cell-main" style={{ fontSize: '1.15rem', fontVariantNumeric: 'tabular-nums' }}>{fmtNumber(g.weighted_total, 2)}</div>
                  <Badge tone={LETTER_TONE[g.letter]}>Grade {g.letter}</Badge>
                </div>
              )}
              <GradeStateBadge state={g.state} />
              <Slot name="grade-row-actions" props={{ grade: g, onChanged }} />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

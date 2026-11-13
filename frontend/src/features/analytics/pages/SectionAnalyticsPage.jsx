import { useAsync } from '../../../core/hooks/useAsync.js';
import { fmtNumber, fmtPercent } from '../../../core/utils/format.js';
import { AsyncBoundary, Card, EmptyState, PageHeader, Stat } from '../../../core/ui/index.js';
import DistributionChart from '../components/DistributionChart.jsx';
import { facultySections } from '../api.js';

export default function SectionAnalyticsPage() {
  const state = useAsync(facultySections, []);
  return (
    <>
      <PageHeader title="Class analytics" subtitle="Grade distribution (A–F), mean, median and attendance for each of your sections." />
      <AsyncBoundary state={state}>
        {({ sections, query_ms }) =>
          sections.length === 0 ? (
            <Card><EmptyState title="No sections assigned to you" /></Card>
          ) : (
            <>
              <div className="grid grid--2">
                {sections.map((s) => (
                  <Card key={s.course_id} title={`${s.code}-${s.section} · ${s.title}`}>
                    {s.graded === 0 ? (
                      <EmptyState title="No grades submitted yet" />
                    ) : (
                      <DistributionChart distribution={s.distribution} />
                    )}
                    <div className="stat-grid" style={{ marginTop: 16 }}>
                      <Stat label="Mean" value={fmtNumber(s.mean, 1)} />
                      <Stat label="Median" value={fmtNumber(s.median, 1)} />
                      <Stat label="Graded" value={`${s.graded}/${s.enrolled}`} />
                      <Stat label="Attendance" value={fmtPercent(s.attendance_rate)} />
                    </div>
                  </Card>
                ))}
              </div>
              <p className="small faint" style={{ marginTop: 14 }}>Analytics computed in {query_ms} ms.</p>
            </>
          )
        }
      </AsyncBoundary>
    </>
  );
}

import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Card, PageHeader } from '../../../core/ui/index.js';
import MyGradesList from '../components/MyGradesList.jsx';
import { myGrades } from '../api.js';

export default function MyGradesPage() {
  const state = useAsync(myGrades, []);
  return (
    <>
      <PageHeader title="My grades" subtitle="Published grades with their rubric breakdown. You can dispute a published grade." />
      <Card>
        <AsyncBoundary state={state}>{({ grades }) => <MyGradesList grades={grades} onChanged={() => state.reload({ silent: true })} />}</AsyncBoundary>
      </Card>
    </>
  );
}

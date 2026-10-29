import { Link } from 'react-router-dom';
import { GraduationCap } from 'lucide-react';
import { useAsync } from '../../../core/hooks/useAsync.js';
import { AsyncBoundary, Card } from '../../../core/ui/index.js';
import { myGrades } from '../api.js';
import MyGradesList from './MyGradesList.jsx';

export default function MyGradesWidget() {
  const state = useAsync(myGrades, []);
  return (
    <Card title="Course grades" icon={GraduationCap} actions={<Link to="/my-grades" className="btn btn--secondary btn--sm">Open</Link>}>
      <AsyncBoundary state={state}>{({ grades }) => <MyGradesList grades={grades} onChanged={() => state.reload({ silent: true })} />}</AsyncBoundary>
    </Card>
  );
}

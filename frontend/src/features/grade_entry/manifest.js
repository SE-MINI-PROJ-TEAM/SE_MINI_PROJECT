import { lazy } from 'react';
import { PenLine } from 'lucide-react';

// US-11 — Rubric score entry in Draft state
// Exposes the 'grade-entry-actions' slot so other stories (e.g. US-12 submission) can add actions to the grid.
export default {
  id: 'grade-entry',
  routes: [
    {
      path: '/grading',
      roles: ['Faculty'],
      component: lazy(() => import('./pages/GradingCoursesPage.jsx')),
      nav: { label: 'Grade entry', icon: PenLine, section: 'Teaching', order: 12, quick: true },
    },
    { path: '/grading/:courseId', roles: ['Faculty'], component: lazy(() => import('./pages/GradeEntryPage.jsx')) },
  ],
};

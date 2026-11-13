import { lazy } from 'react';
import { BarChart3 } from 'lucide-react';

// US-14 — Consolidated GPA (students) & grade distribution analytics (faculty)
export default {
  id: 'analytics',
  routes: [
    {
      path: '/analytics',
      roles: ['Faculty'],
      component: lazy(() => import('./pages/SectionAnalyticsPage.jsx')),
      nav: { label: 'Class analytics', icon: BarChart3, section: 'Teaching', order: 14, quick: true },
    },
  ],
  slots: {
    'student-dashboard': [{ id: 'gpa', order: 5, component: lazy(() => import('./components/GpaWidget.jsx')) }],
    'faculty-dashboard': [{ id: 'sections', order: 40, span: 2, component: lazy(() => import('./components/SectionSummaryWidget.jsx')) }],
  },
};

import { lazy } from 'react';
import { BadgeCheck, GraduationCap } from 'lucide-react';

// US-12 — Weighted grade submission (faculty) & administrative publication; students see published marks.
// Contributes to slots owned by other stories: 'grade-entry-actions' (US-11) and the role dashboards.
export default {
  id: 'grade-publication',
  routes: [
    {
      path: '/admin/publish',
      roles: ['Admin'],
      component: lazy(() => import('./pages/PublishPage.jsx')),
      nav: { label: 'Publish grades', icon: BadgeCheck, section: 'Administration', order: 40, quick: true },
    },
    {
      path: '/my-grades',
      roles: ['Student'],
      component: lazy(() => import('./pages/MyGradesPage.jsx')),
      nav: { label: 'My grades', icon: GraduationCap, section: 'Academics', order: 30, quick: true },
    },
  ],
  slots: {
    'grade-entry-actions': [{ id: 'submit-grades', roles: ['Faculty'], order: 10, component: lazy(() => import('./components/SubmitGradesButton.jsx')) }],
    'student-dashboard': [{ id: 'my-grades', order: 15, span: 2, component: lazy(() => import('./components/MyGradesWidget.jsx')) }],
    'admin-dashboard': [{ id: 'publish-queue', order: 20, component: lazy(() => import('./components/PublishQueueWidget.jsx')) }],
  },
};

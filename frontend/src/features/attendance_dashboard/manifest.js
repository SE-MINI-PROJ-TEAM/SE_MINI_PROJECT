import { lazy } from 'react';
import { PieChart } from 'lucide-react';

// US-10 — Aggregate attendance dashboard views
export default {
  id: 'attendance-dashboard',
  routes: [
    {
      path: '/my-attendance',
      roles: ['Student'],
      component: lazy(() => import('./pages/AttendancePage.jsx')),
      nav: { label: 'My attendance', icon: PieChart, section: 'Academics', order: 20, quick: true },
    },
    { path: '/my-attendance/:courseId', roles: ['Student'], component: lazy(() => import('./pages/CourseAttendancePage.jsx')) },
  ],
  slots: {
    'student-dashboard': [{ id: 'attendance', order: 20, component: lazy(() => import('./components/AttendanceWidget.jsx')) }],
  },
};

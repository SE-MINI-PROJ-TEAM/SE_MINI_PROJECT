import { lazy } from 'react';
import { CalendarDays, CalendarPlus, Users } from 'lucide-react';

// US-07 — Class schedule creation, weekly calendars & faculty roster isolation
export default {
  id: 'schedule',
  routes: [
    {
      path: '/schedule',
      roles: ['Student', 'Faculty', 'Admin'],
      component: lazy(() => import('./pages/SchedulePage.jsx')),
      nav: { label: 'Weekly schedule', icon: CalendarDays, section: 'Academics', order: 11, quick: true },
    },
    {
      path: '/admin/schedule',
      roles: ['Admin'],
      component: lazy(() => import('./pages/ManageSchedulePage.jsx')),
      nav: { label: 'Manage schedule', icon: CalendarPlus, section: 'Administration', order: 21 },
    },
    {
      path: '/faculty/sections',
      roles: ['Faculty'],
      component: lazy(() => import('./pages/SectionsPage.jsx')),
      nav: { label: 'My sections', icon: Users, section: 'Teaching', order: 10 },
    },
  ],
  slots: {
    'student-dashboard': [{ id: 'week', order: 30, span: 2, component: lazy(() => import('./components/UpcomingWidget.jsx')) }],
    'faculty-dashboard': [{ id: 'week', order: 30, span: 2, component: lazy(() => import('./components/UpcomingWidget.jsx')) }],
  },
};

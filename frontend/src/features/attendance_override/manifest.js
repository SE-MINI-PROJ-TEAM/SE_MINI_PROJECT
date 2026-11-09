import { lazy } from 'react';
import { ShieldCheck } from 'lucide-react';

// US-09 — Administrative attendance override & audit logging
export default {
  id: 'attendance-override',
  routes: [
    {
      path: '/admin/attendance-override',
      roles: ['Admin'],
      component: lazy(() => import('./pages/OverridePage.jsx')),
      nav: { label: 'Attendance override', icon: ShieldCheck, section: 'Administration', order: 30 },
    },
  ],
};

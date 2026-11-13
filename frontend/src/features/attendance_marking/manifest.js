import { lazy } from 'react';
import { ClipboardCheck } from 'lucide-react';

// US-08 — Digitised binary roll-call & 48-hour automated lock
export default {
  id: 'attendance-marking',
  routes: [
    {
      path: '/attendance',
      roles: ['Faculty'],
      component: lazy(() => import('./pages/SessionsPage.jsx')),
      nav: { label: 'Take attendance', icon: ClipboardCheck, section: 'Teaching', order: 11, quick: true },
    },
    { path: '/attendance/:sessionId', roles: ['Faculty', 'Admin'], component: lazy(() => import('./pages/RollCallPage.jsx')) },
  ],
  slots: {
    'faculty-dashboard': [{ id: 'open-rollcalls', order: 10, span: 2, component: lazy(() => import('./components/OpenRollCallsWidget.jsx')) }],
  },
};

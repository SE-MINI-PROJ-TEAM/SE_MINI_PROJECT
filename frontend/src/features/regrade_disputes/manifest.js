import { lazy } from 'react';
import { MessageSquareWarning } from 'lucide-react';
import { usePendingDisputes } from './hooks.js';

// US-13 — Student regrade dispute filing & faculty/admin resolution.
// Student side plugs into the 'grade-row-actions' slot owned by the grades list (US-12).
const PendingWidget = lazy(() => import('./components/PendingDisputesWidget.jsx'));

export default {
  id: 'regrade-disputes',
  routes: [
    {
      path: '/disputes',
      roles: ['Faculty', 'Admin'],
      component: lazy(() => import('./pages/DisputesPage.jsx')),
      nav: { label: 'Regrade requests', icon: MessageSquareWarning, section: 'Teaching', order: 13, quick: true, useBadge: usePendingDisputes },
    },
  ],
  slots: {
    'grade-row-actions': [{ id: 'dispute-button', roles: ['Student'], component: lazy(() => import('./components/DisputeButton.jsx')) }],
    'faculty-dashboard': [{ id: 'pending-disputes', order: 20, component: PendingWidget }],
    'admin-dashboard': [{ id: 'pending-disputes', order: 30, component: PendingWidget }],
  },
};

import { lazy } from 'react';
import { ScrollText, Users } from 'lucide-react';

// US-04 — Admin account status & role metadata management (+ audit log viewer)
export default {
  id: 'account-management',
  routes: [
    {
      path: '/admin/users',
      roles: ['Admin'],
      component: lazy(() => import('./pages/UsersPage.jsx')),
      nav: { label: 'Manage users', icon: Users, section: 'Administration', order: 11, quick: true },
    },
    {
      path: '/admin/audit-log',
      roles: ['Admin'],
      component: lazy(() => import('./pages/AuditLogPage.jsx')),
      nav: { label: 'Audit log', icon: ScrollText, section: 'Administration', order: 12 },
    },
  ],
};

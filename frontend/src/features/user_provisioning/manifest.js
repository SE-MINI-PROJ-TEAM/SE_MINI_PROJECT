import { lazy } from 'react';
import { UserPlus } from 'lucide-react';

// US-01 — Administrative user provisioning & credentials
export default {
  id: 'user-provisioning',
  routes: [
    {
      path: '/admin/users/new',
      roles: ['Admin'],
      component: lazy(() => import('./pages/CreateUserPage.jsx')),
      nav: { label: 'Create user', icon: UserPlus, section: 'Administration', order: 10, quick: true },
    },
  ],
};

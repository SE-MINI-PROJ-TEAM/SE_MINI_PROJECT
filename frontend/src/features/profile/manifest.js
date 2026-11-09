import { lazy } from 'react';
import { UserRound } from 'lucide-react';

// US-03 — Self-service profile contact details
export default {
  id: 'profile',
  routes: [
    {
      path: '/profile',
      roles: ['Student', 'Faculty'],
      component: lazy(() => import('./pages/ProfilePage.jsx')),
      nav: { label: 'My profile', icon: UserRound, section: 'Account', order: 80 },
    },
  ],
};

import { lazy } from 'react';
import { KeyRound } from 'lucide-react';

// US-02 — Mandatory password reset on initial login.
// Rendered outside the app shell (layout: 'bare') and reachable while the temporary-password flag is set.
export default {
  id: 'password-reset',
  routes: [
    {
      path: '/change-password',
      layout: 'bare',
      allowTemp: true,
      component: lazy(() => import('./pages/ChangePasswordPage.jsx')),
      nav: { label: 'Change password', icon: KeyRound, section: 'Account', order: 81 },
    },
  ],
};

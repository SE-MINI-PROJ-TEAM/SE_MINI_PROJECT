import { lazy } from 'react';
import { BookPlus } from 'lucide-react';

// US-05 — Course offering setup & rubric auto-normalisation
export default {
  id: 'course-setup',
  routes: [
    {
      path: '/admin/courses',
      roles: ['Admin'],
      component: lazy(() => import('./pages/CoursesPage.jsx')),
      nav: { label: 'Course offerings', icon: BookPlus, section: 'Administration', order: 20, quick: true },
    },
  ],
};

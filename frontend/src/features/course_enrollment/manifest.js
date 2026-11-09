import { lazy } from 'react';
import { Library } from 'lucide-react';

// US-06 — Student course self-enrollment & capacity cap
export default {
  id: 'course-enrollment',
  routes: [
    {
      path: '/catalog',
      roles: ['Student', 'Admin'],
      component: lazy(() => import('./pages/CatalogPage.jsx')),
      nav: { label: 'Course catalog', icon: Library, section: 'Academics', order: 10, quick: true },
    },
  ],
  slots: {
    'student-dashboard': [{ id: 'my-courses', order: 10, span: 2, component: lazy(() => import('./components/MyCoursesWidget.jsx')) }],
  },
};

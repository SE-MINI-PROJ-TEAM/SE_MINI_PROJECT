import { lazy } from 'react';

// US-15 — Admin metrics overview & one-click CSV export
export default {
  id: 'admin-metrics',
  slots: {
    'admin-dashboard': [{ id: 'metrics', order: 10, span: 2, roles: ['Admin'], component: lazy(() => import('./components/MetricsWidget.jsx')) }],
  },
};

import { download, get } from '../../core/api/client.js';

export const getMetrics = () => get('/admin/metrics');
export const exportCsv = () => download('/admin/metrics/export.csv', 'system-metrics.csv');

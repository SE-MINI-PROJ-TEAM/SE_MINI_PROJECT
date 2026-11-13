import { get } from '../../core/api/client.js';

export const studentSummary = () => get('/analytics/student/summary');
export const facultySections = () => get('/analytics/faculty/sections');

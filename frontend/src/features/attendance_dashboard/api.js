import { get } from '../../core/api/client.js';

export const getSummary = () => get('/attendance/summary');
export const getCourseDetail = (courseId) => get(`/attendance/summary/${courseId}`);

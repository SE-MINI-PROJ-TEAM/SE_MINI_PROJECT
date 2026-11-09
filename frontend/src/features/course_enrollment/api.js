import { get, post, put, qs } from '../../core/api/client.js';

export const getCatalog = (search) => get(`/catalog${qs({ search })}`);
export const enroll = (course_id) => post('/enrollments', { course_id });
export const myEnrollments = () => get('/enrollments/mine');
export const setWindow = (open) => put('/enrollments/window', { open });

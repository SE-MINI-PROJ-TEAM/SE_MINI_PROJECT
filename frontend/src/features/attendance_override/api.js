import { get, put, qs } from '../../core/api/client.js';

export const overrideCourses = () => get('/attendance/override/courses');
export const overrideSessions = (course_id) => get(`/attendance/override/sessions${qs({ course_id })}`);
export const overrideSession = (id) => get(`/attendance/override/sessions/${id}`);
export const saveOverride = (id, changes, reason) => put(`/attendance/override/sessions/${id}`, { changes, reason });

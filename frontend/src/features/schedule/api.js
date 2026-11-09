import { del, get, post, qs } from '../../core/api/client.js';

export const getCalendar = (fromIso, toIso, courseId) => get(`/schedule/calendar${qs({ from: fromIso, to: toIso, course_id: courseId })}`);
export const courseOptions = () => get('/schedule/course-options');
export const createSessions = (payload) => post('/schedule/sessions', payload);
export const listSessions = (params) => get(`/schedule/sessions${qs(params)}`);
export const deleteSession = (id) => del(`/schedule/sessions/${id}`);
export const myCourses = () => get('/schedule/my-courses');
export const getRoster = (courseId) => get(`/schedule/roster/${courseId}`);

import { get, post, put, qs } from '../../core/api/client.js';

export const listCourses = (params) => get(`/courses${qs(params)}`);
export const facultyOptions = () => get('/courses/faculty-options');
export const createCourse = (payload) => post('/courses', payload);
export const updateCourse = (id, payload) => put(`/courses/${id}`, payload);

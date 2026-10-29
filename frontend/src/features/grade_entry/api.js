import { get, put } from '../../core/api/client.js';

export const gradingCourses = () => get('/grades/courses');
export const gradeGrid = (courseId) => get(`/grades/courses/${courseId}`);
export const saveDrafts = (courseId, students) => put(`/grades/courses/${courseId}`, { students });

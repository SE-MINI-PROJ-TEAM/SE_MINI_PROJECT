import { get, post } from '../../core/api/client.js';

export const submitCourse = (courseId) => post(`/grades/courses/${courseId}/submit`);
export const publicationQueue = () => get('/grades/publication/queue');
export const publish = (course_ids) => post('/grades/publication/publish', { course_ids });
export const myGrades = () => get('/grades/mine');

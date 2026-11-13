import { get, post, qs } from '../../core/api/client.js';

export const listSessions = (params = {}) => get(`/attendance/sessions${qs(params)}`);
export const getSession = (id) => get(`/attendance/sessions/${id}`);
export const saveAttendance = (id, attendance_list) => post(`/attendance/sessions/${id}`, { attendance_list });

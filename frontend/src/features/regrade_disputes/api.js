import { get, post, qs } from '../../core/api/client.js';

export const fileDispute = (enrollment_id, reason) => post('/disputes', { enrollment_id, reason });
export const listDisputes = (status) => get(`/disputes${qs({ status })}`);
export const pendingCount = () => get('/disputes/pending-count');
export const resolveDispute = (id, payload) => post(`/disputes/${id}/resolve`, payload);

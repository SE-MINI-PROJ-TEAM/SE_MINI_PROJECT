import { get, patch, qs } from '../../core/api/client.js';

export const listUsers = (params) => get(`/users${qs(params)}`);
export const updateUser = (id, changes) => patch(`/users/${id}`, changes);
export const listAuditLogs = (params) => get(`/admin/audit-logs${qs(params)}`);

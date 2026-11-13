import { post } from '../../core/api/client.js';

export const changePassword = (current_password, new_password) => post('/auth/change-password', { current_password, new_password });

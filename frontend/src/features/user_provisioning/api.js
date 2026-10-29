import { post } from '../../core/api/client.js';

export const createUser = (payload) => post('/users', payload);

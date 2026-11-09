import { get, put } from '../../core/api/client.js';

export const getProfile = () => get('/profile');
export const updateProfile = (payload) => put('/profile', payload);

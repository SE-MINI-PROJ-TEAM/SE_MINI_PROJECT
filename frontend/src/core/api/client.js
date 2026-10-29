const BASE = '/api/v1';

// Error codes meaning "your session is no longer valid" -> the AuthProvider sends the user back to sign-in.
const SESSION_ENDED = new Set(['TOKEN_EXPIRED', 'INVALID_TOKEN', 'ACCOUNT_INACTIVE', 'ROLE_CHANGED', 'UNAUTHORIZED']);
export const SESSION_EVENT = 'srs:session-ended';
export const RESET_EVENT = 'srs:password-reset-required';

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function parse(response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { message: text };
  }
}

async function request(path, { method = 'GET', body, headers } = {}) {
  let response;
  try {
    response = await fetch(BASE + path, {
      method,
      credentials: 'include',
      headers: { Accept: 'application/json', ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}), ...headers },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Cannot reach the server. Check your connection and try again.');
  }
  return response;
}

function fail(response, data) {
  const error = new ApiError(response.status, data.code || 'ERROR', data.message || `Request failed (${response.status})`, data.details);
  if (response.status === 401 && SESSION_ENDED.has(error.code)) window.dispatchEvent(new CustomEvent(SESSION_EVENT, { detail: error }));
  if (response.status === 403 && error.code === 'PASSWORD_RESET_REQUIRED') window.dispatchEvent(new CustomEvent(RESET_EVENT));
  return error;
}

export async function api(path, options) {
  const response = await request(path, options);
  const data = await parse(response);
  if (!response.ok) throw fail(response, data);
  return data;
}

export const get = (path) => api(path);
export const post = (path, body = {}) => api(path, { method: 'POST', body });
export const put = (path, body = {}) => api(path, { method: 'PUT', body });
export const patch = (path, body = {}) => api(path, { method: 'PATCH', body });
export const del = (path) => api(path, { method: 'DELETE' });

/** Download a file endpoint (e.g. CSV) through the authenticated cookie session. */
export async function download(path, fallbackName) {
  const response = await request(path, { headers: { Accept: '*/*' } });
  if (!response.ok) throw fail(response, await parse(response));
  const disposition = response.headers.get('Content-Disposition') || '';
  const name = /filename="?([^";]+)"?/.exec(disposition)?.[1] || fallbackName;
  const url = URL.createObjectURL(await response.blob());
  const link = Object.assign(document.createElement('a'), { href: url, download: name });
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  return name;
}

export const qs = (params) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== null && v !== '' && search.set(k, v));
  const text = search.toString();
  return text ? `?${text}` : '';
};

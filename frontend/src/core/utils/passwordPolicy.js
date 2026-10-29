/** Mirrors backend `validate_password_strength` (core/security.py). The server remains authoritative. */
export const PASSWORD_RULES = [
  { id: 'length', label: 'At least 8 characters', test: (p) => p.length >= 8 },
  { id: 'upper', label: 'One uppercase letter', test: (p) => /[A-Z]/.test(p) },
  { id: 'lower', label: 'One lowercase letter', test: (p) => /[a-z]/.test(p) },
  { id: 'digit', label: 'One digit', test: (p) => /\d/.test(p) },
  { id: 'special', label: 'One special character', test: (p) => /[^A-Za-z0-9]/.test(p) },
];

export const checkPassword = (password) => PASSWORD_RULES.map((rule) => ({ ...rule, ok: rule.test(password) }));
export const isStrongPassword = (password) => PASSWORD_RULES.every((rule) => rule.test(password));

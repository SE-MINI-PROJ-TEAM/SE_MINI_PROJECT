// Mirrors backend core/validation.py so users get instant feedback; the server remains authoritative.
const PHONE = /^\+?[0-9(][0-9 \-()]{5,18}[0-9]$/;
const EMAIL = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$/;

export function validateContact({ phone, personal_email }) {
  const errors = {};
  if (phone.trim() && !PHONE.test(phone.trim())) errors.phone = 'Enter a valid phone number, e.g. +91 98765 43210.';
  if (personal_email.trim() && !EMAIL.test(personal_email.trim())) errors.personal_email = 'Enter a valid email address.';
  return errors;
}

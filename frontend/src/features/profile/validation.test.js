import { describe, expect, it } from 'vitest';
import { validateContact } from './validation.js';

describe('validateContact', () => {
  it('passes valid or empty values', () => {
    expect(validateContact({ phone: '+91 98765 43210', personal_email: 'me@example.com' })).toEqual({});
    expect(validateContact({ phone: '', personal_email: '' })).toEqual({});
  });

  it('flags bad phone numbers and emails', () => {
    expect(validateContact({ phone: 'abc', personal_email: 'nope@' })).toEqual({
      phone: expect.any(String),
      personal_email: expect.any(String),
    });
  });
});

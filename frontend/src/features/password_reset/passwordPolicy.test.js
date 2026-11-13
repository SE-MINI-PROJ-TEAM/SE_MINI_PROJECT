import { describe, expect, it } from 'vitest';
import { checkPassword, isStrongPassword } from '../../core/utils/passwordPolicy.js';

describe('password policy', () => {
  it('accepts a password meeting every rule', () => {
    expect(isStrongPassword('Brand#New9pass')).toBe(true);
  });

  it.each([['short1!A'.slice(0, 5)], ['alllowercase1!'], ['ALLUPPERCASE1!'], ['NoDigits!!!!'], ['NoSpecial1234']])('rejects %s', (pw) => {
    expect(isStrongPassword(pw)).toBe(false);
  });

  it('reports each rule individually', () => {
    const result = Object.fromEntries(checkPassword('abc').map((r) => [r.id, r.ok]));
    expect(result).toEqual({ length: false, upper: false, lower: true, digit: false, special: false });
  });
});

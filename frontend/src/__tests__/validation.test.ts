import { describe, expect, it } from 'vitest';

import { isInstitutionalEmail, passwordError } from '../lib/validation';

describe('isInstitutionalEmail', () => {
  it.each([
    'student@thapar.edu',
    'abc123@thapar.edu',
    'Student@Thapar.Edu',
    '  student@thapar.edu  ',
  ])('accepts %s', (email) => {
    expect(isInstitutionalEmail(email)).toBe(true);
  });

  it.each([
    'student@gmail.com',
    'student@thapar.ac.in',
    'student@thapar.edu.fake.com',
    'student@fakethapar.edu',
    'student@sub.thapar.edu',
    '@thapar.edu',
    'student',
    '',
  ])('rejects %s', (email) => {
    expect(isInstitutionalEmail(email)).toBe(false);
  });
});

describe('passwordError', () => {
  it('accepts a password with a letter and a digit', () => {
    expect(passwordError('CampusGig123')).toBeNull();
  });

  it.each(['short1', 'nodigitshere', '12345678'])('rejects %s', (password) => {
    expect(passwordError(password)).not.toBeNull();
  });
});

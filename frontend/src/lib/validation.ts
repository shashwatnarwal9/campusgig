/**
 * Client-side checks exist only to give fast feedback. The backend re-validates
 * everything and its answer is the one that counts.
 */

export const INSTITUTIONAL_DOMAIN = 'thapar.edu';

/** Mirrors the backend rule: exact whole-domain match, case-insensitive. */
export function isInstitutionalEmail(email: string): boolean {
  const normalised = email.trim().toLowerCase();
  const at = normalised.lastIndexOf('@');
  if (at <= 0) return false;
  const local = normalised.slice(0, at);
  const domain = normalised.slice(at + 1);
  if (!local || local.includes('@')) return false;
  return domain === INSTITUTIONAL_DOMAIN;
}

export function emailError(email: string): string | null {
  if (!email.trim()) return 'Email is required.';
  if (!isInstitutionalEmail(email)) {
    return `Use your institutional email ending in @${INSTITUTIONAL_DOMAIN}.`;
  }
  return null;
}

export function passwordError(password: string): string | null {
  if (password.length < 8) return 'Password must be at least 8 characters.';
  if (new TextEncoder().encode(password).length > 72) {
    return 'Password must be at most 72 bytes.';
  }
  if (!/[a-zA-Z]/.test(password)) return 'Password must contain at least one letter.';
  if (!/\d/.test(password)) return 'Password must contain at least one digit.';
  return null;
}

export function rollNoError(rollNo: string): string | null {
  const value = rollNo.trim();
  if (value.length < 3) return 'Roll number must be at least 3 characters.';
  if (value.length > 32) return 'Roll number is too long.';
  return null;
}

export function deptError(dept: string): string | null {
  const value = dept.trim();
  if (value.length < 2) return 'Department is required.';
  return null;
}

export function batchError(batch: string): string | null {
  const value = Number(batch);
  if (!batch.trim() || Number.isNaN(value)) return 'Batch year is required.';
  if (!Number.isInteger(value) || value < 1900 || value > 2100) {
    return 'Enter a valid batch year.';
  }
  return null;
}

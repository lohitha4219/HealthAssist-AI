export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email || '').trim());
}

export function validateFullName(name) {
  const cleaned = String(name || '').trim().replace(/\s+/g, ' ');
  if (cleaned.length < 2) {
    return 'Full name must be at least 2 characters long';
  }
  if (!/^[A-Za-z][A-Za-z\s'.-]{1,149}$/.test(cleaned)) {
    return 'Full name may contain only letters, spaces, hyphens, apostrophes, and periods';
  }
  return '';
}

export function validatePassword(password) {
  if (!password || password.length < 8) {
    return 'Password must be at least 8 characters long';
  }
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    return 'Password must include at least one letter and one number';
  }
  return '';
}

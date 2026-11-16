import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Loader2, UserPlus } from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { BrandLogo } from '../../components/common/BrandLogo';
import { GlassCard } from '../../components/common/CommonUI';
import { AuthSidePanel } from './AuthIllustration';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { extractApiError } from '../../services/apiClient';
import {
  isValidEmail,
  validateFullName,
  validatePassword,
} from '../../utils/validators';
import './AuthPages.css';

export function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState('');
  const [phone, setPhone] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [serverError, setServerError] = useState('');

  const { register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const validate = () => {
    const errs = {};
    const nameErr = validateFullName(fullName);
    if (nameErr) errs.fullName = nameErr;

    if (!email.trim()) {
      errs.email = 'Email address is required';
    } else if (!isValidEmail(email)) {
      errs.email = 'Please enter a valid email address';
    }

    const pwErr = validatePassword(password);
    if (pwErr) errs.password = pwErr;

    if (!confirmPassword) {
      errs.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      errs.confirmPassword = 'Passwords do not match';
    }

    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setServerError('');
    if (submitting || !validate()) return;

    setSubmitting(true);
    try {
      const res = await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        confirm_password: confirmPassword,
        date_of_birth: dateOfBirth || null,
        gender: gender || null,
        phone: phone.trim() || null,
      });
      showToast(res?.message || 'Registration successful!', 'success');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setServerError(
        extractApiError(err, 'Registration failed. Please check your details.')
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <PublicNavbar />
      <main className="auth-main">
        <div className="auth-split">
          <AuthSidePanel
            title="Start your smarter healthcare journey."
            description="Create your private workspace to organize medical reports, track educational symptom checks, and ask questions with local AI assistance."
          />

          <GlassCard className="auth-card glass-surface--strong animate-fade-up" padding="30px">
            <div className="auth-card__header">
              <div style={{ display: 'inline-flex' }}>
                <BrandLogo size={40} showText={false} />
              </div>
              <h1 className="auth-card__title">Create Your Account</h1>
              <p className="auth-card__subtitle">
                Complete the fields below to set up your account.
              </p>
            </div>

            {serverError && (
              <div className="alert alert--error" role="alert" style={{ marginBottom: 16 }}>
                {serverError}
              </div>
            )}

            <form className="auth-form" onSubmit={handleSubmit} noValidate>
              <div className="field-group">
                <label htmlFor="reg-name" className="field-label">
                  Full Name *
                </label>
                <input
                  id="reg-name"
                  type="text"
                  className="field-input"
                  placeholder="Jane Doe"
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    if (fieldErrors.fullName) setFieldErrors((f) => ({ ...f, fullName: '' }));
                  }}
                  autoComplete="name"
                  aria-invalid={Boolean(fieldErrors.fullName)}
                  required
                />
                {fieldErrors.fullName && (
                  <span className="field-error">{fieldErrors.fullName}</span>
                )}
              </div>

              <div className="field-group">
                <label htmlFor="reg-email" className="field-label">
                  Email Address *
                </label>
                <input
                  id="reg-email"
                  type="email"
                  className="field-input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (fieldErrors.email) setFieldErrors((f) => ({ ...f, email: '' }));
                  }}
                  autoComplete="email"
                  aria-invalid={Boolean(fieldErrors.email)}
                  required
                />
                {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
              </div>

              <div className="auth-two-col">
                <div className="field-group">
                  <label htmlFor="reg-password" className="field-label">
                    Password *
                  </label>
                  <div className="password-input-wrap">
                    <input
                      id="reg-password"
                      type={showPassword ? 'text' : 'password'}
                      className="field-input"
                      placeholder="Min 8 chars, letters & numbers"
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        if (fieldErrors.password) setFieldErrors((f) => ({ ...f, password: '' }));
                      }}
                      autoComplete="new-password"
                      aria-invalid={Boolean(fieldErrors.password)}
                      required
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowPassword((v) => !v)}
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                  {fieldErrors.password && (
                    <span className="field-error">{fieldErrors.password}</span>
                  )}
                </div>

                <div className="field-group">
                  <label htmlFor="reg-confirm" className="field-label">
                    Confirm Password *
                  </label>
                  <div className="password-input-wrap">
                    <input
                      id="reg-confirm"
                      type={showConfirm ? 'text' : 'password'}
                      className="field-input"
                      placeholder="Re-enter your password"
                      value={confirmPassword}
                      onChange={(e) => {
                        setConfirmPassword(e.target.value);
                        if (fieldErrors.confirmPassword) {
                          setFieldErrors((f) => ({ ...f, confirmPassword: '' }));
                        }
                      }}
                      autoComplete="new-password"
                      aria-invalid={Boolean(fieldErrors.confirmPassword)}
                      required
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      aria-label={showConfirm ? 'Hide confirm password' : 'Show confirm password'}
                      onClick={() => setShowConfirm((v) => !v)}
                    >
                      {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                  {fieldErrors.confirmPassword && (
                    <span className="field-error">{fieldErrors.confirmPassword}</span>
                  )}
                </div>
              </div>

              <div className="auth-optional-box">
                <span className="auth-optional-title">Optional Profile Details</span>
                <div className="auth-two-col">
                  <div className="field-group">
                    <label htmlFor="reg-dob" className="field-label">
                      Date of Birth
                    </label>
                    <input
                      id="reg-dob"
                      type="date"
                      className="field-input"
                      value={dateOfBirth}
                      onChange={(e) => setDateOfBirth(e.target.value)}
                    />
                  </div>
                  <div className="field-group">
                    <label htmlFor="reg-gender" className="field-label">
                      Gender
                    </label>
                    <select
                      id="reg-gender"
                      className="field-select"
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                    >
                      <option value="">Prefer not to specify</option>
                      <option value="Female">Female</option>
                      <option value="Male">Male</option>
                      <option value="Non-binary">Non-binary</option>
                      <option value="Prefer not to say">Prefer not to say</option>
                    </select>
                  </div>
                </div>
                <div className="field-group">
                  <label htmlFor="reg-phone" className="field-label">
                    Phone Number
                  </label>
                  <input
                    id="reg-phone"
                    type="tel"
                    className="field-input"
                    placeholder="Optional contact number"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    autoComplete="tel"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn btn--primary btn--lg"
                disabled={submitting}
                style={{ width: '100%', marginTop: 4 }}
              >
                {submitting ? (
                  <>
                    <Loader2 size={18} className="spin" /> Creating Account...
                  </>
                ) : (
                  <>
                    <UserPlus size={18} /> Get Started
                  </>
                )}
              </button>
            </form>

            <div className="auth-footer">
              Already have an account?{' '}
              <Link to="/login" className="auth-link">
                Sign in
              </Link>
            </div>
          </GlassCard>
        </div>
      </main>
    </div>
  );
}

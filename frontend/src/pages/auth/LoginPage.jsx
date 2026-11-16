import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Loader2, LogIn } from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { BrandLogo } from '../../components/common/BrandLogo';
import { GlassCard } from '../../components/common/CommonUI';
import { AuthSidePanel } from './AuthIllustration';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { extractApiError } from '../../services/apiClient';
import { isValidEmail } from '../../utils/validators';
import './AuthPages.css';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [serverError, setServerError] = useState('');

  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTarget = location.state?.from?.pathname || '/dashboard';

  const validate = () => {
    const errs = {};
    if (!email.trim()) {
      errs.email = 'Email address is required';
    } else if (!isValidEmail(email)) {
      errs.email = 'Please enter a valid email address';
    }
    if (!password) {
      errs.password = 'Password is required';
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
      const res = await login({
        email: email.trim(),
        password,
        rememberMe,
      });
      showToast('Welcome back to HealthAssist AI', 'success');
      const roleHome =
        res?.user?.role === 'doctor' ? '/doctor/dashboard' : '/dashboard';
      const target =
        location.state?.from?.pathname && res?.user?.role !== 'doctor'
          ? location.state.from.pathname
          : roleHome;
      navigate(target, { replace: true });
    } catch (err) {
      setServerError(
        extractApiError(err, 'Unable to sign in. Please verify your credentials.')
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
            title="AI-Powered Healthcare Assistant"
            description="Your intelligent companion for better health awareness and personalized healthcare guidance."
          />

          <GlassCard className="auth-card glass-surface--strong animate-fade-up" padding="32px">
            <div className="auth-card__header">
              <div style={{ display: 'inline-flex' }}>
                <BrandLogo size={40} showText={false} />
              </div>
              <h1 className="auth-card__title">Welcome Back</h1>
              <p className="auth-card__subtitle">
                Sign in to access your personal health workspace.
              </p>
            </div>

            {serverError && (
              <div className="alert alert--error" role="alert" style={{ marginBottom: 16 }}>
                {serverError}
              </div>
            )}

            <form className="auth-form" onSubmit={handleSubmit} noValidate>
              <div className="field-group">
                <label htmlFor="login-email" className="field-label">
                  Email Address
                </label>
                <input
                  id="login-email"
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

              <div className="field-group">
                <div className="auth-row-between">
                  <label htmlFor="login-password" className="field-label">
                    Password
                  </label>
                  <Link to="/forgot-password" className="auth-link">
                    Forgot password?
                  </Link>
                </div>
                <div className="password-input-wrap">
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    className="field-input"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (fieldErrors.password) setFieldErrors((f) => ({ ...f, password: '' }));
                    }}
                    autoComplete="current-password"
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

              <div className="auth-row-between">
                <label className="remember-check">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  <span>Remember me on this device</span>
                </label>
              </div>

              <button
                type="submit"
                className="btn btn--primary btn--lg"
                disabled={submitting}
                style={{ width: '100%', marginTop: 4 }}
              >
                {submitting ? (
                  <>
                    <Loader2 size={18} className="spin" /> Signing In...
                  </>
                ) : (
                  <>
                    <LogIn size={18} /> Sign In
                  </>
                )}
              </button>
            </form>

            <div className="auth-footer">
              New to HealthAssist AI?{' '}
              <Link to="/register" className="auth-link">
                Create an account
              </Link>
            </div>
          </GlassCard>
        </div>
      </main>
    </div>
  );
}

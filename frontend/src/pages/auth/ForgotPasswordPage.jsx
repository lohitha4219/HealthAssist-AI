import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { KeyRound, Loader2, ArrowLeft } from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { GlassCard } from '../../components/common/CommonUI';
import { BrandLogo } from '../../components/common/BrandLogo';
import { authService } from '../../services/authService';
import { extractApiError } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import { isValidEmail, validatePassword } from '../../utils/validators';
import './AuthPages.css';

export function ForgotPasswordPage() {
  const [step, setStep] = useState('request'); // request | reset
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [infoMessage, setInfoMessage] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setError('');
    setInfoMessage('');
    if (!isValidEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }
    setSubmitting(true);
    try {
      const res = await authService.forgotPassword(email.trim());
      setInfoMessage(res.message);
      if (res.dev_reset_token) {
        setToken(res.dev_reset_token);
      }
      setStep('reset');
    } catch (err) {
      setError(extractApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCompleteReset = async (e) => {
    e.preventDefault();
    setError('');
    if (!token.trim()) {
      setError('Please enter your password reset token');
      return;
    }
    const pwErr = validatePassword(newPassword);
    if (pwErr) {
      setError(pwErr);
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setSubmitting(true);
    try {
      const res = await authService.resetPassword({
        token: token.trim(),
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      showToast(res.message, 'success');
      navigate('/login');
    } catch (err) {
      setError(extractApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <PublicNavbar />
      <main className="auth-main">
        <GlassCard className="auth-card glass-surface--strong animate-fade-up" padding="32px">
          <div className="auth-card__header">
            <div style={{ display: 'inline-flex', marginBottom: 12 }}>
              <BrandLogo size={40} showText={false} />
            </div>
            <h1 className="auth-card__title">
              {step === 'request' ? 'Reset Password' : 'Enter New Password'}
            </h1>
            <p className="auth-card__subtitle">
              {step === 'request'
                ? 'Request a secure single-use password reset token.'
                : 'Apply your reset token and choose a new password.'}
            </p>
          </div>

          {infoMessage && (
            <div className="alert alert--info" style={{ marginBottom: 16 }}>
              {infoMessage}
            </div>
          )}
          {error && (
            <div className="alert alert--error" role="alert" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          {step === 'request' ? (
            <form className="auth-form" onSubmit={handleRequestReset}>
              <div className="field-group">
                <label htmlFor="forgot-email" className="field-label">
                  Account Email
                </label>
                <input
                  id="forgot-email"
                  type="email"
                  className="field-input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <button
                type="submit"
                className="btn btn--primary btn--lg"
                disabled={submitting}
              >
                {submitting ? (
                  <>
                    <Loader2 size={18} className="spin" /> Generating Token...
                  </>
                ) : (
                  <>
                    <KeyRound size={18} /> Request Reset Token
                  </>
                )}
              </button>
            </form>
          ) : (
            <form className="auth-form" onSubmit={handleCompleteReset}>
              <div className="field-group">
                <label htmlFor="reset-token" className="field-label">
                  Reset Token
                </label>
                <input
                  id="reset-token"
                  type="text"
                  className="field-input"
                  placeholder="Paste your reset token"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                />
              </div>
              <div className="field-group">
                <label htmlFor="reset-pw" className="field-label">
                  New Password
                </label>
                <input
                  id="reset-pw"
                  type="password"
                  className="field-input"
                  placeholder="Min 8 chars, letters & numbers"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
              </div>
              <div className="field-group">
                <label htmlFor="reset-confirm" className="field-label">
                  Confirm New Password
                </label>
                <input
                  id="reset-confirm"
                  type="password"
                  className="field-input"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
              <button
                type="submit"
                className="btn btn--primary btn--lg"
                disabled={submitting}
              >
                {submitting ? 'Updating...' : 'Reset Password'}
              </button>
            </form>
          )}

          <div className="auth-footer">
            <Link to="/login" className="auth-link" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <ArrowLeft size={15} /> Back to Login
            </Link>
          </div>
        </GlassCard>
      </main>
    </div>
  );
}

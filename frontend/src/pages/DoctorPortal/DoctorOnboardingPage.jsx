import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, ShieldCheck, Stethoscope } from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { GlassCard } from '../../components/common/CommonUI';
import { AuthSidePanel } from '../auth/AuthIllustration';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { extractApiError } from '../../services/apiClient';
import '../auth/AuthPages.css';

export function DoctorOnboardingPage() {
  const [form, setForm] = useState({
    invitation_token: '',
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
    phone: '',
    qualification: '',
    specialization: '',
    experience_years: 1,
    license_number: '',
    languages: 'English, Telugu',
    consultation_fee: '',
    bio: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const { doctorRegister } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match');
      return;
    }
    setSubmitting(true);
    try {
      await doctorRegister({
        invitation_token: form.invitation_token.trim(),
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
        confirm_password: form.confirm_password,
        phone: form.phone.trim() || null,
        qualification: form.qualification.trim(),
        specialization: form.specialization.trim(),
        experience_years: Number(form.experience_years),
        license_number: form.license_number.trim(),
        languages: form.languages
          .split(',')
          .map((l) => l.trim())
          .filter(Boolean),
        consultation_fee: form.consultation_fee ? Number(form.consultation_fee) : null,
        bio: form.bio.trim() || null,
      });
      showToast('Doctor onboarding completed!', 'success');
      navigate('/doctor/dashboard', { replace: true });
    } catch (err) {
      setError(extractApiError(err, 'Doctor onboarding failed'));
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
            title="Verified Doctor Onboarding"
            description="Doctor accounts require a single-use verification invitation token and valid medical license registration."
          />

          <GlassCard className="auth-card glass-surface--strong animate-fade-up" padding="30px">
            <div className="auth-card__header">
              <span className="badge badge--primary">
                <ShieldCheck size={14} /> Invitation Required
              </span>
              <h1 className="auth-card__title">Doctor Registration</h1>
              <p className="auth-card__subtitle">
                Enter your invitation token and medical credentials to activate your Doctor Portal.
              </p>
            </div>

            {error && (
              <div className="alert alert--error" role="alert" style={{ marginBottom: 14 }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="field-group">
                <label htmlFor="doc-token" className="field-label">
                  Invitation Token *
                </label>
                <input
                  id="doc-token"
                  type="text"
                  className="field-input"
                  value={form.invitation_token}
                  onChange={(e) => setForm((f) => ({ ...f, invitation_token: e.target.value }))}
                  required
                />
              </div>

              <div className="auth-two-col">
                <div className="field-group">
                  <label htmlFor="doc-name" className="field-label">
                    Full Name *
                  </label>
                  <input
                    id="doc-name"
                    type="text"
                    className="field-input"
                    placeholder="Dr. Priya Rao"
                    value={form.full_name}
                    onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                    required
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="doc-email" className="field-label">
                    Invited Email *
                  </label>
                  <input
                    id="doc-email"
                    type="email"
                    className="field-input"
                    value={form.email}
                    onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <div className="auth-two-col">
                <div className="field-group">
                  <label htmlFor="doc-pw" className="field-label">
                    Password *
                  </label>
                  <input
                    id="doc-pw"
                    type="password"
                    className="field-input"
                    value={form.password}
                    onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                    required
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="doc-cpw" className="field-label">
                    Confirm Password *
                  </label>
                  <input
                    id="doc-cpw"
                    type="password"
                    className="field-input"
                    value={form.confirm_password}
                    onChange={(e) => setForm((f) => ({ ...f, confirm_password: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <div className="auth-two-col">
                <div className="field-group">
                  <label htmlFor="doc-qual" className="field-label">
                    Qualification *
                  </label>
                  <input
                    id="doc-qual"
                    type="text"
                    className="field-input"
                    placeholder="MBBS, MD"
                    value={form.qualification}
                    onChange={(e) => setForm((f) => ({ ...f, qualification: e.target.value }))}
                    required
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="doc-spec" className="field-label">
                    Specialization *
                  </label>
                  <input
                    id="doc-spec"
                    type="text"
                    className="field-input"
                    placeholder="Cardiology"
                    value={form.specialization}
                    onChange={(e) => setForm((f) => ({ ...f, specialization: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <div className="auth-two-col">
                <div className="field-group">
                  <label htmlFor="doc-lic" className="field-label">
                    Medical License Number *
                  </label>
                  <input
                    id="doc-lic"
                    type="text"
                    className="field-input"
                    value={form.license_number}
                    onChange={(e) => setForm((f) => ({ ...f, license_number: e.target.value }))}
                    required
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="doc-exp" className="field-label">
                    Experience (Years) *
                  </label>
                  <input
                    id="doc-exp"
                    type="number"
                    min={0}
                    max={70}
                    className="field-input"
                    value={form.experience_years}
                    onChange={(e) => setForm((f) => ({ ...f, experience_years: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <button type="submit" className="btn btn--primary btn--lg" disabled={submitting}>
                {submitting ? (
                  <>
                    <Loader2 size={17} className="spin" /> Activating Doctor Portal...
                  </>
                ) : (
                  <>
                    <Stethoscope size={17} /> Complete Doctor Onboarding
                  </>
                )}
              </button>
            </form>

            <div className="auth-footer">
              Patient registration?{' '}
              <Link to="/register" className="auth-link">
                Create Patient Account
              </Link>
            </div>
          </GlassCard>
        </div>
      </main>
    </div>
  );
}

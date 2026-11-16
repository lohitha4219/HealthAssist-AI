import { useEffect, useState } from 'react';
import { KeyRound, Loader2, Save, ShieldCheck, User } from 'lucide-react';
import { healthService } from '../../services/healthService';
import { extractApiError } from '../../services/apiClient';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { GlassCard, LoadingSpinner, PageHeader } from '../../components/common/CommonUI';
import { formatDate } from '../../utils/formatters';
import { isValidEmail, validatePassword } from '../../utils/validators';
import './ProfilePage.css';

const BLOOD_GROUPS = ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const GENDERS = ['', 'Female', 'Male', 'Non-binary', 'Prefer not to say'];

export function ProfilePage() {
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    date_of_birth: '',
    gender: '',
    phone: '',
    blood_group: '',
    height_cm: '',
    weight_kg: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    allergies: '',
    chronic_conditions: '',
    bio: '',
  });
  const [accountMeta, setAccountMeta] = useState({ created_at: '', role: 'user' });
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);

  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [savingPw, setSavingPw] = useState(false);

  const { updateUserLocal } = useAuth();
  const { showToast } = useToast();

  useEffect(() => {
    let active = true;
    async function loadProfile() {
      setLoading(true);
      try {
        const data = await healthService.getProfile();
        if (!active) return;
        setForm({
          full_name: data.full_name || '',
          email: data.email || '',
          date_of_birth: data.date_of_birth || '',
          gender: data.gender || '',
          phone: data.phone || '',
          blood_group: data.blood_group || '',
          height_cm: data.height_cm ?? '',
          weight_kg: data.weight_kg ?? '',
          emergency_contact_name: data.emergency_contact_name || '',
          emergency_contact_phone: data.emergency_contact_phone || '',
          allergies: data.allergies || '',
          chronic_conditions: data.chronic_conditions || '',
          bio: data.bio || '',
        });
        setAccountMeta({ created_at: data.created_at, role: data.role });
      } catch (err) {
        if (active) showToast(extractApiError(err, 'Failed to load profile'), 'error');
      } finally {
        if (active) setLoading(false);
      }
    }
    loadProfile();
    return () => {
      active = false;
    };
  }, []);

  const handleFieldChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    if (form.full_name.trim().length < 2) {
      showToast('Full name must be at least 2 characters', 'error');
      return;
    }
    if (!isValidEmail(form.email)) {
      showToast('Please enter a valid email address', 'error');
      return;
    }

    setSavingProfile(true);
    try {
      const payload = {
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        date_of_birth: form.date_of_birth || null,
        gender: form.gender || null,
        phone: form.phone.trim() || null,
        blood_group: form.blood_group || null,
        height_cm: form.height_cm === '' ? null : Number(form.height_cm),
        weight_kg: form.weight_kg === '' ? null : Number(form.weight_kg),
        emergency_contact_name: form.emergency_contact_name.trim() || null,
        emergency_contact_phone: form.emergency_contact_phone.trim() || null,
        allergies: form.allergies.trim() || null,
        chronic_conditions: form.chronic_conditions.trim() || null,
        bio: form.bio.trim() || null,
      };
      const updated = await healthService.updateProfile(payload);
      updateUserLocal({
        id: updated.id,
        full_name: updated.full_name,
        email: updated.email,
        role: updated.role,
        is_active: updated.is_active,
        date_of_birth: updated.date_of_birth,
        gender: updated.gender,
        blood_group: updated.blood_group,
        created_at: updated.created_at,
      });
      showToast('Profile saved to PostgreSQL', 'success');
    } catch (err) {
      showToast(extractApiError(err, 'Unable to update profile'), 'error');
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    const pwErr = validatePassword(passwords.new_password);
    if (pwErr) {
      showToast(pwErr, 'error');
      return;
    }
    if (passwords.new_password !== passwords.confirm_password) {
      showToast('New passwords do not match', 'error');
      return;
    }
    setSavingPw(true);
    try {
      const res = await healthService.changePassword(passwords);
      setPasswords({ current_password: '', new_password: '', confirm_password: '' });
      showToast(res.message, 'success');
    } catch (err) {
      showToast(extractApiError(err, 'Failed to update password'), 'error');
    } finally {
      setSavingPw(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading your profile..." />;
  }

  return (
    <div className="profile-page animate-fade-up">
      <PageHeader
        badge={
          <span className="badge badge--primary">
            <ShieldCheck size={14} /> Member Since {formatDate(accountMeta.created_at)}
          </span>
        }
        title="Personal Profile"
        subtitle="Manage your personal details, health reference fields, and account password security."
      />

      <div className="profile-grid">
        {/* Profile Details Form */}
        <GlassCard>
          <h2 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <User size={19} color="var(--color-primary)" /> Personal & Health Information
          </h2>

          <form onSubmit={handleProfileSave} className="profile-form">
            <div className="profile-two-col">
              <div className="field-group">
                <label htmlFor="prof-name" className="field-label">
                  Full Name
                </label>
                <input
                  id="prof-name"
                  type="text"
                  className="field-input"
                  value={form.full_name}
                  onChange={(e) => handleFieldChange('full_name', e.target.value)}
                  required
                />
              </div>

              <div className="field-group">
                <label htmlFor="prof-email" className="field-label">
                  Email Address
                </label>
                <input
                  id="prof-email"
                  type="email"
                  className="field-input"
                  value={form.email}
                  onChange={(e) => handleFieldChange('email', e.target.value)}
                  required
                />
              </div>

              <div className="field-group">
                <label htmlFor="prof-dob" className="field-label">
                  Date of Birth
                </label>
                <input
                  id="prof-dob"
                  type="date"
                  className="field-input"
                  value={form.date_of_birth}
                  onChange={(e) => handleFieldChange('date_of_birth', e.target.value)}
                />
              </div>

              <div className="field-group">
                <label htmlFor="prof-gender" className="field-label">
                  Gender
                </label>
                <select
                  id="prof-gender"
                  className="field-select"
                  value={form.gender}
                  onChange={(e) => handleFieldChange('gender', e.target.value)}
                >
                  {GENDERS.map((g) => (
                    <option key={g} value={g}>
                      {g || 'Select'}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field-group">
                <label htmlFor="prof-phone" className="field-label">
                  Phone Number
                </label>
                <input
                  id="prof-phone"
                  type="text"
                  className="field-input"
                  placeholder="Optional"
                  value={form.phone}
                  onChange={(e) => handleFieldChange('phone', e.target.value)}
                />
              </div>

              <div className="field-group">
                <label htmlFor="prof-blood" className="field-label">
                  Blood Group
                </label>
                <select
                  id="prof-blood"
                  className="field-select"
                  value={form.blood_group}
                  onChange={(e) => handleFieldChange('blood_group', e.target.value)}
                >
                  {BLOOD_GROUPS.map((bg) => (
                    <option key={bg} value={bg}>
                      {bg || 'Not specified'}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field-group">
                <label htmlFor="prof-height" className="field-label">
                  Height (cm)
                </label>
                <input
                  id="prof-height"
                  type="number"
                  step="0.1"
                  min="40"
                  max="270"
                  className="field-input"
                  value={form.height_cm}
                  onChange={(e) => handleFieldChange('height_cm', e.target.value)}
                />
              </div>

              <div className="field-group">
                <label htmlFor="prof-weight" className="field-label">
                  Weight (kg)
                </label>
                <input
                  id="prof-weight"
                  type="number"
                  step="0.1"
                  min="10"
                  max="400"
                  className="field-input"
                  value={form.weight_kg}
                  onChange={(e) => handleFieldChange('weight_kg', e.target.value)}
                />
              </div>

              <div className="field-group">
                <label htmlFor="prof-em-name" className="field-label">
                  Emergency Contact Name
                </label>
                <input
                  id="prof-em-name"
                  type="text"
                  className="field-input"
                  value={form.emergency_contact_name}
                  onChange={(e) => handleFieldChange('emergency_contact_name', e.target.value)}
                />
              </div>

              <div className="field-group">
                <label htmlFor="prof-em-phone" className="field-label">
                  Emergency Contact Phone
                </label>
                <input
                  id="prof-em-phone"
                  type="text"
                  className="field-input"
                  value={form.emergency_contact_phone}
                  onChange={(e) => handleFieldChange('emergency_contact_phone', e.target.value)}
                />
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="prof-allergies" className="field-label">
                Known Allergies
              </label>
              <textarea
                id="prof-allergies"
                rows={2}
                className="field-textarea"
                placeholder="Medications, foods, or environmental allergies..."
                value={form.allergies}
                onChange={(e) => handleFieldChange('allergies', e.target.value)}
              />
            </div>

            <div className="field-group">
              <label htmlFor="prof-conditions" className="field-label">
                Ongoing Health Notes / Conditions
              </label>
              <textarea
                id="prof-conditions"
                rows={2}
                className="field-textarea"
                placeholder="Personal health notes for quick reference..."
                value={form.chronic_conditions}
                onChange={(e) => handleFieldChange('chronic_conditions', e.target.value)}
              />
            </div>

            <div className="field-group">
              <label htmlFor="prof-bio" className="field-label">
                Personal Summary / Bio
              </label>
              <textarea
                id="prof-bio"
                rows={2}
                className="field-textarea"
                value={form.bio}
                onChange={(e) => handleFieldChange('bio', e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn--primary"
              disabled={savingProfile}
              style={{ alignSelf: 'flex-start' }}
            >
              {savingProfile ? (
                <>
                  <Loader2 size={17} className="spin" /> Saving Profile...
                </>
              ) : (
                <>
                  <Save size={17} /> Save Profile Changes
                </>
              )}
            </button>
          </form>
        </GlassCard>

        {/* Change Password Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <GlassCard>
            <h2 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <KeyRound size={19} color="var(--color-accent)" /> Change Password
            </h2>

            <form onSubmit={handlePasswordSubmit} className="profile-form">
              <div className="field-group">
                <label htmlFor="pw-current" className="field-label">
                  Current Password
                </label>
                <input
                  id="pw-current"
                  type="password"
                  className="field-input"
                  value={passwords.current_password}
                  onChange={(e) =>
                    setPasswords((p) => ({ ...p, current_password: e.target.value }))
                  }
                  required
                />
              </div>

              <div className="field-group">
                <label htmlFor="pw-new" className="field-label">
                  New Password
                </label>
                <input
                  id="pw-new"
                  type="password"
                  className="field-input"
                  placeholder="Min 8 chars with letters & numbers"
                  value={passwords.new_password}
                  onChange={(e) =>
                    setPasswords((p) => ({ ...p, new_password: e.target.value }))
                  }
                  required
                />
              </div>

              <div className="field-group">
                <label htmlFor="pw-confirm" className="field-label">
                  Confirm New Password
                </label>
                <input
                  id="pw-confirm"
                  type="password"
                  className="field-input"
                  value={passwords.confirm_password}
                  onChange={(e) =>
                    setPasswords((p) => ({ ...p, confirm_password: e.target.value }))
                  }
                  required
                />
              </div>

              <button type="submit" className="btn btn--accent" disabled={savingPw}>
                {savingPw ? 'Updating Password...' : 'Update Password'}
              </button>
            </form>
          </GlassCard>

          <GlassCard>
            <h3 style={{ margin: '0 0 8px', color: 'var(--color-primary-deep)' }}>
              Account Overview
            </h3>
            <p style={{ margin: '0 0 6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              <strong>Role:</strong> {accountMeta.role}
            </p>
            <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              <strong>Created:</strong> {formatDate(accountMeta.created_at)}
            </p>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}

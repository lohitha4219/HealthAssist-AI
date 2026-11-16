import { useEffect, useState } from 'react';
import { Save, ShieldCheck } from 'lucide-react';
import { healthcareService } from '../../services/healthcareService';
import { extractApiError } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import { GlassCard, LoadingSpinner, PageHeader } from '../../components/common/CommonUI';

export function DoctorProfilePage() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({
    full_name: '',
    languages: '',
    consultation_fee: '',
    bio: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    healthcareService
      .getDoctorOwnProfile()
      .then((d) => {
        setProfile(d);
        setForm({
          full_name: d.full_name || '',
          languages: (d.languages || []).join(', '),
          consultation_fee: d.consultation_fee ?? '',
          bio: d.bio || '',
        });
      })
      .catch((err) => showToast(extractApiError(err), 'error'))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await healthcareService.updateDoctorOwnProfile({
        full_name: form.full_name.trim(),
        languages: form.languages
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        consultation_fee:
          form.consultation_fee === '' ? null : Number(form.consultation_fee),
        bio: form.bio.trim() || null,
      });
      setProfile(updated);
      showToast('Doctor profile updated', 'success');
    } catch (err) {
      showToast(extractApiError(err, 'Failed to update profile'), 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner label="Loading doctor profile..." />;
  if (!profile) return null;

  return (
    <div className="animate-fade-up">
      <PageHeader
        badge={
          <span className="badge badge--success">
            <ShieldCheck size={14} /> {profile.verification_status}
          </span>
        }
        title="Doctor Profile"
        subtitle="Update permitted profile details. Verified credentials and license number are protected."
      />

      <div className="profile-grid">
        <GlassCard>
          <form onSubmit={handleSubmit} className="profile-form">
            <div className="field-group">
              <label htmlFor="dp-name" className="field-label">
                Full Name
              </label>
              <input
                id="dp-name"
                type="text"
                className="field-input"
                value={form.full_name}
                onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                required
              />
            </div>

            <div className="auth-two-col">
              <div className="field-group">
                <label htmlFor="dp-lang" className="field-label">
                  Languages (comma-separated)
                </label>
                <input
                  id="dp-lang"
                  type="text"
                  className="field-input"
                  value={form.languages}
                  onChange={(e) => setForm((f) => ({ ...f, languages: e.target.value }))}
                />
              </div>

              <div className="field-group">
                <label htmlFor="dp-fee" className="field-label">
                  Consultation Fee (₹)
                </label>
                <input
                  id="dp-fee"
                  type="number"
                  min={0}
                  className="field-input"
                  value={form.consultation_fee}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, consultation_fee: e.target.value }))
                  }
                />
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="dp-bio" className="field-label">
                Professional Biography
              </label>
              <textarea
                id="dp-bio"
                rows={4}
                className="field-textarea"
                value={form.bio}
                onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
              />
            </div>

            <button type="submit" className="btn btn--primary" disabled={saving}>
              <Save size={16} /> {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </GlassCard>

        <GlassCard>
          <h2 className="dash-card-title">Verified Credentials (Protected)</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.9rem' }}>
            <div>
              <strong>Qualification:</strong> {profile.qualification}
            </div>
            <div>
              <strong>Specialization:</strong> {profile.specialization}
            </div>
            <div>
              <strong>Experience:</strong> {profile.experience_years} years
            </div>
            <div>
              <strong>License Number:</strong> {profile.license_number || 'On file'}
            </div>
            <div>
              <strong>Hospital Affiliation:</strong>{' '}
              {profile.hospital_name || 'Unassigned'}
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

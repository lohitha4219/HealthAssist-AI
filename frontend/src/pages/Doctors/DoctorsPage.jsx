import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Building2, Search, Stethoscope, UserCheck } from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { Footer } from '../../components/layout/Footer';
import {
  EmptyState,
  GlassCard,
  LoadingSpinner,
  PageHeader,
} from '../../components/common/CommonUI';
import { healthcareService } from '../../services/healthcareService';
import { extractApiError } from '../../services/apiClient';
import { useAuth } from '../../context/AuthContext';
import '../Hospitals/DirectoryPages.css';

export function DoctorsPage() {
  const { isAuthenticated } = useAuth();
  const [filters, setFilters] = useState({ districts: [], cities: [], specialties: [] });
  const [search, setSearch] = useState('');
  const [specialization, setSpecialization] = useState('all');
  const [district, setDistrict] = useState('all');
  const [availableDate, setAvailableDate] = useState('');
  const [availableTime, setAvailableTime] = useState('');

  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    healthcareService
      .getHospitalFilters()
      .then(setFilters)
      .catch(() => {});
  }, []);

  const loadDoctors = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await healthcareService.listDoctors({
        search: search.trim() || undefined,
        specialization: specialization !== 'all' ? specialization : undefined,
        district: district !== 'all' ? district : undefined,
        available_date: availableDate || undefined,
        available_time: availableTime || undefined,
      });
      setDoctors(res.items);
    } catch (err) {
      setError(extractApiError(err, 'Failed to load verified doctors'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDoctors();
  }, [specialization, district, availableDate, availableTime]);

  const body = (
    <div className="animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--cyan">Verified Medical Directory</span>}
        title="Find Verified Doctors"
        subtitle="Search verified physicians by name, specialization, hospital, district, and live date/time slot availability."
        actions={
          <Link to="/doctor-onboarding" className="btn btn--glass btn--sm">
            Doctor Onboarding
          </Link>
        }
      />

      <GlassCard style={{ marginBottom: 20 }}>
        <form
          className="dir-filter-grid"
          onSubmit={(e) => {
            e.preventDefault();
            loadDoctors();
          }}
        >
          <div className="symptom-search-wrap">
            <Search size={16} className="symptom-search-icon" />
            <input
              type="text"
              className="field-input symptom-search-input"
              placeholder="Search doctor, specialty, hospital..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="field-select"
            aria-label="Filter by specialty"
            value={specialization}
            onChange={(e) => setSpecialization(e.target.value)}
          >
            <option value="all">All Specialties</option>
            {filters.specialties.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>

          <select
            className="field-select"
            aria-label="Filter by district"
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
          >
            <option value="all">All Districts</option>
            {filters.districts.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          <input
            type="date"
            className="field-input"
            aria-label="Available date"
            value={availableDate}
            onChange={(e) => setAvailableDate(e.target.value)}
          />

          <input
            type="time"
            className="field-input"
            aria-label="Available time"
            value={availableTime}
            onChange={(e) => setAvailableTime(e.target.value)}
          />
        </form>
      </GlassCard>

      {error && (
        <div className="alert alert--error" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      {loading ? (
        <LoadingSpinner label="Loading verified doctors..." />
      ) : doctors.length === 0 ? (
        <EmptyState
          icon={UserCheck}
          title="No verified doctors available"
          description={
            search.trim() || specialization !== 'all' || district !== 'all' || availableDate || availableTime
              ? 'No verified doctors match the selected search, specialty, district, or availability. Try clearing some filters.'
              : 'No verified doctor profiles have been onboarded yet. Only doctors who complete the secure invitation and verification process appear here; sample profiles are not generated.'
          }
          action={
            <Link to="/hospitals" className="btn btn--primary btn--sm">
              Browse Hospitals
            </Link>
          }
        />
      ) : (
        <div className="dir-cards-grid">
          {doctors.map((doc) => (
            <GlassCard key={doc.id} interactive className="dir-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                <span className="badge badge--primary">{doc.specialization}</span>
                <span className="badge badge--success">Verified</span>
              </div>
              <h2 className="dir-card__title">{doc.full_name}</h2>
              {doc.designation && (
                <div style={{ fontSize: '0.84rem', color: 'var(--color-primary-light)', marginBottom: 6 }}>
                  {doc.designation}
                </div>
              )}
              <div className="dir-card__meta">
                <Stethoscope size={15} />
                <span>
                  {doc.qualification}
                  {doc.experience_years ? ` · ${doc.experience_years} yrs experience` : ''}
                </span>
              </div>
              {doc.hospital_name && (
                <div className="dir-card__meta">
                  <Building2 size={15} />
                  <span>
                    {doc.hospital_name} ({doc.hospital_city})
                  </span>
                </div>
              )}
              <div className="dir-chip-row">
                {doc.languages.map((l) => (
                  <span key={l} className="badge badge--cyan">
                    {l}
                  </span>
                ))}
                {doc.consultation_fee != null && (
                  <span className="badge badge--accent">Fee: ₹{doc.consultation_fee}</span>
                )}
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 'auto', paddingTop: 8 }}>
                {doc.hospital_id && (
                  <Link
                    to={`/hospitals/${doc.hospital_id}`}
                    className="btn btn--glass btn--sm"
                    style={{ flex: 1, textAlign: 'center' }}
                  >
                    View Hospital
                  </Link>
                )}
                <Link
                  to={`/doctors/${doc.id}`}
                  className="btn btn--primary btn--sm"
                  style={{ flex: 1, textAlign: 'center' }}
                >
                  Book Appointment
                </Link>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );

  if (isAuthenticated) {
    return body;
  }

  return (
    <div className="dir-page">
      <PublicNavbar />
      <main className="dir-main">
        <div className="container">{body}</div>
      </main>
      <Footer />
    </div>
  );
}

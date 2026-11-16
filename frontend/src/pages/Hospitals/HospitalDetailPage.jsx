import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Building2,
  Clock,
  ExternalLink,
  MapPin,
  Phone,
  ShieldAlert,
  Stethoscope,
} from 'lucide-react';
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
import './DirectoryPages.css';

export function HospitalDetailPage() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const [hospital, setHospital] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    healthcareService
      .getHospitalDetail(id)
      .then((data) => {
        if (active) setHospital(data);
      })
      .catch((err) => {
        if (active) setError(extractApiError(err, 'Hospital not found'));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id]);

  const body = loading ? (
    <LoadingSpinner label="Loading hospital profile..." />
  ) : error || !hospital ? (
    <GlassCard>
      <div className="alert alert--error" style={{ marginBottom: 14 }}>
        {error || 'Hospital not found'}
      </div>
      <Link to="/hospitals" className="btn btn--primary">
        <ArrowLeft size={16} /> Back to Hospitals
      </Link>
    </GlassCard>
  ) : (
    <div className="animate-fade-up">
      <div style={{ marginBottom: 14 }}>
        <Link to="/hospitals" className="btn btn--glass btn--sm">
          <ArrowLeft size={15} /> All Hospitals
        </Link>
      </div>

      <PageHeader
        badge={
          <span className="badge badge--success">
            {hospital.verification_status} · {hospital.district}, {hospital.state}
          </span>
        }
        title={hospital.name}
        subtitle={`${hospital.hospital_type} · ${hospital.city}`}
        actions={
          <>
            {hospital.website && (
              <a
                href={hospital.website}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn--glass btn--sm"
              >
                Official Website <ExternalLink size={15} />
              </a>
            )}
            <Link to={`/appointments?hospitalId=${hospital.id}`} className="btn btn--primary btn--sm">
              Book Appointment
            </Link>
          </>
        }
      />

      <div className="dir-detail-grid">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <GlassCard>
            <h2 className="dash-card-title">Verified Contact &amp; Hours</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div className="dir-card__meta">
                <MapPin size={17} color="var(--color-primary)" />
                <span>
                  {hospital.address}
                  {hospital.pincode ? ` - ${hospital.pincode}` : ''}
                </span>
              </div>
              {hospital.phone && (
                <div className="dir-card__meta">
                  <Phone size={17} color="var(--color-primary)" />
                  <span>Phone: {hospital.phone}</span>
                </div>
              )}
              {hospital.emergency_phone && (
                <div className="dir-card__meta">
                  <ShieldAlert size={17} color="var(--color-accent)" />
                  <span>Emergency: {hospital.emergency_phone}</span>
                </div>
              )}
              {hospital.operating_hours && (
                <div className="dir-card__meta">
                  <Clock size={17} color="var(--color-secondary)" />
                  <span>{hospital.operating_hours}</span>
                </div>
              )}
              {hospital.emergency_info && (
                <div className="alert alert--info" style={{ marginTop: 6 }}>
                  {hospital.emergency_info}
                </div>
              )}
              {hospital.source_reference && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Source reference: {hospital.source_reference}
                </div>
              )}
            </div>
          </GlassCard>

          <GlassCard>
            <h2 className="dash-card-title">
              Departments ({hospital.departments.length})
            </h2>
            <div className="dir-chip-row">
              {hospital.departments.map((d) => (
                <span key={d.id} className="badge badge--primary">
                  {d.name}
                </span>
              ))}
            </div>
          </GlassCard>

          <GlassCard>
            <h2 className="dash-card-title">
              Verified Treatments ({hospital.treatments.length})
            </h2>
            {hospital.treatments.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', margin: 0 }}>
                No verified specialty treatments published for this hospital yet.
              </p>
            ) : (
              <div className="dash-record-list">
                {hospital.treatments.map((t) => (
                  <div key={t.id} className="dash-record-row">
                    <div>
                      <div className="dash-record-row__title">{t.name}</div>
                      {t.description && (
                        <div className="dash-record-row__meta">{t.description}</div>
                      )}
                    </div>
                    <span className="badge badge--cyan">{t.specialty}</span>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <GlassCard>
            <h2 className="dash-card-title">
              Facilities ({hospital.facilities.length})
            </h2>
            <div className="dir-chip-row">
              {hospital.facilities.map((f) => (
                <span key={f.id} className="badge badge--cyan">
                  {f.name}
                </span>
              ))}
            </div>
          </GlassCard>

          <GlassCard>
            <h2 className="dash-card-title">
              Affiliated Verified Doctors ({hospital.doctors.length})
            </h2>
            {hospital.doctors.length === 0 ? (
              <EmptyState
                icon={Stethoscope}
                title="No doctors onboarded at this hospital yet"
                description="Verified doctors affiliated with this hospital will appear here automatically once onboarded."
              />
            ) : (
              <div className="dash-record-list">
                {hospital.doctors.map((doc) => (
                  <div key={doc.id} className="dash-record-row">
                    <div>
                      <div className="dash-record-row__title">{doc.full_name}</div>
                      <div className="dash-record-row__meta">
                        {doc.specialization} · {doc.qualification}
                      </div>
                    </div>
                    <Link to={`/doctors/${doc.id}`} className="btn btn--primary btn--sm">
                      Book
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>
      </div>
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

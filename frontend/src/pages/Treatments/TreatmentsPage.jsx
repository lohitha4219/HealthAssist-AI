import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Building2, CheckCircle2, HeartPulse, ShieldAlert } from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { Footer } from '../../components/layout/Footer';
import { EmptyState, GlassCard, LoadingSpinner, PageHeader } from '../../components/common/CommonUI';
import { healthcareService } from '../../services/healthcareService';
import { extractApiError } from '../../services/apiClient';
import { useAuth } from '../../context/AuthContext';
import './TreatmentsPage.css';

export function TreatmentsPage() {
  const { isAuthenticated } = useAuth();
  const [items, setItems] = useState([]);
  const [activeSlug, setActiveSlug] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    healthcareService
      .listTreatments()
      .then((data) => {
        if (active) {
          setItems(data);
          if (data.length > 0) setActiveSlug(data[0].slug);
        }
      })
      .catch((err) => {
        if (active) setError(extractApiError(err, 'Unable to load treatment guides'));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const current = items.find((i) => i.slug === activeSlug) || items[0];

  const body = (
    <div className="animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--accent">Educational Specialty Library</span>}
        title="Treatment Information & Precautions"
        subtitle="Explore specialty overviews, consultation preparation, general precautions, aftercare education, and emergency warning signs."
      />

      {error && <div className="alert alert--error">{error}</div>}

      {loading ? (
        <LoadingSpinner label="Loading specialty guides..." />
      ) : (
        <div className="treatments-layout">
          {items.length === 0 ? (
            <EmptyState
              icon={HeartPulse}
              title="No treatment guides published yet"
              description="The treatment library is connected to the live database, but no reviewed education guides have been published yet. Only reviewed content is displayed here; sample medical content is not generated."
            />
          ) : (
          <>
          <GlassCard padding="14px" className="treatments-nav">
            {items.map((item) => (
              <button
                key={item.slug}
                type="button"
                className={`treatments-nav__btn ${
                  item.slug === current?.slug ? 'is-active' : ''
                }`}
                onClick={() => setActiveSlug(item.slug)}
              >
                <HeartPulse size={16} />
                <span>{item.specialty}</span>
              </button>
            ))}
          </GlassCard>

          {current && (
            <GlassCard className="glass-surface--strong">
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
                <span className="badge badge--primary">{current.specialty}</span>
                <span className="badge badge--cyan">
                  Last Reviewed: {current.last_reviewed_date}
                </span>
              </div>

              <h2 className="result-title">{current.specialty} Overview</h2>
              <p className="result-summary">{current.description}</p>

              <div className="treatments-sections">
                <div>
                  <h3>Common Reasons for Consultation</h3>
                  <ul>
                    {current.common_reasons.map((x, idx) => (
                      <li key={idx}><CheckCircle2 size={15} /> {x}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3>General Preparation</h3>
                  <ul>
                    {current.preparation.map((x, idx) => (
                      <li key={idx}><CheckCircle2 size={15} /> {x}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3>General Precautions</h3>
                  <ul>
                    {current.precautions.map((x, idx) => (
                      <li key={idx}><ShieldAlert size={15} color="var(--color-warning)" /> {x}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3>General Aftercare Education</h3>
                  <ul>
                    {current.aftercare.map((x, idx) => (
                      <li key={idx}><CheckCircle2 size={15} /> {x}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="alert alert--info" style={{ marginTop: 16 }}>
                <div>
                  <strong>When to Consult a Doctor:</strong>{' '}
                  {current.when_to_consult.join(' · ')}
                </div>
              </div>

              <div className="alert alert--error" style={{ marginTop: 12 }}>
                <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Emergency Warning Signs:</strong>{' '}
                  {current.emergency_signs.join(' · ')}
                </div>
              </div>

              {current.verified_hospitals?.length > 0 && (
                <div style={{ marginTop: 18 }}>
                  <h3 style={{ margin: '0 0 10px', fontSize: '0.96rem', color: 'var(--color-primary-deep)' }}>
                    Verified Hospitals Offering {current.specialty}
                  </h3>
                  <div className="dir-chip-row">
                    {current.verified_hospitals.map((vh) => (
                      <Link
                        key={`${vh.hospital_id}-${vh.treatment_name}`}
                        to={`/hospitals/${vh.hospital_id}`}
                        className="btn btn--glass btn--sm"
                      >
                        <Building2 size={14} /> {vh.hospital_name} ({vh.city})
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              <p className="result-disclaimer">
                Sources: {current.sources.join(', ')} · Reviewed by:{' '}
                {current.reviewed_by || 'Clinical Education Reference Library'}. Educational
                content only; does not diagnose conditions or prescribe treatment.
              </p>
            </GlassCard>
          )}
          </>
          )}
        </div>
      )}
    </div>
  );

  if (isAuthenticated) return body;

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

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Building2, Clock, ExternalLink, MapPin, Phone, Search } from 'lucide-react';
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

export function HospitalsPage({ embedded = false }) {
  const { isAuthenticated } = useAuth();
  const [filters, setFilters] = useState({
    districts: [],
    cities: [],
    specialties: [],
    facilities: [],
  });
  const [search, setSearch] = useState('');
  const [district, setDistrict] = useState('all');
  const [city, setCity] = useState('all');
  const [specialization, setSpecialization] = useState('all');
  const [facility, setFacility] = useState('all');
  const [page, setPage] = useState(1);

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pageSize = 9;

  useEffect(() => {
    healthcareService
      .getHospitalFilters()
      .then(setFilters)
      .catch(() => {});
  }, []);

  const loadHospitals = async (targetPage = page) => {
    setLoading(true);
    setError('');
    try {
      const res = await healthcareService.listHospitals({
        search: search.trim() || undefined,
        district: district !== 'all' ? district : undefined,
        city: city !== 'all' ? city : undefined,
        specialization: specialization !== 'all' ? specialization : undefined,
        facility: facility !== 'all' ? facility : undefined,
        page: targetPage,
        page_size: pageSize,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      setError(extractApiError(err, 'Unable to load hospitals'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHospitals(page);
  }, [page, district, city, specialization, facility]);

  const content = (
    <div className="animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--primary">Andhra Pradesh Directory</span>}
        title="Verified Hospitals"
        subtitle="Search verified hospitals across Andhra Pradesh by district, city, specialization, treatment, or facility."
      />

      <GlassCard style={{ marginBottom: 20 }}>
        <form
          className="dir-filter-grid"
          onSubmit={(e) => {
            e.preventDefault();
            setPage(1);
            loadHospitals(1);
          }}
        >
          <div className="symptom-search-wrap">
            <Search size={16} className="symptom-search-icon" />
            <input
              type="text"
              className="field-input symptom-search-input"
              placeholder="Search hospital name or city..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="field-select"
            aria-label="Filter by district"
            value={district}
            onChange={(e) => {
              setPage(1);
              setDistrict(e.target.value);
            }}
          >
            <option value="all">All Districts</option>
            {filters.districts.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          <select
            className="field-select"
            aria-label="Filter by city"
            value={city}
            onChange={(e) => {
              setPage(1);
              setCity(e.target.value);
            }}
          >
            <option value="all">All Cities</option>
            {filters.cities.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <select
            className="field-select"
            aria-label="Filter by specialization"
            value={specialization}
            onChange={(e) => {
              setPage(1);
              setSpecialization(e.target.value);
            }}
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
            aria-label="Filter by facility"
            value={facility}
            onChange={(e) => {
              setPage(1);
              setFacility(e.target.value);
            }}
          >
            <option value="all">All Facilities</option>
            {filters.facilities.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        </form>
      </GlassCard>

      {error && (
        <div className="alert alert--error" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      {loading ? (
        <LoadingSpinner label="Loading verified hospitals..." />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No hospitals available"
          description={
            search.trim() || district !== 'all' || city !== 'all' || specialization !== 'all' || facility !== 'all'
              ? 'No published hospitals match the selected filters. Try clearing your search and filters.'
              : 'No hospitals have been published in the directory yet. Only real records added through the secure hospital-maintenance workflow appear here; sample listings are not generated.'
          }
        />
      ) : (
        <>
          <div className="dir-cards-grid">
            {items.map((h) => (
              <GlassCard key={h.id} interactive className="dir-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <span className="badge badge--cyan">{h.district}</span>
                  <span className="badge badge--success">{h.verification_status}</span>
                </div>
                <h2 className="dir-card__title">{h.name}</h2>
                <div className="dir-card__meta">
                  <Building2 size={15} style={{ flexShrink: 0, marginTop: 2 }} />
                  <span>{h.hospital_type}</span>
                </div>
                <div className="dir-card__meta">
                  <MapPin size={15} style={{ flexShrink: 0, marginTop: 2 }} />
                  <span>
                    {h.address} ({h.city}, {h.district})
                  </span>
                </div>
                {h.phone && (
                  <div className="dir-card__meta">
                    <Phone size={15} style={{ flexShrink: 0, marginTop: 2 }} />
                    <span>{h.phone}</span>
                  </div>
                )}
                {h.operating_hours && (
                  <div className="dir-card__meta">
                    <Clock size={15} style={{ flexShrink: 0, marginTop: 2 }} />
                    <span>{h.operating_hours}</span>
                  </div>
                )}

                <div className="dir-chip-row" style={{ marginTop: 'auto', paddingTop: 8 }}>
                  <span className="badge badge--primary">{h.department_count} Departments</span>
                  <span className="badge badge--cyan">{h.treatment_count} Treatments</span>
                  <span className="badge badge--accent">{h.doctor_count} Doctors</span>
                </div>

                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <Link to={`/hospitals/${h.id}`} className="btn btn--primary btn--sm" style={{ flex: 1 }}>
                    View Hospital Profile
                  </Link>
                  {h.website && (
                    <a
                      href={h.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn--glass btn--sm"
                      aria-label={`Official website for ${h.name}`}
                    >
                      <ExternalLink size={15} />
                    </a>
                  )}
                </div>
              </GlassCard>
            ))}
          </div>

          {Math.ceil(total / pageSize) > 1 && (
            <div className="pagination-row" style={{ marginTop: 24 }}>
              <button
                type="button"
                className="btn btn--glass btn--sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span>
                Page {page} of {Math.ceil(total / pageSize)} ({total} hospitals)
              </span>
              <button
                type="button"
                className="btn btn--glass btn--sm"
                disabled={page >= Math.ceil(total / pageSize)}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );

  if (embedded || isAuthenticated) {
    return content;
  }

  return (
    <div className="dir-page">
      <PublicNavbar />
      <main className="dir-main">
        <div className="container">{content}</div>
      </main>
      <Footer />
    </div>
  );
}

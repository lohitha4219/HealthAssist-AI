import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Building2,
  CalendarCheck,
  Clock,
  Loader2,
  Stethoscope,
} from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { Footer } from '../../components/layout/Footer';
import { GlassCard, LoadingSpinner, PageHeader } from '../../components/common/CommonUI';
import { healthcareService } from '../../services/healthcareService';
import { extractApiError } from '../../services/apiClient';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import '../Hospitals/DirectoryPages.css';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export function DoctorDetailPage() {
  const { id } = useParams();
  const { isAuthenticated, user } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [doctor, setDoctor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const todayStr = new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState(todayStr);
  const [slotsData, setSlotsData] = useState(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState('');
  const [reason, setReason] = useState('');
  const [shareReports, setShareReports] = useState(false);
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    healthcareService
      .getDoctorDetail(id)
      .then((d) => {
        if (active) setDoctor(d);
      })
      .catch((err) => {
        if (active) setError(extractApiError(err, 'Doctor not found'));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id]);

  const fetchSlots = async (dateStr) => {
    if (!id || !dateStr) return;
    setLoadingSlots(true);
    setSelectedSlot('');
    try {
      const res = await healthcareService.getDoctorSlots(id, dateStr);
      setSlotsData(res);
    } catch {
      setSlotsData(null);
    } finally {
      setLoadingSlots(false);
    }
  };

  useEffect(() => {
    if (doctor) fetchSlots(selectedDate);
  }, [doctor, selectedDate]);

  const handleBook = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    if (user?.role !== 'patient') {
      showToast('Only patient accounts can book appointments', 'error');
      return;
    }
    if (!selectedSlot) {
      showToast('Please select an available time slot', 'warning');
      return;
    }
    if (reason.trim().length < 5) {
      showToast('Please describe your reason for consultation (min 5 characters)', 'warning');
      return;
    }

    setBooking(true);
    try {
      await healthcareService.bookAppointment({
        doctor_id: doctor.id,
        hospital_id: doctor.hospital_id,
        appointment_date: selectedDate,
        appointment_time: `${selectedSlot}:00`,
        reason: reason.trim(),
        share_reports: shareReports,
      });
      showToast('Appointment booked successfully!', 'success');
      navigate('/appointments');
    } catch (err) {
      showToast(extractApiError(err, 'Failed to book appointment'), 'error');
      fetchSlots(selectedDate);
    } finally {
      setBooking(false);
    }
  };

  const body = loading ? (
    <LoadingSpinner label="Loading doctor profile..." />
  ) : error || !doctor ? (
    <GlassCard>
      <div className="alert alert--error" style={{ marginBottom: 14 }}>
        {error || 'Doctor not found'}
      </div>
      <Link to="/doctors" className="btn btn--primary">
        <ArrowLeft size={16} /> Back to Doctors
      </Link>
    </GlassCard>
  ) : (
    <div className="animate-fade-up">
      <div style={{ marginBottom: 14 }}>
        <Link to="/doctors" className="btn btn--glass btn--sm">
          <ArrowLeft size={15} /> All Doctors
        </Link>
      </div>

      <PageHeader
        badge={<span className="badge badge--success">Verified · {doctor.specialization}</span>}
        title={doctor.full_name}
        subtitle={`${doctor.designation ? `${doctor.designation} · ` : ''}${doctor.qualification}${doctor.experience_years ? ` · ${doctor.experience_years} years experience` : ''}`}
      />

      <div className="dir-detail-grid">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <GlassCard>
            <h2 className="dash-card-title">Doctor &amp; Hospital Affiliation</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {doctor.designation && (
                <div style={{ fontSize: '0.92rem', color: 'var(--color-primary-light)', fontWeight: 500 }}>
                  {doctor.designation}
                </div>
              )}
              <div className="dir-card__meta">
                <Stethoscope size={17} color="var(--color-primary)" />
                <span>
                  Specialization: <strong>{doctor.specialization}</strong>
                </span>
              </div>
              {doctor.hospital_name && (
                <div className="dir-card__meta">
                  <Building2 size={17} color="var(--color-primary)" />
                  <span>
                    Affiliated Hospital:{' '}
                    <Link to={`/hospitals/${doctor.hospital_id}`} className="auth-link">
                      <strong>{doctor.hospital_name}</strong>
                    </Link>{' '}
                    ({doctor.hospital_city})
                  </span>
                </div>
              )}
              {doctor.hospital_phone && (
                <div className="dir-card__meta">
                  <Clock size={16} color="var(--color-primary)" />
                  <span>Official Hospital Phone: <strong>{doctor.hospital_phone}</strong></span>
                </div>
              )}
              {doctor.published_timings && (
                <div className="dir-card__meta">
                  <Clock size={16} color="var(--color-cyan)" />
                  <span>Published OPD Hours: <strong>{doctor.published_timings}</strong></span>
                </div>
              )}
              {doctor.official_source_url && (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  Verified Profile Source:{' '}
                  <a
                    href={doctor.official_source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="auth-link"
                  >
                    {doctor.official_source_url}
                  </a>
                </div>
              )}
              {doctor.bio && <p style={{ margin: '6px 0 0', color: 'var(--text-secondary)' }}>{doctor.bio}</p>}
              <div className="dir-chip-row">
                {doctor.languages.map((l) => (
                  <span key={l} className="badge badge--cyan">
                    {l}
                  </span>
                ))}
                {doctor.consultation_fee != null && (
                  <span className="badge badge--accent">Fee: ₹{doctor.consultation_fee}</span>
                )}
              </div>
            </div>
          </GlassCard>

          <GlassCard>
            <h2 className="dash-card-title">Weekly Consultation Schedule</h2>
            {doctor.availability.length === 0 ? (
              <p style={{ margin: 0, color: 'var(--text-muted)' }}>
                This doctor has not published weekly consultation hours yet.
              </p>
            ) : (
              <div className="dash-record-list">
                {doctor.availability.map((rule) => (
                  <div key={rule.id} className="dash-record-row">
                    <strong>{DAYS[rule.day_of_week]}</strong>
                    <span>
                      <Clock size={14} style={{ display: 'inline', marginRight: 5 }} />
                      {rule.start_time.slice(0, 5)} – {rule.end_time.slice(0, 5)} ({rule.slot_duration_minutes}m slots)
                    </span>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>

        <GlassCard className="glass-surface--strong">
          <h2 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <CalendarCheck size={19} color="var(--color-primary)" /> Book Appointment
          </h2>

          <form onSubmit={handleBook} className="auth-form">
            <div className="field-group">
              <label htmlFor="slot-date" className="field-label">
                Select Date
              </label>
              <input
                id="slot-date"
                type="date"
                min={todayStr}
                className="field-input"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
              />
            </div>

            <div className="field-group">
              <span className="field-label">Available Time Slots</span>
              {loadingSlots ? (
                <LoadingSpinner label="Checking live slots..." />
              ) : slotsData?.unavailable_reason ? (
                <div className="alert alert--info">{slotsData.unavailable_reason}</div>
              ) : slotsData?.slots?.length > 0 ? (
                <div className="slots-grid">
                  {slotsData.slots.map((slot) => (
                    <button
                      key={slot.time}
                      type="button"
                      disabled={!slot.available}
                      className={`slot-btn ${selectedSlot === slot.time ? 'is-selected' : ''}`}
                      onClick={() => setSelectedSlot(slot.time)}
                    >
                      {slot.display_time}
                    </button>
                  ))}
                </div>
              ) : (
                <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                  No slots configured for this date.
                </p>
              )}
            </div>

            <div className="field-group">
              <label htmlFor="appt-reason" className="field-label">
                Reason for Consultation
              </label>
              <textarea
                id="appt-reason"
                rows={3}
                className="field-textarea"
                placeholder="Describe symptoms or consultation topic..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                required
              />
            </div>

            <label className="remember-check">
              <input
                type="checkbox"
                checked={shareReports}
                onChange={(e) => setShareReports(e.target.checked)}
              />
              <span>Authorize this doctor to view my uploaded medical reports</span>
            </label>

            <button
              type="submit"
              className="btn btn--primary btn--lg"
              disabled={booking || !doctor.hospital_id}
            >
              {booking ? (
                <>
                  <Loader2 size={17} className="spin" /> Booking...
                </>
              ) : isAuthenticated ? (
                'Confirm Appointment'
              ) : (
                'Sign In to Book Appointment'
              )}
            </button>
          </form>
        </GlassCard>
      </div>
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

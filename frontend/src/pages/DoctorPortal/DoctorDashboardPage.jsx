import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CalendarCheck,
  CalendarClock,
  CheckCircle2,
  Clock,
  RefreshCw,
  ShieldCheck,
  Users,
  XCircle,
} from 'lucide-react';
import { healthcareService } from '../../services/healthcareService';
import { extractApiError } from '../../services/apiClient';
import {
  EmptyState,
  GlassCard,
  LoadingSpinner,
  PageHeader,
} from '../../components/common/CommonUI';

export function DoctorDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await healthcareService.getDoctorDashboard();
      setData(res);
    } catch (err) {
      setError(extractApiError(err, 'Failed to load doctor dashboard'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  if (loading) return <LoadingSpinner label="Loading Doctor Portal dashboard..." />;
  if (error) {
    return (
      <GlassCard>
        <div className="alert alert--error" style={{ marginBottom: 14 }}>
          {error}
        </div>
        <button type="button" className="btn btn--primary" onClick={loadDashboard}>
          <RefreshCw size={15} /> Retry
        </button>
      </GlassCard>
    );
  }

  const { doctor, stats, recent_appointments } = data;

  return (
    <div className="animate-fade-up">
      <PageHeader
        badge={
          <span className="badge badge--success">
            <ShieldCheck size={14} /> {doctor.verification_status} · {doctor.specialization}
          </span>
        }
        title={`Welcome, ${doctor.full_name}`}
        subtitle={`${doctor.qualification}${doctor.hospital_name ? ` · ${doctor.hospital_name}` : ''}`}
        actions={
          <>
            <Link to="/doctor/appointments" className="btn btn--primary btn--sm">
              Manage Appointments
            </Link>
            <Link to="/doctor/availability" className="btn btn--glass btn--sm">
              Configure Schedule
            </Link>
          </>
        }
      />

      <div className="dash-stats-grid">
        <GlassCard interactive className="dash-stat-card">
          <div className="dash-stat-card__icon dash-stat-card__icon--blue">
            <Clock size={22} />
          </div>
          <div>
            <div className="dash-stat-card__value">{stats.today_appointments}</div>
            <div className="dash-stat-card__label">Today&apos;s Appointments</div>
          </div>
        </GlassCard>

        <GlassCard interactive className="dash-stat-card">
          <div className="dash-stat-card__icon dash-stat-card__icon--cyan">
            <CalendarClock size={22} />
          </div>
          <div>
            <div className="dash-stat-card__value">{stats.upcoming_appointments}</div>
            <div className="dash-stat-card__label">Upcoming Appointments</div>
          </div>
        </GlassCard>

        <GlassCard interactive className="dash-stat-card">
          <div className="dash-stat-card__icon dash-stat-card__icon--red">
            <CalendarCheck size={22} />
          </div>
          <div>
            <div className="dash-stat-card__value">{stats.pending_requests}</div>
            <div className="dash-stat-card__label">Pending Requests</div>
          </div>
        </GlassCard>

        <GlassCard interactive className="dash-stat-card">
          <div className="dash-stat-card__icon dash-stat-card__icon--indigo">
            <Users size={22} />
          </div>
          <div>
            <div className="dash-stat-card__value">{stats.patient_count}</div>
            <div className="dash-stat-card__label">Patients Served</div>
          </div>
        </GlassCard>
      </div>

      <div className="insights-summary-row" style={{ marginBottom: 22 }}>
        <GlassCard>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <CheckCircle2 size={20} color="var(--color-success)" />
            <div>
              <div className="dash-stat-card__value">{stats.confirmed_appointments}</div>
              <div className="dash-stat-card__label">Confirmed</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <CheckCircle2 size={20} color="var(--color-primary)" />
            <div>
              <div className="dash-stat-card__value">{stats.completed_appointments}</div>
              <div className="dash-stat-card__label">Completed</div>
            </div>
          </div>
        </GlassCard>
        <GlassCard>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <XCircle size={20} color="var(--color-danger)" />
            <div>
              <div className="dash-stat-card__value">{stats.cancelled_appointments}</div>
              <div className="dash-stat-card__label">Cancelled / Declined</div>
            </div>
          </div>
        </GlassCard>
      </div>

      <GlassCard>
        <div className="dash-card-head">
          <h2 className="dash-card-title">Upcoming &amp; Recent Appointments</h2>
          <Link to="/doctor/appointments" className="auth-link">
            Open All
          </Link>
        </div>

        {recent_appointments.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title="No appointments scheduled yet"
            description="Configure your weekly working hours in Availability & Leave so patients can book slots with you."
            action={
              <Link to="/doctor/availability" className="btn btn--primary btn--sm">
                Set Weekly Availability
              </Link>
            }
          />
        ) : (
          <div className="dash-record-list">
            {recent_appointments.map((a) => (
              <div key={a.id} className="dash-record-row">
                <div>
                  <div className="dash-record-row__title">
                    {a.patient_name} · {a.appointment_date} at {a.appointment_time.slice(0, 5)}
                  </div>
                  <div className="dash-record-row__meta">{a.reason}</div>
                </div>
                <span className="badge badge--primary">{a.status}</span>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  );
}

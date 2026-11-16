import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  CalendarCheck,
  CalendarClock,
  CheckCircle2,
  FileText,
  Loader2,
  XCircle,
} from 'lucide-react';
import { healthcareService } from '../../services/healthcareService';
import { extractApiError } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import {
  EmptyState,
  GlassCard,
  LoadingSpinner,
  Modal,
  PageHeader,
} from '../../components/common/CommonUI';

const STATUS_BADGES = {
  pending: 'badge--warning',
  confirmed: 'badge--success',
  rescheduled: 'badge--cyan',
  completed: 'badge--primary',
  cancelled: 'badge--danger',
  rejected: 'badge--danger',
};

export function AppointmentsPage() {
  const [searchParams] = useSearchParams();
  const initialHospitalId = searchParams.get('hospitalId') || '';

  const [hospitals, setHospitals] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [selectedHospitalId, setSelectedHospitalId] = useState(initialHospitalId);
  const [selectedDoctorId, setSelectedDoctorId] = useState('');

  const todayStr = new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState(todayStr);
  const [slotsData, setSlotsData] = useState(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState('');
  const [reason, setReason] = useState('');
  const [shareReports, setShareReports] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [appointments, setAppointments] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [loadingAppts, setLoadingAppts] = useState(true);

  const [cancelTarget, setCancelTarget] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  const [rescheduleTarget, setRescheduleTarget] = useState(null);
  const [rescheduleDate, setRescheduleDate] = useState(todayStr);
  const [rescheduleSlots, setRescheduleSlots] = useState(null);
  const [rescheduleTime, setRescheduleTime] = useState('');
  const [notesTarget, setNotesTarget] = useState(null);

  const { showToast } = useToast();

  const loadAppointments = async (filter = statusFilter) => {
    setLoadingAppts(true);
    try {
      const data = await healthcareService.listMyAppointments(filter);
      setAppointments(data);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to load appointments'), 'error');
    } finally {
      setLoadingAppts(false);
    }
  };

  useEffect(() => {
    healthcareService
      .listHospitals({ page: 1, page_size: 50 })
      .then((res) => setHospitals(res.items || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadAppointments(statusFilter);
  }, [statusFilter]);

  useEffect(() => {
    if (!selectedHospitalId) {
      setDoctors([]);
      setSelectedDoctorId('');
      return;
    }
    healthcareService
      .listDoctors({ hospital_id: Number(selectedHospitalId), page: 1, page_size: 50 })
      .then((res) => setDoctors(res.items || []))
      .catch(() => setDoctors([]));
  }, [selectedHospitalId]);

  useEffect(() => {
    if (!selectedDoctorId || !selectedDate) {
      setSlotsData(null);
      setSelectedSlot('');
      return;
    }
    setLoadingSlots(true);
    setSelectedSlot('');
    healthcareService
      .getDoctorSlots(selectedDoctorId, selectedDate)
      .then(setSlotsData)
      .catch(() => setSlotsData(null))
      .finally(() => setLoadingSlots(false));
  }, [selectedDoctorId, selectedDate]);

  useEffect(() => {
    if (!rescheduleTarget || !rescheduleDate) return;
    setRescheduleTime('');
    healthcareService
      .getDoctorSlots(rescheduleTarget.doctor_id, rescheduleDate)
      .then(setRescheduleSlots)
      .catch(() => setRescheduleSlots(null));
  }, [rescheduleTarget, rescheduleDate]);

  const handleBook = async (e) => {
    e.preventDefault();
    if (!selectedHospitalId || !selectedDoctorId || !selectedSlot) {
      showToast('Select a hospital, verified doctor, date, and open slot', 'warning');
      return;
    }
    if (reason.trim().length < 5) {
      showToast('Please enter a consultation reason (min 5 characters)', 'warning');
      return;
    }
    setSubmitting(true);
    try {
      await healthcareService.bookAppointment({
        hospital_id: Number(selectedHospitalId),
        doctor_id: Number(selectedDoctorId),
        appointment_date: selectedDate,
        appointment_time: `${selectedSlot}:00`,
        reason: reason.trim(),
        share_reports: shareReports,
      });
      showToast('Appointment booked successfully!', 'success');
      setReason('');
      setSelectedSlot('');
      loadAppointments(statusFilter);
      const updatedSlots = await healthcareService.getDoctorSlots(selectedDoctorId, selectedDate);
      setSlotsData(updatedSlots);
    } catch (err) {
      showToast(extractApiError(err, 'Unable to book appointment'), 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelSubmit = async (e) => {
    e.preventDefault();
    if (!cancelTarget || cancelReason.trim().length < 3) {
      showToast('Please enter a cancellation reason', 'warning');
      return;
    }
    try {
      await healthcareService.cancelAppointment(cancelTarget.id, cancelReason.trim());
      showToast('Appointment cancelled', 'info');
      setCancelTarget(null);
      setCancelReason('');
      loadAppointments(statusFilter);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to cancel appointment'), 'error');
    }
  };

  const handleRescheduleSubmit = async (e) => {
    e.preventDefault();
    if (!rescheduleTarget || !rescheduleTime) {
      showToast('Please choose an available reschedule slot', 'warning');
      return;
    }
    try {
      await healthcareService.rescheduleAppointment(rescheduleTarget.id, {
        appointment_date: rescheduleDate,
        appointment_time: `${rescheduleTime}:00`,
      });
      showToast('Appointment rescheduled', 'success');
      setRescheduleTarget(null);
      loadAppointments(statusFilter);
    } catch (err) {
      showToast(extractApiError(err, 'Unable to reschedule appointment'), 'error');
    }
  };

  return (
    <div className="animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--primary">Hospital &amp; Doctor Scheduling</span>}
        title="Appointments"
        subtitle="Book real available slots with verified hospital doctors, reschedule, cancel, and read shareable consultation notes."
      />

      <div className="dir-detail-grid" style={{ marginBottom: 24 }}>
        <GlassCard className="glass-surface--strong">
          <h2 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <CalendarCheck size={19} color="var(--color-primary)" /> Book New Appointment
          </h2>

          <form onSubmit={handleBook} className="auth-form">
            <div className="field-group">
              <label htmlFor="bk-hospital" className="field-label">
                1. Select Hospital
              </label>
              <select
                id="bk-hospital"
                className="field-select"
                value={selectedHospitalId}
                onChange={(e) => setSelectedHospitalId(e.target.value)}
              >
                <option value="">Choose a verified hospital...</option>
                {hospitals.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.name} ({h.city}, {h.district})
                  </option>
                ))}
              </select>
            </div>

            <div className="field-group">
              <label htmlFor="bk-doctor" className="field-label">
                2. Select Verified Doctor
              </label>
              <select
                id="bk-doctor"
                className="field-select"
                value={selectedDoctorId}
                onChange={(e) => setSelectedDoctorId(e.target.value)}
                disabled={!selectedHospitalId}
              >
                <option value="">
                  {selectedHospitalId
                    ? doctors.length > 0
                      ? 'Choose a verified doctor...'
                      : 'No verified doctors onboarded at this hospital yet'
                    : 'Select a hospital first'}
                </option>
                {doctors.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.full_name} — {d.specialization}
                  </option>
                ))}
              </select>
            </div>

            <div className="field-group">
              <label htmlFor="bk-date" className="field-label">
                3. Select Date
              </label>
              <input
                id="bk-date"
                type="date"
                min={todayStr}
                className="field-input"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                disabled={!selectedDoctorId}
              />
            </div>

            {selectedDoctorId && (
              <div className="field-group">
                <span className="field-label">4. Available Time Slots</span>
                {loadingSlots ? (
                  <LoadingSpinner label="Checking doctor schedule..." />
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
                ) : null}
              </div>
            )}

            <div className="field-group">
              <label htmlFor="bk-reason" className="field-label">
                5. Reason for Consultation
              </label>
              <textarea
                id="bk-reason"
                rows={3}
                className="field-textarea"
                placeholder="Describe symptoms or follow-up details..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </div>

            <label className="remember-check">
              <input
                type="checkbox"
                checked={shareReports}
                onChange={(e) => setShareReports(e.target.checked)}
              />
              <span>Allow this doctor to view my uploaded medical reports</span>
            </label>

            <button
              type="submit"
              className="btn btn--primary"
              disabled={submitting || !selectedSlot}
            >
              {submitting ? (
                <>
                  <Loader2 size={16} className="spin" /> Booking Appointment...
                </>
              ) : (
                'Confirm Appointment'
              )}
            </button>
          </form>
        </GlassCard>

        {/* My Appointments */}
        <GlassCard>
          <div className="dash-card-head">
            <h2 className="dash-card-title">My Appointments</h2>
            <select
              className="field-select"
              style={{ width: 'auto' }}
              aria-label="Filter appointments by status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="rescheduled">Rescheduled</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          {loadingAppts ? (
            <LoadingSpinner label="Loading your appointments..." />
          ) : appointments.length === 0 ? (
            <EmptyState
              icon={CalendarClock}
              title="No appointments yet"
              description="Select a hospital and verified doctor on the left or browse the Doctor Directory."
              action={
                <Link to="/doctors" className="btn btn--glass btn--sm">
                  Browse Doctors
                </Link>
              }
            />
          ) : (
            <div className="dash-record-list">
              {appointments.map((appt) => {
                const canModify = ['pending', 'confirmed', 'rescheduled'].includes(appt.status);
                return (
                  <div key={appt.id} className="symptom-history-item glass-surface--subtle">
                    <div className="symptom-history-main">
                      <div className="symptom-history-top">
                        <strong>{appt.doctor_name}</strong>
                        <span className={`badge ${STATUS_BADGES[appt.status] || 'badge--primary'}`}>
                          {appt.status}
                        </span>
                      </div>
                      <div className="symptom-history-meta">
                        {appt.hospital_name} · {appt.appointment_date} at{' '}
                        {appt.appointment_time.slice(0, 5)}
                      </div>
                      <div style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', marginTop: 4 }}>
                        {appt.reason}
                      </div>
                      {appt.cancellation_reason && (
                        <div style={{ fontSize: '0.82rem', color: 'var(--color-danger)', marginTop: 4 }}>
                          Note: {appt.cancellation_reason}
                        </div>
                      )}
                    </div>

                    <div className="symptom-history-actions" style={{ flexWrap: 'wrap' }}>
                      {appt.consultation_notes?.length > 0 && (
                        <button
                          type="button"
                          className="btn btn--glass btn--sm"
                          onClick={() => setNotesTarget(appt)}
                        >
                          <FileText size={14} /> Notes ({appt.consultation_notes.length})
                        </button>
                      )}
                      {canModify && (
                        <>
                          <button
                            type="button"
                            className="btn btn--glass btn--sm"
                            onClick={() => {
                              setRescheduleTarget(appt);
                              setRescheduleDate(appt.appointment_date);
                            }}
                          >
                            <CalendarClock size={14} /> Reschedule
                          </button>
                          <button
                            type="button"
                            className="btn btn--danger btn--sm"
                            onClick={() => setCancelTarget(appt)}
                          >
                            <XCircle size={14} /> Cancel
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </GlassCard>
      </div>

      {/* Cancel Modal */}
      <Modal
        open={Boolean(cancelTarget)}
        title="Cancel Appointment"
        onClose={() => setCancelTarget(null)}
      >
        <form onSubmit={handleCancelSubmit} className="auth-form">
          <div className="field-group">
            <label htmlFor="cancel-reason" className="field-label">
              Reason for Cancellation
            </label>
            <textarea
              id="cancel-reason"
              rows={3}
              className="field-textarea"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn--danger">
            Confirm Cancellation
          </button>
        </form>
      </Modal>

      {/* Reschedule Modal */}
      <Modal
        open={Boolean(rescheduleTarget)}
        title="Reschedule Appointment"
        onClose={() => setRescheduleTarget(null)}
      >
        <form onSubmit={handleRescheduleSubmit} className="auth-form">
          <div className="field-group">
            <label htmlFor="resched-date" className="field-label">
              New Date
            </label>
            <input
              id="resched-date"
              type="date"
              min={todayStr}
              className="field-input"
              value={rescheduleDate}
              onChange={(e) => setRescheduleDate(e.target.value)}
            />
          </div>
          {rescheduleSlots?.unavailable_reason ? (
            <div className="alert alert--info">{rescheduleSlots.unavailable_reason}</div>
          ) : (
            <div className="slots-grid">
              {(rescheduleSlots?.slots || []).map((s) => (
                <button
                  key={s.time}
                  type="button"
                  disabled={!s.available}
                  className={`slot-btn ${rescheduleTime === s.time ? 'is-selected' : ''}`}
                  onClick={() => setRescheduleTime(s.time)}
                >
                  {s.display_time}
                </button>
              ))}
            </div>
          )}
          <button type="submit" className="btn btn--primary" disabled={!rescheduleTime}>
            Confirm Reschedule
          </button>
        </form>
      </Modal>

      {/* Consultation Notes Modal */}
      <Modal
        open={Boolean(notesTarget)}
        title="Shareable Consultation Notes"
        onClose={() => setNotesTarget(null)}
      >
        {notesTarget && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {notesTarget.consultation_notes.map((n) => (
              <div key={n.id} className="cause-item glass-surface--subtle">
                <div className="cause-item__head">
                  <strong>
                    <CheckCircle2 size={15} style={{ display: 'inline', marginRight: 5 }} />
                    Consultation Observations
                  </strong>
                  <span className="badge badge--success">Shared by Doctor</span>
                </div>
                <p style={{ color: 'var(--text-primary)', marginBottom: 6 }}>{n.observations}</p>
                {n.notes && <p style={{ marginBottom: 6 }}>Notes: {n.notes}</p>}
                {n.follow_up_recommendations && (
                  <p style={{ marginBottom: 6 }}>
                    <strong>Follow-up:</strong> {n.follow_up_recommendations}
                  </p>
                )}
                {n.treatment_info && (
                  <p style={{ margin: 0 }}>
                    <strong>Treatment Information:</strong> {n.treatment_info}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
}

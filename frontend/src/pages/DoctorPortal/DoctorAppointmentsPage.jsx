import { useEffect, useState } from 'react';
import {
  CalendarClock,
  Check,
  FileText,
  NotebookPen,
  X,
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

export function DoctorAppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const [rejectTarget, setRejectTarget] = useState(null);
  const [rejectReason, setRejectReason] = useState('');

  const [reschedTarget, setReschedTarget] = useState(null);
  const [reschedDate, setReschedDate] = useState('');
  const [reschedTime, setReschedTime] = useState('');

  const [noteTarget, setNoteTarget] = useState(null);
  const [noteForm, setNoteForm] = useState({
    observations: '',
    notes: '',
    follow_up_recommendations: '',
    treatment_info: '',
    is_shareable: true,
  });

  const [reportsModal, setReportsModal] = useState({ open: false, items: [], patientName: '' });
  const { showToast } = useToast();

  const loadAppointments = async (filter = statusFilter) => {
    setLoading(true);
    try {
      const data = await healthcareService.listDoctorAppointments(filter);
      setAppointments(data);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to load appointments'), 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments(statusFilter);
  }, [statusFilter]);

  const handleAction = async (id, payload, successMsg) => {
    try {
      await healthcareService.updateDoctorAppointmentStatus(id, payload);
      showToast(successMsg, 'success');
      loadAppointments(statusFilter);
    } catch (err) {
      showToast(extractApiError(err, 'Action failed'), 'error');
    }
  };

  const handleViewSharedReports = async (appt) => {
    try {
      const items = await healthcareService.getDoctorAppointmentReports(appt.id);
      setReportsModal({ open: true, items, patientName: appt.patient_name });
    } catch (err) {
      showToast(extractApiError(err, 'Unable to load shared reports'), 'error');
    }
  };

  const handleSaveNote = async (e) => {
    e.preventDefault();
    if (!noteTarget || noteForm.observations.trim().length < 3) {
      showToast('Please enter consultation observations', 'warning');
      return;
    }
    try {
      await healthcareService.addConsultationNote(noteTarget.id, noteForm);
      showToast('Consultation note saved', 'success');
      setNoteTarget(null);
      setNoteForm({
        observations: '',
        notes: '',
        follow_up_recommendations: '',
        treatment_info: '',
        is_shareable: true,
      });
      loadAppointments(statusFilter);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to save consultation note'), 'error');
    }
  };

  return (
    <div className="animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--primary">Doctor Appointment Management</span>}
        title="Manage Patient Appointments"
        subtitle="Review requests, confirm or decline with reasons, reschedule, view authorized shared reports, and record consultation notes."
        actions={
          <select
            className="field-select"
            style={{ width: 'auto' }}
            aria-label="Filter appointments"
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
        }
      />

      {loading ? (
        <LoadingSpinner label="Loading doctor appointments..." />
      ) : appointments.length === 0 ? (
        <EmptyState
          icon={CalendarClock}
          title="No appointments found"
          description="Incoming patient booking requests and consultations will appear here."
        />
      ) : (
        <GlassCard>
          <div className="dash-record-list">
            {appointments.map((appt) => (
              <div key={appt.id} className="symptom-history-item glass-surface--subtle">
                <div className="symptom-history-main">
                  <div className="symptom-history-top">
                    <strong>{appt.patient_name}</strong>
                    <span className="badge badge--cyan">{appt.status}</span>
                    {appt.share_reports && (
                      <span className="badge badge--success">Reports Shared</span>
                    )}
                  </div>
                  <div className="symptom-history-meta">
                    {appt.patient_email}
                    {appt.patient_phone ? ` · ${appt.patient_phone}` : ''} ·{' '}
                    {appt.appointment_date} at {appt.appointment_time.slice(0, 5)}
                  </div>
                  <p style={{ margin: '6px 0 0', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                    <strong>Reason:</strong> {appt.reason}
                  </p>
                  {appt.consultation_notes?.length > 0 && (
                    <div style={{ fontSize: '0.82rem', color: 'var(--color-primary)', marginTop: 4 }}>
                      {appt.consultation_notes.length} consultation note(s) recorded
                    </div>
                  )}
                </div>

                <div className="symptom-history-actions" style={{ flexWrap: 'wrap' }}>
                  {appt.share_reports && (
                    <button
                      type="button"
                      className="btn btn--glass btn--sm"
                      onClick={() => handleViewSharedReports(appt)}
                    >
                      <FileText size={14} /> Reports
                    </button>
                  )}

                  {['pending', 'rescheduled'].includes(appt.status) && (
                    <button
                      type="button"
                      className="btn btn--primary btn--sm"
                      onClick={() =>
                        handleAction(appt.id, { status: 'confirmed' }, 'Appointment confirmed')
                      }
                    >
                      <Check size={14} /> Confirm
                    </button>
                  )}

                  {['pending', 'confirmed', 'rescheduled'].includes(appt.status) && (
                    <>
                      <button
                        type="button"
                        className="btn btn--glass btn--sm"
                        onClick={() => {
                          setReschedTarget(appt);
                          setReschedDate(appt.appointment_date);
                          setReschedTime(appt.appointment_time.slice(0, 5));
                        }}
                      >
                        Reschedule
                      </button>
                      <button
                        type="button"
                        className="btn btn--glass btn--sm"
                        onClick={() =>
                          handleAction(appt.id, { status: 'completed' }, 'Marked completed')
                        }
                      >
                        Complete
                      </button>
                      <button
                        type="button"
                        className="btn btn--danger btn--sm"
                        onClick={() => setRejectTarget(appt)}
                      >
                        <X size={14} /> Reject
                      </button>
                    </>
                  )}

                  <button
                    type="button"
                    className="btn btn--glass btn--sm"
                    onClick={() => setNoteTarget(appt)}
                  >
                    <NotebookPen size={14} /> Add Note
                  </button>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Reject Modal */}
      <Modal
        open={Boolean(rejectTarget)}
        title="Reject Appointment Request"
        onClose={() => setRejectTarget(null)}
      >
        <form
          className="auth-form"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!rejectReason.trim()) return;
            await handleAction(
              rejectTarget.id,
              { status: 'rejected', reason: rejectReason.trim() },
              'Appointment declined'
            );
            setRejectTarget(null);
            setRejectReason('');
          }}
        >
          <div className="field-group">
            <label htmlFor="rej-reason" className="field-label">
              Reason for Rejection
            </label>
            <textarea
              id="rej-reason"
              rows={3}
              className="field-textarea"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn--danger">
            Confirm Rejection
          </button>
        </form>
      </Modal>

      {/* Reschedule Modal */}
      <Modal
        open={Boolean(reschedTarget)}
        title="Reschedule Patient Appointment"
        onClose={() => setReschedTarget(null)}
      >
        <form
          className="auth-form"
          onSubmit={async (e) => {
            e.preventDefault();
            await handleAction(
              reschedTarget.id,
              {
                status: 'rescheduled',
                appointment_date: reschedDate,
                appointment_time: `${reschedTime}:00`,
              },
              'Appointment rescheduled'
            );
            setReschedTarget(null);
          }}
        >
          <div className="field-group">
            <label htmlFor="doc-resched-date" className="field-label">
              New Date
            </label>
            <input
              id="doc-resched-date"
              type="date"
              className="field-input"
              value={reschedDate}
              onChange={(e) => setReschedDate(e.target.value)}
              required
            />
          </div>
          <div className="field-group">
            <label htmlFor="doc-resched-time" className="field-label">
              New Time
            </label>
            <input
              id="doc-resched-time"
              type="time"
              className="field-input"
              value={reschedTime}
              onChange={(e) => setReschedTime(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn--primary">
            Save Reschedule
          </button>
        </form>
      </Modal>

      {/* Consultation Note Modal */}
      <Modal
        open={Boolean(noteTarget)}
        title={`Consultation Note — ${noteTarget?.patient_name || ''}`}
        onClose={() => setNoteTarget(null)}
      >
        <form onSubmit={handleSaveNote} className="auth-form">
          <div className="field-group">
            <label htmlFor="note-obs" className="field-label">
              Consultation Observations *
            </label>
            <textarea
              id="note-obs"
              rows={3}
              className="field-textarea"
              value={noteForm.observations}
              onChange={(e) => setNoteForm((f) => ({ ...f, observations: e.target.value }))}
              required
            />
          </div>
          <div className="field-group">
            <label htmlFor="note-extra" className="field-label">
              Clinical Notes
            </label>
            <textarea
              id="note-extra"
              rows={2}
              className="field-textarea"
              value={noteForm.notes}
              onChange={(e) => setNoteForm((f) => ({ ...f, notes: e.target.value }))}
            />
          </div>
          <div className="field-group">
            <label htmlFor="note-followup" className="field-label">
              Follow-Up Recommendations
            </label>
            <textarea
              id="note-followup"
              rows={2}
              className="field-textarea"
              value={noteForm.follow_up_recommendations}
              onChange={(e) =>
                setNoteForm((f) => ({ ...f, follow_up_recommendations: e.target.value }))
              }
            />
          </div>
          <div className="field-group">
            <label htmlFor="note-treatment" className="field-label">
              Relevant Treatment Information
            </label>
            <textarea
              id="note-treatment"
              rows={2}
              className="field-textarea"
              value={noteForm.treatment_info}
              onChange={(e) => setNoteForm((f) => ({ ...f, treatment_info: e.target.value }))}
            />
          </div>
          <label className="remember-check">
            <input
              type="checkbox"
              checked={noteForm.is_shareable}
              onChange={(e) => setNoteForm((f) => ({ ...f, is_shareable: e.target.checked }))}
            />
            <span>Make this note visible to the patient</span>
          </label>
          <button type="submit" className="btn btn--primary">
            Save Consultation Note
          </button>
        </form>
      </Modal>

      {/* Shared Reports Modal */}
      <Modal
        open={reportsModal.open}
        title={`Authorized Shared Reports — ${reportsModal.patientName}`}
        onClose={() => setReportsModal({ open: false, items: [], patientName: '' })}
      >
        {reportsModal.items.length === 0 ? (
          <p style={{ margin: 0, color: 'var(--text-muted)' }}>
            No uploaded reports available for this patient.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {reportsModal.items.map((rep) => (
              <div key={rep.id} className="cause-item glass-surface--subtle">
                <strong>{rep.original_filename}</strong>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  {rep.category} · Status: {rep.processing_status}
                </div>
                {rep.ai_summary && <p style={{ marginTop: 6 }}>{rep.ai_summary}</p>}
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
}

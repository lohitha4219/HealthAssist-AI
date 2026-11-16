import { useEffect, useState } from 'react';
import { CalendarOff, Clock, Plus, Save, Trash2 } from 'lucide-react';
import { healthcareService } from '../../services/healthcareService';
import { extractApiError } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import { GlassCard, LoadingSpinner, PageHeader } from '../../components/common/CommonUI';

const DAYS = [
  { idx: 0, label: 'Monday' },
  { idx: 1, label: 'Tuesday' },
  { idx: 2, label: 'Wednesday' },
  { idx: 3, label: 'Thursday' },
  { idx: 4, label: 'Friday' },
  { idx: 5, label: 'Saturday' },
  { idx: 6, label: 'Sunday' },
];

export function DoctorAvailabilityPage() {
  const [rules, setRules] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [newRule, setNewRule] = useState({
    day_of_week: 0,
    start_time: '09:00',
    end_time: '17:00',
    slot_duration_minutes: 30,
    break_start: '13:00',
    break_end: '14:00',
    is_active: true,
  });

  const [newLeave, setNewLeave] = useState({
    leave_date: '',
    reason: '',
    is_holiday: false,
  });

  const { showToast } = useToast();

  useEffect(() => {
    Promise.all([
      healthcareService.getDoctorAvailability(),
      healthcareService.listDoctorLeaves(),
    ])
      .then(([avail, lvs]) => {
        setRules(
          avail.map((r) => ({
            ...r,
            start_time: r.start_time.slice(0, 5),
            end_time: r.end_time.slice(0, 5),
            break_start: r.break_start ? r.break_start.slice(0, 5) : '',
            break_end: r.break_end ? r.break_end.slice(0, 5) : '',
          }))
        );
        setLeaves(lvs);
      })
      .catch((err) => showToast(extractApiError(err, 'Failed to load availability'), 'error'))
      .finally(() => setLoading(false));
  }, []);

  const handleAddRule = () => {
    setRules((prev) => [...prev, { ...newRule }]);
  };

  const handleSaveSchedule = async () => {
    setSaving(true);
    try {
      const payload = rules.map((r) => ({
        day_of_week: Number(r.day_of_week),
        start_time: `${r.start_time}:00`,
        end_time: `${r.end_time}:00`,
        slot_duration_minutes: Number(r.slot_duration_minutes),
        break_start: r.break_start ? `${r.break_start}:00` : null,
        break_end: r.break_end ? `${r.break_end}:00` : null,
        is_active: Boolean(r.is_active),
      }));
      await healthcareService.saveDoctorAvailability(payload);
      showToast('Weekly consultation schedule saved', 'success');
    } catch (err) {
      showToast(extractApiError(err, 'Failed to save schedule'), 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleAddLeave = async (e) => {
    e.preventDefault();
    if (!newLeave.leave_date) return;
    try {
      const created = await healthcareService.addDoctorLeave(newLeave);
      setLeaves((prev) => [...prev, created]);
      setNewLeave({ leave_date: '', reason: '', is_holiday: false });
      showToast('Leave / holiday added', 'success');
    } catch (err) {
      showToast(extractApiError(err, 'Unable to add leave date'), 'error');
    }
  };

  const handleDeleteLeave = async (id) => {
    try {
      await healthcareService.deleteDoctorLeave(id);
      setLeaves((prev) => prev.filter((l) => l.id !== id));
      showToast('Leave date removed', 'info');
    } catch (err) {
      showToast(extractApiError(err), 'error');
    }
  };

  if (loading) return <LoadingSpinner label="Loading schedule configuration..." />;

  return (
    <div className="animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--cyan">Schedule Configuration</span>}
        title="Availability &amp; Leave"
        subtitle="Configure working days, slot durations, break windows, holidays, and leave dates."
      />

      <div className="dir-detail-grid">
        <GlassCard>
          <h2 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Clock size={18} color="var(--color-primary)" /> Weekly Working Hours
          </h2>

          <div className="auth-optional-box" style={{ marginBottom: 16 }}>
            <div className="auth-two-col">
              <div className="field-group">
                <label className="field-label">Day of Week</label>
                <select
                  className="field-select"
                  value={newRule.day_of_week}
                  onChange={(e) =>
                    setNewRule((r) => ({ ...r, day_of_week: Number(e.target.value) }))
                  }
                >
                  {DAYS.map((d) => (
                    <option key={d.idx} value={d.idx}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field-group">
                <label className="field-label">Slot Duration (min)</label>
                <input
                  type="number"
                  min={10}
                  max={120}
                  className="field-input"
                  value={newRule.slot_duration_minutes}
                  onChange={(e) =>
                    setNewRule((r) => ({ ...r, slot_duration_minutes: Number(e.target.value) }))
                  }
                />
              </div>
              <div className="field-group">
                <label className="field-label">Start Time</label>
                <input
                  type="time"
                  className="field-input"
                  value={newRule.start_time}
                  onChange={(e) => setNewRule((r) => ({ ...r, start_time: e.target.value }))}
                />
              </div>
              <div className="field-group">
                <label className="field-label">End Time</label>
                <input
                  type="time"
                  className="field-input"
                  value={newRule.end_time}
                  onChange={(e) => setNewRule((r) => ({ ...r, end_time: e.target.value }))}
                />
              </div>
              <div className="field-group">
                <label className="field-label">Break Start (Optional)</label>
                <input
                  type="time"
                  className="field-input"
                  value={newRule.break_start}
                  onChange={(e) => setNewRule((r) => ({ ...r, break_start: e.target.value }))}
                />
              </div>
              <div className="field-group">
                <label className="field-label">Break End (Optional)</label>
                <input
                  type="time"
                  className="field-input"
                  value={newRule.break_end}
                  onChange={(e) => setNewRule((r) => ({ ...r, break_end: e.target.value }))}
                />
              </div>
            </div>
            <button type="button" className="btn btn--glass btn--sm" onClick={handleAddRule}>
              <Plus size={15} /> Add Working Block
            </button>
          </div>

          <div className="dash-record-list" style={{ marginBottom: 16 }}>
            {rules.map((r, idx) => (
              <div key={idx} className="dash-record-row">
                <div>
                  <strong>{DAYS.find((d) => d.idx === r.day_of_week)?.label}</strong>
                  <div className="dash-record-row__meta">
                    {r.start_time} – {r.end_time} ({r.slot_duration_minutes}m)
                    {r.break_start && r.break_end ? ` · Break ${r.break_start}–${r.break_end}` : ''}
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn--danger btn--sm"
                  onClick={() => setRules((prev) => prev.filter((_, i) => i !== idx))}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>

          <button
            type="button"
            className="btn btn--primary"
            disabled={saving}
            onClick={handleSaveSchedule}
          >
            <Save size={16} /> {saving ? 'Saving...' : 'Save Weekly Schedule'}
          </button>
        </GlassCard>

        <GlassCard>
          <h2 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <CalendarOff size={18} color="var(--color-accent)" /> Holidays &amp; Leave Dates
          </h2>
          <form onSubmit={handleAddLeave} className="auth-form" style={{ marginBottom: 18 }}>
            <div className="field-group">
              <label htmlFor="lv-date" className="field-label">
                Leave / Holiday Date
              </label>
              <input
                id="lv-date"
                type="date"
                className="field-input"
                value={newLeave.leave_date}
                onChange={(e) => setNewLeave((l) => ({ ...l, leave_date: e.target.value }))}
                required
              />
            </div>
            <div className="field-group">
              <label htmlFor="lv-reason" className="field-label">
                Reason
              </label>
              <input
                id="lv-reason"
                type="text"
                className="field-input"
                placeholder="Conference, personal leave, public holiday..."
                value={newLeave.reason}
                onChange={(e) => setNewLeave((l) => ({ ...l, reason: e.target.value }))}
              />
            </div>
            <label className="remember-check">
              <input
                type="checkbox"
                checked={newLeave.is_holiday}
                onChange={(e) => setNewLeave((l) => ({ ...l, is_holiday: e.target.checked }))}
              />
              <span>Mark as hospital/public holiday</span>
            </label>
            <button type="submit" className="btn btn--primary btn--sm">
              <Plus size={15} /> Add Leave Date
            </button>
          </form>

          <div className="dash-record-list">
            {leaves.map((lv) => (
              <div key={lv.id} className="dash-record-row">
                <div>
                  <strong>{lv.leave_date}</strong>
                  <div className="dash-record-row__meta">
                    {lv.is_holiday ? 'Holiday' : 'Leave'}
                    {lv.reason ? ` · ${lv.reason}` : ''}
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn--danger btn--sm"
                  onClick={() => handleDeleteLeave(lv.id)}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

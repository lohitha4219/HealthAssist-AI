import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Plus,
  Search,
  ShieldAlert,
  Stethoscope,
  Trash2,
} from 'lucide-react';
import { healthService } from '../../services/healthService';
import { extractApiError } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import {
  EmptyState,
  GlassCard,
  LoadingSpinner,
  PageHeader,
} from '../../components/common/CommonUI';
import { formatDateTime, formatUrgencyLabel } from '../../utils/formatters';
import './SymptomsPage.css';

const DURATIONS = ['< 24 hours', '1-3 days', '4-7 days', '1-2 weeks', '> 2 weeks'];
const SEVERITIES = [
  { value: 'mild', label: 'Mild', desc: 'Noticeable, manageable daily activity' },
  { value: 'moderate', label: 'Moderate', desc: 'Interferes with comfort or routine' },
  { value: 'severe', label: 'Severe', desc: 'Intense discomfort or limiting' },
];

export function SymptomAnalysisPage() {
  const [catalog, setCatalog] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [customSymptom, setCustomSymptom] = useState('');
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [duration, setDuration] = useState('1-3 days');
  const [severity, setSeverity] = useState('mild');
  const [additionalDetails, setAdditionalDetails] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [latestResult, setLatestResult] = useState(null);

  const [history, setHistory] = useState([]);
  const [totalHistory, setTotalHistory] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const { showToast } = useToast();
  const pageSize = 6;

  const loadData = async (targetPage = 1) => {
    setLoading(true);
    setError('');
    try {
      const [catData, histData] = await Promise.all([
        healthService.getSymptomCatalog(),
        healthService.getSymptomHistory(targetPage, pageSize),
      ]);
      setCatalog(catData);
      setHistory(histData.items);
      setTotalHistory(histData.total);
    } catch (err) {
      setError(extractApiError(err, 'Failed to load symptom analysis module'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(page);
  }, [page]);

  const filteredCatalog = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return catalog;
    return catalog.filter(
      (item) =>
        item.name.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q)
    );
  }, [catalog, searchQuery]);

  const toggleSymptom = (name) => {
    setSelectedSymptoms((prev) =>
      prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name]
    );
  };

  const addCustomSymptom = () => {
    const cleaned = customSymptom.trim();
    if (!cleaned) return;
    if (!selectedSymptoms.some((s) => s.toLowerCase() === cleaned.toLowerCase())) {
      setSelectedSymptoms((prev) => [...prev, cleaned]);
    }
    setCustomSymptom('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedSymptoms.length === 0) {
      showToast('Please select or add at least one symptom', 'warning');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const res = await healthService.assessSymptoms({
        symptoms: selectedSymptoms,
        duration,
        severity,
        additional_details: additionalDetails.trim() || null,
      });
      setLatestResult(res);
      showToast('Educational symptom assessment saved', 'success');
      setPage(1);
      const histData = await healthService.getSymptomHistory(1, pageSize);
      setHistory(histData.items);
      setTotalHistory(histData.total);
    } catch (err) {
      setError(extractApiError(err, 'Unable to complete symptom assessment'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await healthService.deleteSymptomAssessment(id);
      if (latestResult?.id === id) setLatestResult(null);
      showToast('Assessment removed', 'info');
      loadData(page);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to delete assessment'), 'error');
    }
  };

  if (loading && catalog.length === 0) {
    return <LoadingSpinner label="Loading Symptom Analysis..." />;
  }

  const totalPages = Math.max(1, Math.ceil(totalHistory / pageSize));

  return (
    <div className="symptoms-page animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--accent">Educational Health Triage</span>}
        title="Symptom Analysis"
        subtitle="Select symptoms, duration, and severity to view general educational explanations and guidance on when to seek care."
      />

      <div className="alert alert--info" style={{ marginBottom: 20 }}>
        <ShieldAlert size={18} style={{ flexShrink: 0, marginTop: 2 }} />
        <span>
          <strong>Educational Notice:</strong> HealthAssist AI does not diagnose diseases or
          prescribe medications. For severe chest pain, breathing difficulty, fainting, or
          sudden neurological changes, seek immediate emergency medical care.
        </span>
      </div>

      {error && (
        <div className="alert alert--error" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      <div className="symptoms-grid">
        {/* Form Panel */}
        <GlassCard>
          <form onSubmit={handleSubmit} className="symptoms-form">
            <div className="field-group">
              <label htmlFor="symptom-search" className="field-label">
                1. Search & Select Symptoms ({selectedSymptoms.length} selected)
              </label>
              <div className="symptom-search-wrap">
                <Search size={17} className="symptom-search-icon" />
                <input
                  id="symptom-search"
                  type="text"
                  className="field-input symptom-search-input"
                  placeholder="Search symptoms (e.g. headache, cough, fever, respiratory)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            {selectedSymptoms.length > 0 && (
              <div className="selected-chips-box">
                {selectedSymptoms.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="selected-chip"
                    onClick={() => toggleSymptom(s)}
                  >
                    {s} &times;
                  </button>
                ))}
              </div>
            )}

            <div className="symptom-catalog-grid">
              {filteredCatalog.map((item) => {
                const active = selectedSymptoms.includes(item.name);
                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`symptom-chip ${active ? 'is-selected' : ''} ${
                      item.is_red_flag ? 'is-red-flag' : ''
                    }`}
                    onClick={() => toggleSymptom(item.name)}
                  >
                    <span>{item.name}</span>
                    <small>{item.is_red_flag ? 'Urgent flag' : item.category}</small>
                  </button>
                );
              })}
            </div>

            <div className="custom-symptom-row">
              <input
                type="text"
                className="field-input"
                placeholder="Add another symptom not listed above..."
                value={customSymptom}
                onChange={(e) => setCustomSymptom(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addCustomSymptom();
                  }
                }}
              />
              <button
                type="button"
                className="btn btn--glass"
                onClick={addCustomSymptom}
              >
                <Plus size={16} /> Add
              </button>
            </div>

            <div className="symptoms-meta-row">
              <div className="field-group">
                <label htmlFor="symptom-duration" className="field-label">
                  2. Duration
                </label>
                <select
                  id="symptom-duration"
                  className="field-select"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                >
                  {DURATIONS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field-group">
                <span className="field-label">3. Severity</span>
                <div className="severity-pills">
                  {SEVERITIES.map((sev) => (
                    <button
                      key={sev.value}
                      type="button"
                      className={`severity-pill ${
                        severity === sev.value ? 'is-active' : ''
                      }`}
                      onClick={() => setSeverity(sev.value)}
                      title={sev.desc}
                    >
                      {sev.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="symptom-details" className="field-label">
                4. Additional Information (Optional)
              </label>
              <textarea
                id="symptom-details"
                rows={3}
                className="field-textarea"
                placeholder="Note triggers, temperature readings, medications taken, or relevant context..."
                value={additionalDetails}
                onChange={(e) => setAdditionalDetails(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn--primary btn--lg"
              disabled={submitting || selectedSymptoms.length === 0}
            >
              {submitting ? (
                <>
                  <Loader2 size={18} className="spin" /> Analyzing Symptoms...
                </>
              ) : (
                <>
                  <Stethoscope size={18} /> Submit Assessment
                </>
              )}
            </button>
          </form>
        </GlassCard>

        {/* Results Panel */}
        <div className="symptoms-result-col">
          {latestResult ? (
            <GlassCard className="glass-surface--strong animate-fade-up">
              <div className="result-header">
                <span
                  className={`badge ${
                    latestResult.urgency_level === 'urgent_emergency'
                      ? 'badge--danger'
                      : latestResult.urgency_level === 'prompt_care'
                      ? 'badge--warning'
                      : 'badge--success'
                  }`}
                >
                  {formatUrgencyLabel(latestResult.urgency_level)}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {formatDateTime(latestResult.created_at)}
                </span>
              </div>

              <h2 className="result-title">Educational Assessment Summary</h2>

              {latestResult.emergency_warning && (
                <div className="alert alert--error" style={{ marginBottom: 14 }}>
                  <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
                  <span>{latestResult.emergency_warning}</span>
                </div>
              )}

              <p className="result-summary">{latestResult.educational_summary}</p>

              <h3 className="result-subheading">General Possible Factors (Educational)</h3>
              <div className="causes-list">
                {latestResult.possible_causes.map((cause, idx) => (
                  <div key={idx} className="cause-item glass-surface--subtle">
                    <div className="cause-item__head">
                      <strong>{cause.title}</strong>
                      <span className="badge badge--cyan">{cause.category}</span>
                    </div>
                    <p>{cause.description}</p>
                  </div>
                ))}
              </div>

              <h3 className="result-subheading">Guidance & When to Seek Care</h3>
              <ul className="guidance-list">
                {latestResult.care_guidance.map((tip, idx) => (
                  <li key={idx}>
                    <CheckCircle2 size={16} color="var(--color-primary)" />
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>

              <p className="result-disclaimer">{latestResult.disclaimer}</p>
            </GlassCard>
          ) : (
            <EmptyState
              icon={Stethoscope}
              title="Ready for Educational Assessment"
              description="Choose one or more symptoms on the left and submit to generate and save an educational summary."
            />
          )}
        </div>
      </div>

      {/* Assessment History */}
      <GlassCard style={{ marginTop: 24 }}>
        <div className="dash-card-head">
          <h2 className="dash-card-title">Past Symptom Assessments ({totalHistory})</h2>
        </div>

        {history.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', margin: 0 }}>
            No assessments recorded yet.
          </p>
        ) : (
          <>
            <div className="symptom-history-list">
              {history.map((item) => (
                <div key={item.id} className="symptom-history-item glass-surface--subtle">
                  <div className="symptom-history-main">
                    <div className="symptom-history-top">
                      <strong>{item.symptoms.join(', ')}</strong>
                      <span
                        className={`badge ${
                          item.urgency_level === 'urgent_emergency'
                            ? 'badge--danger'
                            : item.urgency_level === 'prompt_care'
                            ? 'badge--warning'
                            : 'badge--success'
                        }`}
                      >
                        {formatUrgencyLabel(item.urgency_level)}
                      </span>
                    </div>
                    <div className="symptom-history-meta">
                      Severity: {item.severity} · Duration: {item.duration} ·{' '}
                      {formatDateTime(item.created_at)}
                    </div>
                  </div>
                  <div className="symptom-history-actions">
                    <button
                      type="button"
                      className="btn btn--glass btn--sm"
                      onClick={() => setLatestResult(item)}
                    >
                      View
                    </button>
                    <button
                      type="button"
                      className="btn btn--danger btn--sm"
                      aria-label="Delete assessment"
                      onClick={() => handleDelete(item.id)}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="pagination-row">
                <button
                  type="button"
                  className="btn btn--glass btn--sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </button>
                <span>
                  Page {page} of {totalPages}
                </span>
                <button
                  type="button"
                  className="btn btn--glass btn--sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </GlassCard>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Clock, Eye, Search, Trash2 } from 'lucide-react';
import { healthService } from '../../services/healthService';
import { extractApiError } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import {
  EmptyState,
  GlassCard,
  LoadingSpinner,
  Modal,
  PageHeader,
} from '../../components/common/CommonUI';
import { formatDateTime } from '../../utils/formatters';
import './HistoryPage.css';

const RECORD_TYPES = [
  { value: 'all', label: 'All Records' },
  { value: 'assessment', label: 'Symptom Assessments' },
  { value: 'report', label: 'Medical Reports' },
  { value: 'activity', label: 'Health Activities' },
];

export function HealthHistoryPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [recordType, setRecordType] = useState('all');
  const [search, setSearch] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedEntry, setSelectedEntry] = useState(null);

  const { showToast } = useToast();
  const pageSize = 10;

  const fetchHistory = async (targetPage = page) => {
    setLoading(true);
    try {
      const res = await healthService.getHistory({
        record_type: recordType,
        search: search.trim() || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        page: targetPage,
        page_size: pageSize,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to load health history'), 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(page);
  }, [page, recordType]);

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchHistory(1);
  };

  const handleDelete = async (entry) => {
    try {
      await healthService.deleteHistoryRecord(entry.record_type, entry.id);
      if (selectedEntry?.id === entry.id) setSelectedEntry(null);
      showToast('Record removed from history', 'info');
      fetchHistory(page);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to delete record'), 'error');
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="history-page animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--primary">Chronological Timeline</span>}
        title="Health History"
        subtitle="Search, filter, inspect, and manage your chronological assessments, uploaded reports, and account activities."
      />

      <GlassCard style={{ marginBottom: 20 }}>
        <form onSubmit={handleFilterSubmit} className="history-filter-bar">
          <div className="symptom-search-wrap" style={{ flex: 2, minWidth: 200 }}>
            <Search size={16} className="symptom-search-icon" />
            <input
              type="text"
              className="field-input symptom-search-input"
              placeholder="Search titles, symptoms, filenames..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="field-select"
            aria-label="Filter record type"
            value={recordType}
            onChange={(e) => {
              setPage(1);
              setRecordType(e.target.value);
            }}
          >
            {RECORD_TYPES.map((rt) => (
              <option key={rt.value} value={rt.value}>
                {rt.label}
              </option>
            ))}
          </select>

          <input
            type="date"
            className="field-input"
            aria-label="Start date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <input
            type="date"
            className="field-input"
            aria-label="End date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />

          <button type="submit" className="btn btn--primary btn--sm">
            Apply Filters
          </button>
        </form>
      </GlassCard>

      {loading ? (
        <LoadingSpinner label="Loading chronological history..." />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Clock}
          title="No matching history records"
          description="Try clearing search filters or log a symptom assessment or report upload."
        />
      ) : (
        <GlassCard>
          <div className="history-list">
            {items.map((entry) => (
              <div key={`${entry.record_type}-${entry.id}`} className="history-row glass-surface--subtle">
                <div className="history-row__info">
                  <div className="history-row__badges">
                    <span className="badge badge--primary">{entry.record_type}</span>
                    <span className="badge badge--cyan">{entry.badge}</span>
                  </div>
                  <div className="history-row__title">{entry.title}</div>
                  <div className="history-row__meta">
                    {entry.subtitle} · {formatDateTime(entry.created_at)}
                  </div>
                </div>

                <div className="history-row__actions">
                  <button
                    type="button"
                    className="btn btn--glass btn--sm"
                    onClick={() => setSelectedEntry(entry)}
                  >
                    <Eye size={15} /> Details
                  </button>
                  {entry.deletable && (
                    <button
                      type="button"
                      className="btn btn--danger btn--sm"
                      aria-label={`Delete ${entry.title}`}
                      onClick={() => handleDelete(entry)}
                    >
                      <Trash2 size={15} />
                    </button>
                  )}
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
                Page {page} of {totalPages} ({total} total)
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
        </GlassCard>
      )}

      <Modal
        open={Boolean(selectedEntry)}
        title={selectedEntry?.title || 'Record Details'}
        onClose={() => setSelectedEntry(null)}
      >
        {selectedEntry && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              Type: <strong>{selectedEntry.record_type}</strong> · Logged:{' '}
              {formatDateTime(selectedEntry.created_at)}
            </div>
            <p style={{ margin: 0 }}>{selectedEntry.subtitle}</p>
            {selectedEntry.details?.educational_summary && (
              <div className="alert alert--info">
                {selectedEntry.details.educational_summary}
              </div>
            )}
            {selectedEntry.details?.extracted_text && (
              <pre className="report-extracted-text">
                {selectedEntry.details.extracted_text}
              </pre>
            )}
            {selectedEntry.details?.description && (
              <p style={{ margin: 0, color: 'var(--text-secondary)' }}>
                {selectedEntry.details.description}
              </p>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

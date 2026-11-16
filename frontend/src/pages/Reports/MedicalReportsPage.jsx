import { useEffect, useRef, useState } from 'react';
import {
  Download,
  Eye,
  FileText,
  Image as ImageIcon,
  Loader2,
  Search,
  Trash2,
  UploadCloud,
} from 'lucide-react';
import { reportService } from '../../services/chatAndReportService';
import { extractApiError } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import {
  EmptyState,
  GlassCard,
  LoadingSpinner,
  Modal,
  PageHeader,
} from '../../components/common/CommonUI';
import { formatBytes, formatDateTime } from '../../utils/formatters';
import './ReportsPage.css';

const CATEGORIES = [
  'General Report',
  'Lab Results',
  'Imaging',
  'Prescription Summary',
  'Consultation Notes',
];

export function MedicalReportsPage() {
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [loading, setLoading] = useState(true);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadCategory, setUploadCategory] = useState('Lab Results');
  const [uploadNotes, setUploadNotes] = useState('');
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const [detailReport, setDetailReport] = useState(null);
  const fileInputRef = useRef(null);
  const { showToast } = useToast();
  const pageSize = 8;

  const fetchReports = async (targetPage = page) => {
    setLoading(true);
    try {
      const res = await reportService.listReports({
        page: targetPage,
        page_size: pageSize,
        search: search.trim() || undefined,
        category: categoryFilter !== 'All' ? categoryFilter : undefined,
      });
      setReports(res.items);
      setTotal(res.total);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to fetch medical reports'), 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports(page);
  }, [page, categoryFilter]);

  const handleFileSelect = (file) => {
    if (!file) return;
    const allowedExt = /\.(pdf|png|jpg|jpeg|webp)$/i;
    if (!allowedExt.test(file.name)) {
      showToast('Allowed formats: PDF, PNG, JPG, JPEG, WEBP', 'error');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      showToast('File size must be 10 MB or less', 'error');
      return;
    }
    setSelectedFile(file);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      showToast('Select a PDF or image file first', 'warning');
      return;
    }
    setUploading(true);
    try {
      await reportService.uploadReport(selectedFile, uploadCategory, uploadNotes.trim());
      showToast('Medical report uploaded and processed', 'success');
      setSelectedFile(null);
      setUploadNotes('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      setPage(1);
      fetchReports(1);
    } catch (err) {
      showToast(extractApiError(err, 'Upload failed'), 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (report) => {
    try {
      await reportService.downloadReport(report.id, report.original_filename);
    } catch (err) {
      showToast(extractApiError(err, 'Unable to download file'), 'error');
    }
  };

  const handleDelete = async (id) => {
    try {
      await reportService.deleteReport(id);
      if (detailReport?.id === id) setDetailReport(null);
      showToast('Report deleted', 'info');
      fetchReports(page);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to delete report'), 'error');
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="reports-page animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--primary">Protected File Vault</span>}
        title="Medical Reports"
        subtitle="Upload validated PDFs and images, inspect extracted text, and securely download or manage your files."
      />

      <div className="reports-grid">
        {/* Upload Card */}
        <GlassCard>
          <h2 className="dash-card-title">Upload Report</h2>
          <form onSubmit={handleUpload} className="reports-upload-form">
            <div
              className={`upload-dropzone ${dragOver ? 'is-drag-over' : ''}`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                handleFileSelect(e.dataTransfer.files?.[0]);
              }}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  fileInputRef.current?.click();
                }
              }}
            >
              <UploadCloud size={32} color="var(--color-primary)" />
              <div className="upload-dropzone__title">
                {selectedFile ? selectedFile.name : 'Click or drop a PDF or Image'}
              </div>
              <div className="upload-dropzone__sub">
                {selectedFile
                  ? `${formatBytes(selectedFile.size)} ready to upload`
                  : 'PDF, PNG, JPG, JPEG, WEBP · Max 10 MB'}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.webp"
                hidden
                onChange={(e) => handleFileSelect(e.target.files?.[0])}
              />
            </div>

            <div className="field-group">
              <label htmlFor="rep-category" className="field-label">
                Category
              </label>
              <select
                id="rep-category"
                className="field-select"
                value={uploadCategory}
                onChange={(e) => setUploadCategory(e.target.value)}
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div className="field-group">
              <label htmlFor="rep-notes" className="field-label">
                Notes (Optional)
              </label>
              <textarea
                id="rep-notes"
                rows={2}
                className="field-textarea"
                placeholder="Lab facility, clinician name, or summary notes..."
                value={uploadNotes}
                onChange={(e) => setUploadNotes(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn--primary"
              disabled={uploading || !selectedFile}
            >
              {uploading ? (
                <>
                  <Loader2 size={17} className="spin" /> Processing Upload...
                </>
              ) : (
                <>
                  <UploadCloud size={17} /> Upload & Process Report
                </>
              )}
            </button>
          </form>
        </GlassCard>

        {/* Reports List */}
        <GlassCard>
          <div className="reports-toolbar">
            <h2 className="dash-card-title" style={{ margin: 0 }}>
              Saved Reports ({total})
            </h2>
            <div className="reports-filters">
              <div className="symptom-search-wrap">
                <Search size={16} className="symptom-search-icon" />
                <input
                  type="text"
                  className="field-input symptom-search-input"
                  placeholder="Search filename or text..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      setPage(1);
                      fetchReports(1);
                    }
                  }}
                />
              </div>
              <select
                className="field-select"
                aria-label="Filter by category"
                value={categoryFilter}
                onChange={(e) => {
                  setPage(1);
                  setCategoryFilter(e.target.value);
                }}
              >
                <option value="All">All Categories</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="btn btn--glass btn--sm"
                onClick={() => {
                  setPage(1);
                  fetchReports(1);
                }}
              >
                Search
              </button>
            </div>
          </div>

          {loading ? (
            <LoadingSpinner label="Loading reports..." />
          ) : reports.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No medical reports found"
              description="Upload a PDF lab summary or medical image on the left to store and inspect it here."
            />
          ) : (
            <>
              <div className="reports-list">
                {reports.map((rep) => {
                  const isPdf = rep.content_type === 'application/pdf';
                  return (
                    <div key={rep.id} className="report-row glass-surface--subtle">
                      <div className="report-row__left">
                        <div className="report-row__icon">
                          {isPdf ? <FileText size={20} /> : <ImageIcon size={20} />}
                        </div>
                        <div style={{ minWidth: 0 }}>
                          <div className="report-row__name">{rep.original_filename}</div>
                          <div className="report-row__meta">
                            {rep.category} · {formatBytes(rep.file_size)} ·{' '}
                            {formatDateTime(rep.created_at)}
                          </div>
                          <div style={{ marginTop: 4 }}>
                            <span
                              className={`badge ${
                                rep.processing_status === 'extracted'
                                  ? 'badge--success'
                                  : rep.processing_status === 'scanned_no_text'
                                  ? 'badge--warning'
                                  : 'badge--cyan'
                              }`}
                            >
                              {rep.processing_status.replace(/_/g, ' ')}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="report-row__actions">
                        <button
                          type="button"
                          className="btn btn--glass btn--sm"
                          onClick={() => setDetailReport(rep)}
                        >
                          <Eye size={15} /> Details
                        </button>
                        <button
                          type="button"
                          className="btn btn--glass btn--sm"
                          onClick={() => handleDownload(rep)}
                        >
                          <Download size={15} /> Download
                        </button>
                        <button
                          type="button"
                          className="btn btn--danger btn--sm"
                          aria-label={`Delete ${rep.original_filename}`}
                          onClick={() => handleDelete(rep.id)}
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </div>
                  );
                })}
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

      <Modal
        open={Boolean(detailReport)}
        title={detailReport?.original_filename || 'Report Details'}
        onClose={() => setDetailReport(null)}
        width="720px"
      >
        {detailReport && (
          <div className="report-detail-body">
            <div className="report-detail-meta">
              <span>
                <strong>Category:</strong> {detailReport.category}
              </span>
              <span>
                <strong>Type:</strong> {detailReport.content_type}
              </span>
              <span>
                <strong>Size:</strong> {formatBytes(detailReport.file_size)}
              </span>
              <span>
                <strong>Uploaded:</strong> {formatDateTime(detailReport.created_at)}
              </span>
              {detailReport.page_count && (
                <span>
                  <strong>Pages:</strong> {detailReport.page_count}
                </span>
              )}
              {detailReport.image_width && (
                <span>
                  <strong>Dimensions:</strong> {detailReport.image_width} &times;{' '}
                  {detailReport.image_height} px
                </span>
              )}
            </div>

            {detailReport.notes && (
              <div className="alert alert--info">
                <strong>Notes:</strong> {detailReport.notes}
              </div>
            )}

            {detailReport.ai_summary && (
              <div className="alert alert--success" style={{ flexDirection: 'column', gap: 6 }}>
                <strong>Educational Analysis Summary</strong>
                <span>{detailReport.ai_summary}</span>
              </div>
            )}

            {detailReport.analysis?.findings?.length > 0 && (
              <div>
                <h4 style={{ margin: '8px 0' }}>
                  Parsed Laboratory Measurements ({detailReport.analysis.parsed_count})
                </h4>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ textAlign: 'left', borderBottom: '1px solid rgba(15,23,42,0.12)' }}>
                        <th style={{ padding: '6px 8px' }}>Test</th>
                        <th style={{ padding: '6px 8px' }}>Observed</th>
                        <th style={{ padding: '6px 8px' }}>Supplied Range</th>
                        <th style={{ padding: '6px 8px' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detailReport.analysis.findings.map((f, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid rgba(15,23,42,0.06)' }}>
                          <td style={{ padding: '6px 8px', fontWeight: 600 }}>{f.test_name}</td>
                          <td style={{ padding: '6px 8px' }}>
                            {f.observed_value} {f.unit || ''}
                          </td>
                          <td style={{ padding: '6px 8px' }}>
                            {f.reference_range || 'Not supplied'}
                          </td>
                          <td style={{ padding: '6px 8px' }}>
                            <span
                              className={`badge ${
                                f.status === 'high' || f.status === 'low'
                                  ? 'badge--danger'
                                  : f.status === 'normal'
                                  ? 'badge--success'
                                  : 'badge--cyan'
                              }`}
                            >
                              {f.status.replace(/_/g, ' ')}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {detailReport.analysis?.disclaimer && (
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 8 }}>
                    {detailReport.analysis.disclaimer}
                  </p>
                )}
              </div>
            )}

            <div>
              <h4 style={{ margin: '10px 0 6px' }}>Extracted Text Preview</h4>
              {detailReport.extracted_text ? (
                <pre className="report-extracted-text">{detailReport.extracted_text}</pre>
              ) : (
                <p style={{ color: 'var(--text-muted)', margin: 0 }}>
                  {detailReport.processing_status === 'scanned_no_text'
                    ? 'This PDF appears to be scanned/image-only without embedded text.'
                    : 'No text extraction available for image uploads; original file is safely stored for download.'}
                </p>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn--glass"
                onClick={async () => {
                  try {
                    const updated = await reportService.analyzeReport(detailReport.id);
                    setDetailReport(updated);
                    setReports((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
                    showToast('Report analysis refreshed', 'success');
                  } catch (err) {
                    showToast(extractApiError(err, 'Unable to re-analyze report'), 'error');
                  }
                }}
              >
                Re-analyze Text
              </button>
              <button
                type="button"
                className="btn btn--primary"
                onClick={() => handleDownload(detailReport)}
              >
                <Download size={16} /> Download Original File
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

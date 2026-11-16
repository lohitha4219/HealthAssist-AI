import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, BarChart3, Lightbulb, RefreshCw } from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { healthService } from '../../services/healthService';
import { extractApiError } from '../../services/apiClient';
import {
  EmptyState,
  GlassCard,
  LoadingSpinner,
  PageHeader,
} from '../../components/common/CommonUI';
import './InsightsPage.css';

const CHART_COLORS = ['#0B4F8A', '#0EA5E9', '#06B6D4', '#E11D48', '#6366F1', '#10B981'];

export function HealthInsightsPage() {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadInsights = async () => {
    setLoading(true);
    setError('');
    try {
      const [sumData, trendData] = await Promise.all([
        healthService.getInsightsSummary(),
        healthService.getInsightsTrends(),
      ]);
      setSummary(sumData);
      setTrends(trendData);
    } catch (err) {
      setError(extractApiError(err, 'Failed to load health insights'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInsights();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Analyzing your recorded health trends..." />;
  }

  if (error) {
    return (
      <GlassCard>
        <div className="alert alert--error" style={{ marginBottom: 14 }}>
          {error}
        </div>
        <button type="button" className="btn btn--primary" onClick={loadInsights}>
          <RefreshCw size={16} /> Retry
        </button>
      </GlassCard>
    );
  }

  return (
    <div className="insights-page animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--cyan">Live Record Analytics</span>}
        title="Health Insights"
        subtitle="Visual summaries and activity trends computed solely from your actual logged assessments, reports, and conversations."
      />

      {!summary.has_data ? (
        <EmptyState
          icon={BarChart3}
          title="Not enough personal records yet"
          description="Insights appear automatically as you complete symptom assessments, upload medical reports, or start AI conversations."
          action={
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center' }}>
              <Link to="/symptom-analysis" className="btn btn--primary btn--sm">
                Log Symptom Assessment
              </Link>
              <Link to="/medical-reports" className="btn btn--glass btn--sm">
                Upload Report
              </Link>
            </div>
          }
        />
      ) : (
        <>
          <div className="insights-summary-row">
            <GlassCard>
              <div className="dash-stat-card__value">{summary.total_assessments}</div>
              <div className="dash-stat-card__label">Assessments Analyzed</div>
            </GlassCard>
            <GlassCard>
              <div className="dash-stat-card__value">{summary.total_reports}</div>
              <div className="dash-stat-card__label">Reports Organized</div>
            </GlassCard>
            <GlassCard>
              <div className="dash-stat-card__value">{summary.total_conversations}</div>
              <div className="dash-stat-card__label">AI Chat Sessions</div>
            </GlassCard>
          </div>

          <div className="insights-charts-grid">
            {/* Activity Timeline Chart */}
            <GlassCard>
              <h2 className="dash-card-title">Activity Timeline</h2>
              {trends?.has_sufficient_data ? (
                <div className="chart-box">
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={trends.timeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.08)" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="assessments"
                        name="Assessments"
                        stroke="#E11D48"
                        fill="rgba(225, 29, 72, 0.2)"
                      />
                      <Area
                        type="monotone"
                        dataKey="reports"
                        name="Reports"
                        stroke="#0B4F8A"
                        fill="rgba(11, 79, 138, 0.2)"
                      />
                      <Area
                        type="monotone"
                        dataKey="chats"
                        name="Chats"
                        stroke="#06B6D4"
                        fill="rgba(6, 182, 212, 0.2)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>No timeline points available yet.</p>
              )}
            </GlassCard>

            {/* Top Symptoms */}
            <GlassCard>
              <h2 className="dash-card-title">Most Logged Symptoms</h2>
              {summary.top_symptoms.length > 0 ? (
                <div className="chart-box">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={summary.top_symptoms} layout="vertical" margin={{ left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.08)" />
                      <XAxis type="number" allowDecimals={false} />
                      <YAxis type="category" dataKey="label" width={120} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="count" name="Occurrences" fill="#0B4F8A" radius={[0, 8, 8, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>
                  Submit a symptom assessment to see top logged symptoms.
                </p>
              )}
            </GlassCard>

            {/* Severity Breakdown */}
            <GlassCard>
              <h2 className="dash-card-title">Assessment Severity Mix</h2>
              {summary.severity_breakdown.length > 0 ? (
                <div className="chart-box">
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie
                        data={summary.severity_breakdown}
                        dataKey="count"
                        nameKey="label"
                        cx="50%"
                        cy="50%"
                        outerRadius={90}
                        label
                      >
                        {summary.severity_breakdown.map((_, idx) => (
                          <Cell
                            key={idx}
                            fill={CHART_COLORS[idx % CHART_COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>No severity breakdown yet.</p>
              )}
            </GlassCard>

            {/* Report Categories */}
            <GlassCard>
              <h2 className="dash-card-title">Report Categories</h2>
              {summary.report_categories.length > 0 ? (
                <div className="chart-box">
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={summary.report_categories}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.08)" />
                      <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" name="Reports" fill="#06B6D4" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>
                  Upload medical reports to view category summaries.
                </p>
              )}
            </GlassCard>
          </div>
        </>
      )}

      {/* Educational Tips */}
      <GlassCard style={{ marginTop: 22 }}>
        <h2 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Lightbulb size={19} color="var(--color-primary)" /> Educational Health Notes
        </h2>
        <div className="insights-tips-list">
          {summary.educational_guidance.map((tip, i) => (
            <div key={i} className="insights-tip-item glass-surface--subtle">
              <Activity size={17} color="var(--color-secondary)" />
              <span>{tip}</span>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  Bell,
  Bot,
  Building2,
  CalendarCheck,
  Clock,
  FileText,
  MessageSquare,
  RefreshCw,
  Stethoscope,
  UserCheck,
} from 'lucide-react';
import { healthService } from '../../services/healthService';
import { extractApiError } from '../../services/apiClient';
import {
  EmptyState,
  GlassCard,
  LoadingSpinner,
  PageHeader,
} from '../../components/common/CommonUI';
import { formatDate, formatDateTime, formatUrgencyLabel } from '../../utils/formatters';
import './DashboardPage.css';

export function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadSummary = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await healthService.getDashboardSummary();
      setSummary(data);
    } catch (err) {
      setError(extractApiError(err, 'Failed to load dashboard summary'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Loading your personal health dashboard..." />;
  }

  if (error) {
    return (
      <GlassCard>
        <div className="alert alert--error" style={{ marginBottom: 16 }}>
          {error}
        </div>
        <button type="button" className="btn btn--primary" onClick={loadSummary}>
          <RefreshCw size={16} /> Retry
        </button>
      </GlassCard>
    );
  }

  const { user, stats, recent_assessments, recent_reports, recent_activities, ai_status, notifications } =
    summary;

  return (
    <div className="dashboard-page animate-fade-up">
      <PageHeader
        badge={
          <span className={`badge ${ai_status.available ? 'badge--success' : 'badge--warning'}`}>
            <Bot size={14} />
            Local AI: {ai_status.available ? `Online (${ai_status.provider})` : 'Offline'}
          </span>
        }
        title={`Welcome back, ${user.full_name}`}
        subtitle="Your live overview pulled directly from your personal PostgreSQL health records."
        actions={
          <>
            <Link to="/symptom-analysis" className="btn btn--primary btn--sm">
              <Stethoscope size={16} /> New Assessment
            </Link>
            <Link to="/medical-reports" className="btn btn--glass btn--sm">
              <FileText size={16} /> Upload Report
            </Link>
          </>
        }
      />

      {/* Metrics Grid */}
      <div className="dash-stats-grid">
        <GlassCard interactive className="dash-stat-card">
          <div className="dash-stat-card__icon dash-stat-card__icon--red">
            <Stethoscope size={22} />
          </div>
          <div>
            <div className="dash-stat-card__value">{stats.total_assessments}</div>
            <div className="dash-stat-card__label">Symptom Assessments</div>
          </div>
        </GlassCard>

        <GlassCard interactive className="dash-stat-card">
          <div className="dash-stat-card__icon dash-stat-card__icon--blue">
            <FileText size={22} />
          </div>
          <div>
            <div className="dash-stat-card__value">{stats.total_reports}</div>
            <div className="dash-stat-card__label">Medical Reports</div>
          </div>
        </GlassCard>

        <GlassCard interactive className="dash-stat-card">
          <div className="dash-stat-card__icon dash-stat-card__icon--cyan">
            <MessageSquare size={22} />
          </div>
          <div>
            <div className="dash-stat-card__value">{stats.total_conversations}</div>
            <div className="dash-stat-card__label">AI Conversations</div>
          </div>
        </GlassCard>

        <GlassCard interactive className="dash-stat-card">
          <div className="dash-stat-card__icon dash-stat-card__icon--indigo">
            <Activity size={22} />
          </div>
          <div>
            <div className="dash-stat-card__value">{stats.total_activities}</div>
            <div className="dash-stat-card__label">Health Activities</div>
          </div>
        </GlassCard>
      </div>

      {/* Main Content Grid */}
      <div className="dash-main-grid">
        {/* Left Column */}
        <div className="dash-col">
          {/* Quick Actions */}
          <GlassCard>
            <h2 className="dash-card-title">Quick Actions</h2>
            <div className="dash-quick-grid">
              <Link to="/hospitals" className="dash-quick-item glass-surface--subtle">
                <Building2 size={20} color="var(--color-primary)" />
                <span>Explore Hospitals</span>
                <ArrowRight size={15} />
              </Link>
              <Link to="/appointments" className="dash-quick-item glass-surface--subtle">
                <CalendarCheck size={20} color="var(--color-accent)" />
                <span>Book Appointment</span>
                <ArrowRight size={15} />
              </Link>
              <Link to="/symptom-analysis" className="dash-quick-item glass-surface--subtle">
                <Stethoscope size={20} color="var(--color-accent)" />
                <span>Analyze Symptoms</span>
                <ArrowRight size={15} />
              </Link>
              <Link to="/chat" className="dash-quick-item glass-surface--subtle">
                <MessageSquare size={20} color="var(--color-cyan)" />
                <span>Open AI Chat</span>
                <ArrowRight size={15} />
              </Link>
              <Link to="/medical-reports" className="dash-quick-item glass-surface--subtle">
                <FileText size={20} color="var(--color-primary)" />
                <span>Manage Reports</span>
                <ArrowRight size={15} />
              </Link>
              <Link to="/health-insights" className="dash-quick-item glass-surface--subtle">
                <Activity size={20} color="var(--color-success)" />
                <span>View Insights</span>
                <ArrowRight size={15} />
              </Link>
            </div>
          </GlassCard>

          {/* Recent Assessments & Reports */}
          <GlassCard>
            <div className="dash-card-head">
              <h2 className="dash-card-title">Recent Health Records</h2>
              <Link to="/health-history" className="auth-link">
                View All
              </Link>
            </div>

            {recent_assessments.length === 0 && recent_reports.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="No health records logged yet"
                description="Run a symptom assessment or upload a medical report to see your records here."
                action={
                  <Link to="/symptom-analysis" className="btn btn--primary btn--sm">
                    Start First Assessment
                  </Link>
                }
              />
            ) : (
              <div className="dash-record-list">
                {recent_assessments.map((a) => (
                  <div key={a.id} className="dash-record-row">
                    <div>
                      <div className="dash-record-row__title">
                        {a.symptoms.slice(0, 3).join(', ')}
                        {a.symptoms.length > 3 ? ` (+${a.symptoms.length - 3})` : ''}
                      </div>
                      <div className="dash-record-row__meta">
                        Symptom Assessment · {formatDateTime(a.created_at)}
                      </div>
                    </div>
                    <span
                      className={`badge ${
                        a.urgency_level === 'urgent_emergency'
                          ? 'badge--danger'
                          : a.urgency_level === 'prompt_care'
                          ? 'badge--warning'
                          : 'badge--success'
                      }`}
                    >
                      {formatUrgencyLabel(a.urgency_level)}
                    </span>
                  </div>
                ))}

                {recent_reports.map((r) => (
                  <div key={r.id} className="dash-record-row">
                    <div>
                      <div className="dash-record-row__title">{r.original_filename}</div>
                      <div className="dash-record-row__meta">
                        {r.category} · {formatDateTime(r.created_at)}
                      </div>
                    </div>
                    <span className="badge badge--primary">{r.processing_status}</span>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>

        {/* Right Column */}
        <div className="dash-col">
          {/* Profile Summary */}
          <GlassCard>
            <div className="dash-card-head">
              <h2 className="dash-card-title">Profile Summary</h2>
              <Link to="/profile" className="auth-link">
                Edit
              </Link>
            </div>
            <div className="dash-profile-box">
              <div className="dash-profile-row">
                <UserCheck size={17} color="var(--color-primary)" />
                <span>{user.full_name}</span>
              </div>
              <div className="dash-profile-meta">Email: {user.email}</div>
              <div className="dash-profile-meta">
                Blood Group: {user.blood_group || 'Not set'}
              </div>
              <div className="dash-profile-meta">
                Member Since: {formatDate(user.created_at)}
              </div>
            </div>
          </GlassCard>

          {/* Notifications */}
          {notifications.length > 0 && (
            <GlassCard>
              <h2 className="dash-card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Bell size={18} color="var(--color-primary)" /> Notifications
              </h2>
              <div className="dash-notif-list">
                {notifications.map((n) => (
                  <div
                    key={n.id}
                    className={`alert ${n.severity === 'warning' ? 'alert--warning' : 'alert--info'}`}
                    style={{ flexDirection: 'column', gap: 6 }}
                  >
                    <strong>{n.title}</strong>
                    <span>{n.message}</span>
                    {n.action_route && (
                      <Link to={n.action_route} className="auth-link" style={{ fontSize: '0.84rem' }}>
                        Open &rarr;
                      </Link>
                    )}
                  </div>
                ))}
              </div>
            </GlassCard>
          )}

          {/* Recent Activities */}
          <GlassCard>
            <div className="dash-card-head">
              <h2 className="dash-card-title">Recent Activity</h2>
              <Clock size={17} color="var(--text-muted)" />
            </div>
            {recent_activities.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', margin: 0 }}>No recent activity yet.</p>
            ) : (
              <div className="dash-activity-list">
                {recent_activities.map((act) => (
                  <div key={act.id} className="dash-activity-item">
                    <span className="dash-activity-dot" />
                    <div>
                      <div className="dash-activity-title">{act.title}</div>
                      <div className="dash-activity-time">{formatDateTime(act.created_at)}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bell, CheckCheck } from 'lucide-react';
import { healthcareService } from '../../services/healthcareService';
import { extractApiError } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import {
  EmptyState,
  GlassCard,
  LoadingSpinner,
  PageHeader,
} from '../../components/common/CommonUI';
import { formatDateTime } from '../../utils/formatters';

export function NotificationsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await healthcareService.listNotifications();
      setItems(data);
    } catch (err) {
      showToast(extractApiError(err, 'Failed to load notifications'), 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const handleMarkRead = async (id) => {
    try {
      const updated = await healthcareService.markNotificationRead(id);
      setItems((prev) => prev.map((n) => (n.id === id ? updated : n)));
    } catch (err) {
      showToast(extractApiError(err), 'error');
    }
  };

  const handleMarkAll = async () => {
    try {
      await healthcareService.markAllNotificationsRead();
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      showToast('All notifications marked as read', 'success');
    } catch (err) {
      showToast(extractApiError(err), 'error');
    }
  };

  return (
    <div className="animate-fade-up">
      <PageHeader
        badge={<span className="badge badge--primary">Live Alerts</span>}
        title="Notifications"
        subtitle="Track booking confirmations, schedule changes, and shared consultation notes."
        actions={
          items.some((n) => !n.is_read) && (
            <button type="button" className="btn btn--glass btn--sm" onClick={handleMarkAll}>
              <CheckCheck size={15} /> Mark All Read
            </button>
          )
        }
      />

      {loading ? (
        <LoadingSpinner label="Loading notifications..." />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="No notifications yet"
          description="Appointment updates and consultation notifications will appear here automatically."
        />
      ) : (
        <GlassCard>
          <div className="dash-record-list">
            {items.map((n) => (
              <div
                key={n.id}
                className="symptom-history-item glass-surface--subtle"
                style={{
                  borderLeft: n.is_read
                    ? '3px solid transparent'
                    : '4px solid var(--color-secondary)',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <strong>{n.title}</strong>
                    {!n.is_read && <span className="badge badge--cyan">New</span>}
                  </div>
                  <p style={{ margin: '4px 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    {n.message}
                  </p>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {formatDateTime(n.created_at)}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                  {n.related_route && (
                    <Link to={n.related_route} className="btn btn--glass btn--sm">
                      Open
                    </Link>
                  )}
                  {!n.is_read && (
                    <button
                      type="button"
                      className="btn btn--primary btn--sm"
                      onClick={() => handleMarkRead(n.id)}
                    >
                      Mark Read
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  );
}

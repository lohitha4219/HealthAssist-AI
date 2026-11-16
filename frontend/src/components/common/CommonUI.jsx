import { Component } from 'react';
import { Loader2, X } from 'lucide-react';
import './CommonUI.css';

export function GlassCard({ children, className = '', interactive = false, padding = '24px', ...props }) {
  return (
    <div
      className={`glass-card ${interactive ? 'glass-card--interactive' : ''} ${className}`}
      style={{ padding, ...props.style }}
      {...props}
    >
      {children}
    </div>
  );
}

export function PageHeader({ title, subtitle, badge, actions }) {
  return (
    <div className="page-header">
      <div>
        {badge && <div className="page-header__badge">{badge}</div>}
        <h1 className="page-header__title">{title}</h1>
        {subtitle && <p className="page-header__subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
    </div>
  );
}

export function LoadingSpinner({ label = 'Loading...', fullScreen = false }) {
  return (
    <div className={`loading-state ${fullScreen ? 'loading-state--full' : ''}`} role="status">
      <Loader2 size={28} className="spin loading-state__icon" />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <GlassCard className="empty-state">
      {Icon && (
        <div className="empty-state__icon">
          <Icon size={28} />
        </div>
      )}
      <h3 className="empty-state__title">{title}</h3>
      <p className="empty-state__desc">{description}</p>
      {action && <div className="empty-state__action">{action}</div>}
    </GlassCard>
  );
}

export function Modal({ open, title, onClose, children, width = '640px' }) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={title} onClick={onClose}>
      <div
        className="modal-card glass-surface--strong animate-fade-up"
        style={{ maxWidth: width }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-card__header">
          <h2 className="modal-card__title">{title}</h2>
          <button type="button" className="modal-card__close" aria-label="Close modal" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="modal-card__body">{children}</div>
      </div>
    </div>
  );
}

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || 'Unexpected render error' };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="container" style={{ paddingBlock: 64 }}>
          <GlassCard>
            <h2 style={{ marginTop: 0 }}>Something went wrong</h2>
            <p style={{ color: 'var(--text-muted)' }}>{this.state.message}</p>
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => window.location.reload()}
            >
              Reload Application
            </button>
          </GlassCard>
        </div>
      );
    }
    return this.props.children;
  }
}

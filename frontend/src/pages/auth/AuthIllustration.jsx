import { Activity, Lock, ShieldCheck } from 'lucide-react';

export function AuthSidePanel({ title, description }) {
  return (
    <div className="auth-hero-panel glass-surface animate-fade-up">
      <div className="auth-hero-illustration" aria-hidden="true">
        <svg viewBox="0 0 360 220" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="authPanelGrad" x1="20" y1="10" x2="340" y2="210" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#0B4F8A" stopOpacity="0.16" />
              <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.22" />
            </linearGradient>
            <linearGradient id="authStrokeGrad" x1="40" y1="110" x2="310" y2="110" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#0B4F8A" />
              <stop offset="55%" stopColor="#0EA5E9" />
              <stop offset="100%" stopColor="#E11D48" />
            </linearGradient>
          </defs>
          <rect x="8" y="8" width="344" height="204" rx="26" fill="url(#authPanelGrad)" stroke="rgba(255,255,255,0.85)" strokeWidth="2" />
          <circle cx="84" cy="70" r="32" fill="rgba(14, 165, 233, 0.16)" />
          <circle cx="288" cy="154" r="38" fill="rgba(225, 29, 72, 0.11)" />
          <rect x="44" y="54" width="272" height="112" rx="18" fill="rgba(255,255,255,0.78)" stroke="rgba(11,79,138,0.12)" />
          <path
            d="M66 112 H116 L132 82 L152 142 L170 96 L186 122 L202 112 H294"
            stroke="url(#authStrokeGrad)"
            strokeWidth="4.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle cx="272" cy="76" r="14" fill="#E11D48" fillOpacity="0.14" />
          <path d="M272 70 V82 M266 76 H278" stroke="#E11D48" strokeWidth="2.8" strokeLinecap="round" />
        </svg>
      </div>

      <span className="badge badge--cyan" style={{ alignSelf: 'flex-start' }}>
        <Activity size={14} /> HealthAssist AI
      </span>

      <h2 className="auth-hero-title">{title}</h2>
      <p className="auth-hero-desc">{description}</p>

      <div className="auth-hero-pills">
        <div className="auth-hero-pill">
          <ShieldCheck size={17} color="var(--color-primary)" />
          <span>Salted bcrypt password hashing &amp; JWT protection</span>
        </div>
        <div className="auth-hero-pill">
          <Lock size={17} color="var(--color-secondary)" />
          <span>Strict per-user health record isolation in PostgreSQL</span>
        </div>
      </div>
    </div>
  );
}

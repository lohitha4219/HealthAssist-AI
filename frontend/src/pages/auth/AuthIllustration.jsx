import { CheckCircle2, HeartPulse, Lock, ShieldCheck, Sparkles, UserCheck } from 'lucide-react';

export function AuthSidePanel({ title, description }) {
  return (
    <div className="auth-hero-panel glass-surface animate-fade-up">
      <div className="auth-hero-illustration" aria-hidden="true">
        <svg viewBox="0 0 380 200" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="authPanelGrad" x1="20" y1="10" x2="360" y2="190" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#0B4F8A" stopOpacity="0.12" />
              <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.18" />
            </linearGradient>
            <linearGradient id="authStrokeGrad" x1="40" y1="100" x2="340" y2="100" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#0B4F8A" />
              <stop offset="50%" stopColor="#0EA5E9" />
              <stop offset="100%" stopColor="#E11D48" />
            </linearGradient>
            <filter id="softGlow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#0EA5E9" floodOpacity="0.25" />
            </filter>
          </defs>
          <rect x="6" y="6" width="368" height="188" rx="24" fill="url(#authPanelGrad)" stroke="rgba(255,255,255,0.9)" strokeWidth="2" />
          <circle cx="84" cy="60" r="36" fill="rgba(14, 165, 233, 0.12)" />
          <circle cx="310" cy="144" r="42" fill="rgba(225, 29, 72, 0.08)" />
          <rect x="36" y="44" width="308" height="112" rx="16" fill="rgba(255,255,255,0.85)" stroke="rgba(11,79,138,0.12)" filter="url(#softGlow)" />
          {/* ECG Medical Heartbeat Curve */}
          <path
            d="M56 100 H112 L128 72 L146 128 L164 86 L180 110 L196 100 H324"
            stroke="url(#authStrokeGrad)"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Clinical Cross Icon */}
          <circle cx="296" cy="68" r="14" fill="#E11D48" fillOpacity="0.14" />
          <path d="M296 62 V74 M290 68 H302" stroke="#E11D48" strokeWidth="2.8" strokeLinecap="round" />
        </svg>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="badge badge--cyan">
          <Sparkles size={13} /> Clinical AI Ready
        </span>
        <span className="badge badge--primary">
          <UserCheck size={13} /> 50+ Verified AP Doctors
        </span>
      </div>

      <h2 className="auth-hero-title">{title}</h2>
      <p className="auth-hero-desc">{description}</p>

      <div className="auth-hero-pills">
        <div className="auth-hero-pill">
          <ShieldCheck size={18} color="var(--color-primary)" />
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Bcrypt &amp; JWT Protected</div>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Enterprise security standards for patient health records</div>
          </div>
        </div>

        <div className="auth-hero-pill">
          <Lock size={18} color="var(--color-secondary)" />
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Strict Data Isolation</div>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Per-user PostgreSQL separation &amp; encrypted storage</div>
          </div>
        </div>

        <div className="auth-hero-pill">
          <CheckCircle2 size={18} color="var(--color-success)" />
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Verified Andhra Pradesh Care</div>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Direct booking with government &amp; multispecialty hospitals</div>
          </div>
        </div>
      </div>
    </div>
  );
}

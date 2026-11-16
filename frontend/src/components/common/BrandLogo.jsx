export function BrandLogo({ size = 36, showText = true }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="brandGrad" x1="8" y1="6" x2="56" y2="58" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0B4F8A" />
            <stop offset="100%" stopColor="#06B6D4" />
          </linearGradient>
        </defs>
        <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#brandGrad)" />
        <path
          d="M15 34h9l4-11 7 21 5-13 4 3h5"
          stroke="#FFFFFF"
          strokeWidth="4.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="48" cy="18" r="5" fill="#F43F5E" />
      </svg>
      {showText && (
        <span style={{ display: 'inline-flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <span
            style={{
              fontWeight: 800,
              fontSize: '1.08rem',
              letterSpacing: '-0.02em',
              color: 'var(--color-primary-deep)',
            }}
          >
            HealthAssist <span style={{ color: 'var(--color-accent)' }}>AI</span>
          </span>
        </span>
      )}
    </span>
  );
}

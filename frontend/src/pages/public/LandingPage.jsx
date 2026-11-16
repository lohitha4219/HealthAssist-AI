import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Activity,
  AlertCircle,
  ArrowRight,
  Bell,
  Building2,
  CalendarCheck,
  CheckCircle2,
  Clock,
  FileText,
  HeartPulse,
  Info,
  LayoutDashboard,
  Loader2,
  Lock,
  Mail,
  MapPin,
  MessageSquare,
  Phone,
  Send,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UserCheck,
} from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { Footer } from '../../components/layout/Footer';
import { GlassCard } from '../../components/common/CommonUI';
import { useScrollReveal } from '../../hooks/useScrollReveal';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { healthcareService } from '../../services/healthcareService';
import { extractApiError } from '../../services/apiClient';
import { isValidEmail } from '../../utils/validators';
import './LandingPage.css';

const FEATURES = [
  {
    title: 'AI Healthcare Chatbot',
    description:
      'Ask healthcare education, symptom triage questions, or report terminology with persistent conversation history.',
    icon: MessageSquare,
    to: '/chat',
    accent: 'cyan',
  },
  {
    title: 'Symptom Analysis',
    description:
      'Log multiple symptoms, duration, and severity for structured educational triage and emergency warning alerts.',
    icon: Stethoscope,
    to: '/symptom-analysis',
    accent: 'accent',
  },
  {
    title: 'Medical Report Analysis',
    description:
      'Upload PDF or image reports, extract text, inspect observed lab values against reference ranges, and store records securely.',
    icon: FileText,
    to: '/medical-reports',
    accent: 'primary',
  },
  {
    title: 'Hospital Discovery',
    description:
      'Browse verified hospitals across Andhra Pradesh by district, city, specialty, treatment, and facilities.',
    icon: Building2,
    to: '/hospitals',
    accent: 'primary',
  },
  {
    title: 'Doctor Discovery',
    description:
      'Search verified doctors by specialty, hospital affiliation, city, district, and live schedule availability.',
    icon: UserCheck,
    to: '/doctors',
    accent: 'cyan',
  },
  {
    title: 'Online Appointment Booking',
    description:
      'Pick a hospital, select a verified doctor, choose an open time slot, and track real-time status transitions.',
    icon: CalendarCheck,
    to: '/appointments',
    accent: 'accent',
  },
  {
    title: 'Patient Dashboard',
    description:
      'Centralized overview of upcoming appointments, recent medical reports, assessments, and recent activities.',
    icon: LayoutDashboard,
    to: '/dashboard',
    accent: 'primary',
  },
  {
    title: 'Doctor Dashboard',
    description:
      'Dedicated portal for verified doctors to manage appointment requests, schedules, and clinical consultation notes.',
    icon: HeartPulse,
    to: '/doctor/dashboard',
    accent: 'cyan',
  },
  {
    title: 'Medical History',
    description:
      'Searchable, filterable chronological timeline of your symptom assessments, uploaded reports, and bookings.',
    icon: Clock,
    to: '/health-history',
    accent: 'primary',
  },
  {
    title: 'Treatment Precautions',
    description:
      'Specialty guides covering preparation, precautions, aftercare, consultation cues, and emergency signs.',
    icon: ShieldCheck,
    to: '/treatments',
    accent: 'cyan',
  },
  {
    title: 'Appointment Notifications',
    description:
      'Real PostgreSQL-backed alerts whenever an appointment is booked, confirmed, declined, or rescheduled.',
    icon: Bell,
    to: '/notifications',
    accent: 'accent',
  },
  {
    title: 'Health Insights',
    description:
      'Charts and trend visualizations built strictly from your actual stored records with zero fabricated data.',
    icon: Activity,
    to: '/health-insights',
    accent: 'primary',
  },
];

const WORKFLOW_STEPS = [
  'Register or log in to your Patient or Doctor account',
  'Complete your personal patient profile & emergency contact',
  'Search verified hospitals across Andhra Pradesh districts',
  'Explore verified doctors and clinical departments',
  'Select a doctor and review consultation details',
  'Check real available dates and open time slots',
  'Book an appointment with race-condition protection',
  'Use the AI healthcare chatbot for educational guidance',
  'Upload medical reports for extraction & lab parsing',
  'Track health records, notes, and appointment updates',
];

function RevealSection({ id, className = '', children }) {
  const { ref, isVisible } = useScrollReveal();
  return (
    <section
      id={id}
      ref={ref}
      className={`landing-section reveal-block ${isVisible ? 'is-visible' : ''} ${className}`}
    >
      {children}
    </section>
  );
}

export function LandingPage() {
  const location = useLocation();
  const { isAuthenticated, user } = useAuth();
  const { showToast } = useToast();

  const [overview, setOverview] = useState(null);

  const [contactForm, setContactForm] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [sendingContact, setSendingContact] = useState(false);
  const [contactResult, setContactResult] = useState(null);

  const portalRoute = user?.role === 'doctor' ? '/doctor/dashboard' : '/dashboard';

  useEffect(() => {
    let active = true;
    healthcareService
      .getPublicOverview()
      .then((data) => {
        if (active) setOverview(data);
      })
      .catch(() => {
        // Fallback silently if offline
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (location.hash) {
      const target = document.getElementById(location.hash.replace('#', ''));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, [location.hash]);

  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    else if (id === 'hero') window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    setContactResult(null);

    const name = contactForm.name.trim();
    const email = contactForm.email.trim();
    const subject = contactForm.subject.trim();
    const message = contactForm.message.trim();

    if (name.length < 2) {
      showToast('Please enter your full name (at least 2 characters)', 'error');
      return;
    }
    if (!isValidEmail(email)) {
      showToast('Please enter a valid email address', 'error');
      return;
    }
    if (subject.length < 3) {
      showToast('Please provide a subject (at least 3 characters)', 'error');
      return;
    }
    if (message.length < 10) {
      showToast('Please write a message with at least 10 characters', 'error');
      return;
    }

    setSendingContact(true);
    try {
      const res = await healthcareService.submitContactEnquiry({
        name,
        email,
        subject,
        message,
      });

      if (res.email_delivered) {
        setContactResult({
          type: 'success',
          message:
            res.message ||
            `Thank you, ${name}! Your enquiry has been delivered successfully to our support team at nslohitha2924@gmail.com.`,
        });
        showToast('Enquiry sent to support successfully', 'success');
      } else {
        setContactResult({
          type: 'info',
          message:
            res.message ||
            'Your enquiry has been saved to our database. (Email delivery is awaiting SMTP credentials in backend/.env).',
        });
        showToast('Enquiry saved to database', 'info');
      }

      setContactForm({ name: '', email: '', subject: '', message: '' });
    } catch (err) {
      const errorMsg = extractApiError(
        err,
        'Unable to submit enquiry. Please check your network connection.'
      );
      setContactResult({
        type: 'error',
        message: errorMsg,
      });
      showToast(errorMsg, 'error');
    } finally {
      setSendingContact(false);
    }
  };

  const supportEmail = overview?.support?.email || 'nslohitha2924@gmail.com';
  const supportPhone = overview?.support?.phone?.trim();
  const supportAddress = overview?.support?.address?.trim();

  return (
    <div className="landing-page">
      <div className="landing-bg-orb landing-bg-orb--one" aria-hidden="true" />
      <div className="landing-bg-orb landing-bg-orb--two" aria-hidden="true" />

      <PublicNavbar />

      <main>
        {/* HERO SECTION */}
        <section id="hero" className="hero-section">
          <div className="container hero-grid">
            <div className="hero-copy animate-fade-up">
              <div className="hero-eyebrow badge badge--primary">
                <Sparkles size={14} /> Patient &amp; Doctor Healthcare Platform
              </div>

              <h1 className="hero-title">
                Your Health, <span className="gradient-text">Our Intelligence.</span>
              </h1>

              <p className="hero-subtitle">
                Experience smarter healthcare with AI-powered health assistance, medical report
                analysis, expert doctors, and convenient hospital appointments.
              </p>

              <div className="hero-actions">
                <Link
                  to={isAuthenticated ? portalRoute : '/register'}
                  className="btn btn--primary btn--lg"
                >
                  {isAuthenticated ? 'Open Your Portal' : 'Get Started'}{' '}
                  <ArrowRight size={18} />
                </Link>
                <button
                  type="button"
                  onClick={() => scrollToSection('features')}
                  className="btn btn--glass btn--lg"
                >
                  Explore Features <ArrowRight size={16} />
                </button>
              </div>

              <div className="hero-trust-row">
                <span className="hero-trust-pill">
                  <ShieldCheck size={16} /> Role-Enforced Portals
                </span>
                <span className="hero-trust-pill">
                  <Lock size={16} /> PostgreSQL Persistence
                </span>
                <Link to="/treatments" className="hero-trust-pill">
                  <HeartPulse size={16} /> Treatment Precautions
                </Link>
              </div>
            </div>

            <div className="hero-visual animate-fade-up">
              <div className="hero-preview-shell glass-surface--strong">
                <div className="hero-preview-topbar">
                  <div className="hero-dots">
                    <span />
                    <span />
                    <span />
                  </div>
                  <span className="badge badge--cyan">Live Platform Modules</span>
                </div>

                <div className="hero-preview-grid">
                  <Link to="/chat" className="hero-preview-tile glass-surface--subtle">
                    <div className="hero-preview-icon hero-preview-icon--blue">
                      <MessageSquare size={20} />
                    </div>
                    <div>
                      <div className="hero-preview-label">AI Healthcare Assistant</div>
                      <div className="hero-preview-text">
                        Instant health education, terminology explanations &amp; triage guidance
                      </div>
                    </div>
                  </Link>

                  <Link to="/symptom-analysis" className="hero-preview-tile glass-surface--subtle">
                    <div className="hero-preview-icon hero-preview-icon--cyan">
                      <Stethoscope size={20} />
                    </div>
                    <div>
                      <div className="hero-preview-label">Structured Symptom Analysis</div>
                      <div className="hero-preview-text">
                        Multi-symptom triage with emergency red-flag indicators
                      </div>
                    </div>
                  </Link>

                  <Link to="/medical-reports" className="hero-preview-tile glass-surface--subtle">
                    <div className="hero-preview-icon hero-preview-icon--red">
                      <FileText size={20} />
                    </div>
                    <div>
                      <div className="hero-preview-label">Medical Report Lab Parsing</div>
                      <div className="hero-preview-text">
                        Secure PDF &amp; image vault with observed value extraction
                      </div>
                    </div>
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Real Database-Backed Statistics Strip */}
          {overview && (
            <div className="container" style={{ marginTop: 34 }}>
              <div className="stats-strip glass-surface">
                <div className="stats-strip__item">
                  <strong>{overview.stats.verified_hospitals}</strong>
                  <span>Verified Hospitals</span>
                </div>
                <div className="stats-strip__item">
                  <strong>{overview.stats.departments}</strong>
                  <span>Hospital Departments</span>
                </div>
                <div className="stats-strip__item">
                  <strong>{overview.stats.specialties}</strong>
                  <span>Treatment Guides</span>
                </div>
                <div className="stats-strip__item">
                  <strong>{overview.stats.verified_doctors}</strong>
                  <span>Verified Doctors</span>
                </div>
                <div className="stats-strip__item">
                  <strong>{overview.stats.appointments}</strong>
                  <span>Appointments Logged</span>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* ABOUT US */}
        <RevealSection id="about">
          <div className="container about-grid">
            <GlassCard className="about-card" padding="32px">
              <span className="badge badge--accent">About Us</span>
              <h2 className="about-card__title">
                Connecting Patients, Verified Hospitals, Doctors &amp; Responsible AI
              </h2>
              <p className="about-card__text">
                <strong>What the platform does:</strong> HealthAssist AI unifies hospital discovery
                across Andhra Pradesh, verified doctor scheduling, appointment tracking, medical
                report parsing, symptom triage education, and AI-assisted Q&amp;A in one platform.
              </p>
              <p className="about-card__text">
                <strong>Why it was developed:</strong> Patients often struggle to verify hospital
                departments, organize scattered lab reports, and prepare questions before a visit.
                HealthAssist AI structures those records cleanly without inventing clinical claims.
              </p>
              <p className="about-card__text">
                <strong>How AI helps patients:</strong> The AI assistant explains medical terminology,
                summarizes extracted report text, answers general health education questions, and
                flags urgent warning signs so patients seek timely care.
              </p>
            </GlassCard>

            <GlassCard className="why-card" padding="32px">
              <span className="badge badge--primary">Two Dedicated Portals</span>
              <h2 className="about-card__title">Built for Patients and Verified Doctors</h2>
              <div className="why-list">
                <div className="why-item">
                  <UserCheck size={20} className="why-item__icon" />
                  <div>
                    <h4 className="why-item__title">Patient Portal</h4>
                    <p className="why-item__desc">
                      Patients search hospitals and doctors, book real available slots, upload lab
                      PDFs/images, review shareable consultation notes, and track health history.
                    </p>
                  </div>
                </div>
                <div className="why-item">
                  <Stethoscope size={20} className="why-item__icon" />
                  <div>
                    <h4 className="why-item__title">Doctor Portal</h4>
                    <p className="why-item__desc">
                      Credential-verified doctors configure working hours and leave dates, confirm
                      or reschedule requests, inspect authorized shared reports, and record notes.
                    </p>
                  </div>
                </div>
                <div className="why-item">
                  <ShieldCheck size={20} className="why-item__icon" />
                  <div>
                    <h4 className="why-item__title">Educational &amp; Privacy Guardrails</h4>
                    <p className="why-item__desc">
                      All patient data is isolated per account via JWT authorization; AI outputs are
                      strictly educational and never replace a licensed physician&apos;s diagnosis.
                    </p>
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>
        </RevealSection>

        {/* 12 FEATURES */}
        <RevealSection id="features">
          <div className="container">
            <div className="section-heading">
              <span className="badge badge--cyan">Platform Features</span>
              <h2>Twelve Integrated Healthcare Capabilities</h2>
              <p>Every feature connects directly to PostgreSQL and role-enforced FastAPI endpoints.</p>
            </div>

            <div className="features-grid">
              {FEATURES.map((feat) => {
                const Icon = feat.icon;
                return (
                  <Link key={feat.title} to={feat.to} className="feature-link-wrap">
                    <GlassCard interactive className="feature-card">
                      <div className={`feature-card__icon feature-card__icon--${feat.accent}`}>
                        <Icon size={24} />
                      </div>
                      <h3 className="feature-card__title">{feat.title}</h3>
                      <p className="feature-card__desc">{feat.description}</p>
                      <span className="feature-card__cta">
                        Open Feature <ArrowRight size={15} />
                      </span>
                    </GlassCard>
                  </Link>
                );
              })}
            </div>
          </div>
        </RevealSection>

        {/* HOW IT WORKS (10 STEPS) */}
        <RevealSection id="how-it-works">
          <div className="container">
            <div className="section-heading">
              <span className="badge badge--primary">Step-By-Step Workflow</span>
              <h2>How HealthAssist AI Works</h2>
              <p>Ten clear steps from registration to appointment care and health tracking.</p>
            </div>

            <div className="workflow-grid">
              {WORKFLOW_STEPS.map((text, idx) => (
                <GlassCard key={text} className="workflow-card" padding="18px">
                  <div className="step-card__num">{String(idx + 1).padStart(2, '0')}</div>
                  <p className="step-card__desc" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {text}
                  </p>
                </GlassCard>
              ))}
            </div>
          </div>
        </RevealSection>

        {/* CONTACT SUPPORT SECTION (TWO-COLUMN RESPONSIVE LAYOUT) */}
        <RevealSection id="contact">
          <div className="container contact-section-wrap">
            <div className="section-heading" style={{ marginBottom: 28 }}>
              <span className="badge badge--cyan">Get In Touch</span>
              <h2>Contact Support</h2>
              <p>
                Have questions about HealthAssist AI or need assistance? Reach out to our support team
                directly.
              </p>
            </div>

            <div className="contact-grid">
              {/* Left Column: Contact Support Info & Healthcare Details */}
              <GlassCard className="contact-info-panel" padding="34px">
                <div className="contact-info-panel__header">
                  <span className="badge badge--primary">Support Information</span>
                  <h3 className="contact-info-panel__title">We Are Here to Help</h3>
                  <p className="contact-info-panel__desc">
                    Whether you have questions regarding your patient account, verified doctor
                    appointments, or platform features, our team is ready to assist you.
                  </p>
                </div>

                <div className="contact-channels">
                  <a
                    href={`mailto:${supportEmail}`}
                    className="contact-channel-item"
                    aria-label={`Send email to ${supportEmail}`}
                  >
                    <div className="contact-channel-item__icon contact-channel-item__icon--mail">
                      <Mail size={18} />
                    </div>
                    <div>
                      <div className="contact-channel-item__label">Direct Support Email</div>
                      <div className="contact-channel-item__value">{supportEmail}</div>
                    </div>
                  </a>

                  {supportPhone && (
                    <a
                      href={`tel:${supportPhone}`}
                      className="contact-channel-item"
                      aria-label={`Call support phone ${supportPhone}`}
                    >
                      <div className="contact-channel-item__icon contact-channel-item__icon--phone">
                        <Phone size={18} />
                      </div>
                      <div>
                        <div className="contact-channel-item__label">Official Support Phone</div>
                        <div className="contact-channel-item__value">{supportPhone}</div>
                      </div>
                    </a>
                  )}

                  {supportAddress && (
                    <div className="contact-channel-item">
                      <div className="contact-channel-item__icon contact-channel-item__icon--location">
                        <MapPin size={18} />
                      </div>
                      <div>
                        <div className="contact-channel-item__label">Support Center</div>
                        <div className="contact-channel-item__value">{supportAddress}</div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="contact-advisory-box">
                  <div className="contact-advisory-box__header">
                    <HeartPulse size={18} className="text-red" />
                    <strong>Emergency Advisory</strong>
                  </div>
                  <p className="contact-advisory-box__text">
                    HealthAssist AI is an educational platform. For life-threatening symptoms, chest
                    pain, or severe trauma, please dial <strong>108</strong> or <strong>112</strong> immediately.
                  </p>
                </div>

                <div className="contact-security-pill">
                  <ShieldCheck size={16} />
                  <span>Encrypted message storage &amp; role-isolated records.</span>
                </div>
              </GlassCard>

              {/* Right Column: Contact Enquiry Form */}
              <GlassCard className="contact-form-panel glass-surface--strong" padding="34px">
                <div style={{ marginBottom: 20 }}>
                  <h3 style={{ margin: '0 0 6px', fontSize: '1.25rem', color: 'var(--color-primary-deep)' }}>
                    Send an Enquiry
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                    Fill out the form below. Messages are sent directly to our support inbox.
                  </p>
                </div>

                {contactResult && (
                  <div
                    className={`contact-alert contact-alert--${contactResult.type} animate-fade-up`}
                    role="alert"
                  >
                    {contactResult.type === 'success' && <CheckCircle2 size={18} />}
                    {contactResult.type === 'info' && <Info size={18} />}
                    {contactResult.type === 'error' && <AlertCircle size={18} />}
                    <div style={{ fontSize: '0.88rem', lineHeight: 1.45 }}>{contactResult.message}</div>
                  </div>
                )}

                <form onSubmit={handleContactSubmit} className="contact-form" noValidate>
                  <div className="field-group">
                    <label htmlFor="contact-name" className="field-label">
                      Full Name <span style={{ color: 'var(--color-danger, #ef4444)' }}>*</span>
                    </label>
                    <input
                      id="contact-name"
                      type="text"
                      className="field-input"
                      placeholder="e.g. Lohitha N"
                      value={contactForm.name}
                      onChange={(e) => setContactForm((f) => ({ ...f, name: e.target.value }))}
                      disabled={sendingContact}
                      required
                    />
                  </div>

                  <div className="field-group">
                    <label htmlFor="contact-email" className="field-label">
                      Email Address <span style={{ color: 'var(--color-danger, #ef4444)' }}>*</span>
                    </label>
                    <input
                      id="contact-email"
                      type="email"
                      className="field-input"
                      placeholder="your.email@example.com"
                      value={contactForm.email}
                      onChange={(e) => setContactForm((f) => ({ ...f, email: e.target.value }))}
                      disabled={sendingContact}
                      required
                    />
                  </div>

                  <div className="field-group">
                    <label htmlFor="contact-subject" className="field-label">
                      Subject <span style={{ color: 'var(--color-danger, #ef4444)' }}>*</span>
                    </label>
                    <input
                      id="contact-subject"
                      type="text"
                      className="field-input"
                      placeholder="e.g. Appointment enquiry or hospital feedback"
                      value={contactForm.subject}
                      onChange={(e) => setContactForm((f) => ({ ...f, subject: e.target.value }))}
                      disabled={sendingContact}
                      required
                    />
                  </div>

                  <div className="field-group">
                    <label htmlFor="contact-message" className="field-label">
                      Message <span style={{ color: 'var(--color-danger, #ef4444)' }}>*</span>
                    </label>
                    <textarea
                      id="contact-message"
                      rows={4}
                      className="field-textarea"
                      placeholder="Please write your questions or details here (at least 10 characters)..."
                      value={contactForm.message}
                      onChange={(e) => setContactForm((f) => ({ ...f, message: e.target.value }))}
                      disabled={sendingContact}
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn btn--primary btn--lg contact-submit-btn"
                    disabled={sendingContact}
                  >
                    {sendingContact ? (
                      <>
                        <Loader2 size={18} className="spin" /> Sending Enquiry...
                      </>
                    ) : (
                      <>
                        <Send size={18} /> Submit Enquiry
                      </>
                    )}
                  </button>
                </form>
              </GlassCard>
            </div>
          </div>
        </RevealSection>
      </main>

      <Footer support={overview?.support} />
    </div>
  );
}

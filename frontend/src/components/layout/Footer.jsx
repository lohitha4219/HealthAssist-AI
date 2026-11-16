import { Mail, Phone } from 'lucide-react';
import { BrandLogo } from '../common/BrandLogo';
import './Footer.css';

export function Footer({ support }) {
  const currentYear = new Date().getFullYear();
  const contactEmail = support?.email || 'nslohitha2924@gmail.com';
  const contactPhone = support?.phone?.trim();

  return (
    <footer className="site-footer">
      <div className="container">
        <div className="site-footer__minimal glass-surface">
          <div className="site-footer__main">
            <div className="site-footer__brand-wrap">
              <BrandLogo size={32} />
              <p className="site-footer__tagline">
                Your intelligent healthcare companion for smarter health awareness and better access to healthcare services.
              </p>
            </div>

            <div className="site-footer__contact-row">
              <a
                href={`mailto:${contactEmail}`}
                className="site-footer__contact-link"
                aria-label={`Send email to ${contactEmail}`}
              >
                <span className="site-footer__icon-bubble">
                  <Mail size={16} />
                </span>
                <span>{contactEmail}</span>
              </a>

              {contactPhone && (
                <a
                  href={`tel:${contactPhone}`}
                  className="site-footer__contact-link"
                  aria-label={`Call support phone ${contactPhone}`}
                >
                  <span className="site-footer__icon-bubble">
                    <Phone size={16} />
                  </span>
                  <span>{contactPhone}</span>
                </a>
              )}
            </div>
          </div>

          <div className="site-footer__divider" />

          <div className="site-footer__legal-bar">
            <p className="site-footer__copyright">
              &copy; {currentYear} HealthAssist AI. All Rights Reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}

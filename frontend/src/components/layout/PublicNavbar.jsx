import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Menu, X, ArrowRight } from 'lucide-react';
import { BrandLogo } from '../common/BrandLogo';
import { useAuth } from '../../context/AuthContext';
import './PublicNavbar.css';

const SECTION_LINKS = [
  { label: 'Home', hash: 'hero', type: 'section' },
  { label: 'About Us', hash: 'about', type: 'section' },
  { label: 'Features', hash: 'features', type: 'section' },
  { label: 'How It Works', hash: 'how-it-works', type: 'section' },
  { label: 'Contact', hash: 'contact', type: 'section' },
];

export function PublicNavbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const portalPath = user?.role === 'doctor' ? '/doctor/dashboard' : '/dashboard';

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 18);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleSectionClick = (hash) => {
    setMenuOpen(false);
    if (location.pathname !== '/') {
      navigate(`/#${hash}`);
      return;
    }
    const el = document.getElementById(hash);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (hash === 'hero') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <header className={`pub-nav-wrap ${scrolled ? 'is-scrolled' : ''}`}>
      <div className="container">
        <nav className="pub-nav glass-surface" aria-label="Main navigation">
          <Link to="/" className="pub-nav__brand" onClick={() => setMenuOpen(false)}>
            <BrandLogo size={34} />
          </Link>

          <ul className="pub-nav__links">
            {SECTION_LINKS.map((item) => (
              <li key={item.label}>
                {item.type === 'route' ? (
                  <Link
                    to={item.to}
                    className={`pub-nav__link ${
                      location.pathname.startsWith(item.to) ? 'is-active' : ''
                    }`}
                  >
                    {item.label}
                  </Link>
                ) : (
                  <button
                    type="button"
                    className="pub-nav__link"
                    onClick={() => handleSectionClick(item.hash)}
                  >
                    {item.label}
                  </button>
                )}
              </li>
            ))}
          </ul>

          <div className="pub-nav__actions">
            {isAuthenticated ? (
              <Link to={portalPath} className="btn btn--primary btn--sm">
                Open Portal <ArrowRight size={15} />
              </Link>
            ) : (
              <>
                <Link to="/login" className="btn btn--ghost btn--sm">
                  Login
                </Link>
                <Link to="/register" className="btn btn--primary btn--sm">
                  Register <ArrowRight size={15} />
                </Link>
              </>
            )}
          </div>

          <button
            type="button"
            className="pub-nav__toggle"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((prev) => !prev)}
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </nav>

        {menuOpen && (
          <div className="pub-nav-mobile glass-surface--strong animate-fade-up">
            {SECTION_LINKS.map((item) =>
              item.type === 'route' ? (
                <Link
                  key={item.label}
                  to={item.to}
                  className="pub-nav-mobile__link"
                  onClick={() => setMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ) : (
                <button
                  key={item.label}
                  type="button"
                  className="pub-nav-mobile__link"
                  onClick={() => handleSectionClick(item.hash)}
                >
                  {item.label}
                </button>
              )
            )}
            <div className="pub-nav-mobile__actions">
              {isAuthenticated ? (
                <Link
                  to={portalPath}
                  className="btn btn--primary"
                  onClick={() => setMenuOpen(false)}
                >
                  Open Portal
                </Link>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="btn btn--glass"
                    onClick={() => setMenuOpen(false)}
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="btn btn--primary"
                    onClick={() => setMenuOpen(false)}
                  >
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

import { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Activity,
  Bell,
  Building2,
  CalendarCheck,
  CalendarClock,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Stethoscope,
  User,
  UserCheck,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { BrandLogo } from '../components/common/BrandLogo';
import './AuthenticatedLayout.css';

const PATIENT_SIDEBAR_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/hospitals', label: 'Hospitals', icon: Building2 },
  { to: '/doctors', label: 'Doctors', icon: UserCheck },
  { to: '/appointments', label: 'Appointments', icon: CalendarCheck },
  { to: '/symptom-analysis', label: 'Symptom Analysis', icon: Stethoscope },
  { to: '/chat', label: 'AI Chat', icon: MessageSquare },
  { to: '/medical-reports', label: 'Medical Reports', icon: FileText },
  { to: '/treatments', label: 'Treatments', icon: HeartPulse },
  { to: '/health-insights', label: 'Health Insights', icon: Activity },
  { to: '/health-history', label: 'Health History', icon: Clock },
  { to: '/notifications', label: 'Notifications', icon: Bell },
  { to: '/profile', label: 'Profile', icon: User },
];

const DOCTOR_SIDEBAR_ITEMS = [
  { to: '/doctor/dashboard', label: 'Doctor Dashboard', icon: LayoutDashboard },
  { to: '/doctor/appointments', label: 'Appointments', icon: CalendarCheck },
  { to: '/doctor/availability', label: 'Availability & Leave', icon: CalendarClock },
  { to: '/doctor/profile', label: 'Doctor Profile', icon: UserCheck },
  { to: '/notifications', label: 'Notifications', icon: Bell },
  { to: '/chat', label: 'AI Chat', icon: MessageSquare },
  { to: '/treatments', label: 'Treatments', icon: HeartPulse },
];

export function AuthenticatedLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const isDoctor = user?.role === 'doctor';
  const sidebarItems = isDoctor ? DOCTOR_SIDEBAR_ITEMS : PATIENT_SIDEBAR_ITEMS;
  const homePortal = isDoctor ? '/doctor/dashboard' : '/dashboard';
  const profileRoute = isDoctor ? '/doctor/profile' : '/profile';

  const initials = (user?.full_name || 'U')
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const handleLogout = async () => {
    setDropdownOpen(false);
    setMobileOpen(false);
    await logout();
    showToast('Signed out safely', 'info');
    navigate('/', { replace: true });
  };

  return (
    <div className={`app-shell ${collapsed ? 'app-shell--collapsed' : ''}`}>
      {mobileOpen && (
        <div
          className="app-backdrop"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={`app-sidebar glass-surface--strong ${
          mobileOpen ? 'is-mobile-open' : ''
        }`}
        aria-label="Application navigation"
      >
        <div className="app-sidebar__top">
          <Link
            to={homePortal}
            className="app-sidebar__logo"
            onClick={() => setMobileOpen(false)}
          >
            <BrandLogo size={34} showText={!collapsed} />
          </Link>

          <button
            type="button"
            className="app-sidebar__collapse-btn"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={() => setCollapsed((c) => !c)}
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>

          <button
            type="button"
            className="app-sidebar__mobile-close"
            aria-label="Close navigation menu"
            onClick={() => setMobileOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="app-sidebar__nav">
          {sidebarItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `app-sidebar__item ${isActive ? 'is-active' : ''}`
              }
              title={collapsed ? label : undefined}
            >
              <Icon size={20} className="app-sidebar__icon" />
              {!collapsed && <span className="app-sidebar__label">{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="app-sidebar__bottom">
          <button
            type="button"
            className="app-sidebar__item app-sidebar__logout"
            onClick={handleLogout}
            title={collapsed ? 'Logout' : undefined}
          >
            <LogOut size={20} className="app-sidebar__icon" />
            {!collapsed && <span className="app-sidebar__label">Logout</span>}
          </button>
        </div>
      </aside>

      <div className="app-main">
        <header className="app-topbar glass-surface">
          <div className="app-topbar__left">
            <button
              type="button"
              className="app-topbar__menu-btn"
              aria-label="Open navigation menu"
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={22} />
            </button>
            <Link to="/" className="app-topbar__home-link">
              Public Home
            </Link>
            <span className="badge badge--cyan">
              {isDoctor ? 'Doctor Portal' : 'Patient Portal'}
            </span>
          </div>

          <div className="app-topbar__right">
            <div className="user-menu">
              <button
                type="button"
                className="user-menu__trigger"
                onClick={() => setDropdownOpen((o) => !o)}
                aria-expanded={dropdownOpen}
              >
                <span className="user-menu__avatar">{initials}</span>
                <span className="user-menu__meta">
                  <span className="user-menu__name">{user?.full_name || 'Member'}</span>
                  <span className="user-menu__email">{user?.email || ''}</span>
                </span>
                <ChevronDown size={16} />
              </button>

              {dropdownOpen && (
                <div className="user-menu__dropdown glass-surface--strong animate-fade-up">
                  <Link
                    to={profileRoute}
                    className="user-menu__item"
                    onClick={() => setDropdownOpen(false)}
                  >
                    <User size={16} /> Profile Settings
                  </Link>
                  <Link
                    to="/notifications"
                    className="user-menu__item"
                    onClick={() => setDropdownOpen(false)}
                  >
                    <Bell size={16} /> Notifications
                  </Link>
                  <button
                    type="button"
                    className="user-menu__item user-menu__item--danger"
                    onClick={handleLogout}
                  >
                    <LogOut size={16} /> Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../common/CommonUI';

export function ProtectedRoute() {
  const { isAuthenticated, initializing } = useAuth();
  const location = useLocation();

  if (initializing) {
    return <LoadingSpinner fullScreen label="Verifying your session..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}

export function RoleRoute({ allowedRoles }) {
  const { user, initializing } = useAuth();

  if (initializing) {
    return <LoadingSpinner fullScreen label="Loading portal..." />;
  }

  const role = user?.role || 'patient';
  if (!allowedRoles.includes(role)) {
    return (
      <Navigate
        to={role === 'doctor' ? '/doctor/dashboard' : '/dashboard'}
        replace
      />
    );
  }

  return <Outlet />;
}

export function PublicOnlyRoute() {
  const { isAuthenticated, initializing, user } = useAuth();

  if (initializing) {
    return <LoadingSpinner fullScreen label="Loading HealthAssist AI..." />;
  }

  if (isAuthenticated) {
    return (
      <Navigate
        to={user?.role === 'doctor' ? '/doctor/dashboard' : '/dashboard'}
        replace
      />
    );
  }

  return <Outlet />;
}

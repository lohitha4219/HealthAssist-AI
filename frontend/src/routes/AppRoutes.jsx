import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import {
  ProtectedRoute,
  PublicOnlyRoute,
  RoleRoute,
} from '../components/navigation/ProtectedRoute';
import { LoadingSpinner } from '../components/common/CommonUI';
import { AuthenticatedLayout } from '../layouts/AuthenticatedLayout';
import { LandingPage } from '../pages/public/LandingPage';
import { LoginPage } from '../pages/auth/LoginPage';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { ForgotPasswordPage } from '../pages/auth/ForgotPasswordPage';
import { DoctorOnboardingPage } from '../pages/DoctorPortal/DoctorOnboardingPage';
import { HospitalsPage } from '../pages/Hospitals/HospitalsPage';
import { HospitalDetailPage } from '../pages/Hospitals/HospitalDetailPage';
import { DoctorsPage } from '../pages/Doctors/DoctorsPage';
import { DoctorDetailPage } from '../pages/Doctors/DoctorDetailPage';
import { TreatmentsPage } from '../pages/Treatments/TreatmentsPage';

const DashboardPage = lazy(() =>
  import('../pages/Dashboard/DashboardPage').then((m) => ({ default: m.DashboardPage }))
);
const SymptomAnalysisPage = lazy(() =>
  import('../pages/Symptoms/SymptomAnalysisPage').then((m) => ({
    default: m.SymptomAnalysisPage,
  }))
);
const ChatPage = lazy(() =>
  import('../pages/Chat/ChatPage').then((m) => ({ default: m.ChatPage }))
);
const MedicalReportsPage = lazy(() =>
  import('../pages/Reports/MedicalReportsPage').then((m) => ({
    default: m.MedicalReportsPage,
  }))
);
const HealthInsightsPage = lazy(() =>
  import('../pages/Insights/HealthInsightsPage').then((m) => ({
    default: m.HealthInsightsPage,
  }))
);
const HealthHistoryPage = lazy(() =>
  import('../pages/History/HealthHistoryPage').then((m) => ({
    default: m.HealthHistoryPage,
  }))
);
const ProfilePage = lazy(() =>
  import('../pages/Profile/ProfilePage').then((m) => ({ default: m.ProfilePage }))
);
const AppointmentsPage = lazy(() =>
  import('../pages/Appointments/AppointmentsPage').then((m) => ({
    default: m.AppointmentsPage,
  }))
);
const NotificationsPage = lazy(() =>
  import('../pages/Notifications/NotificationsPage').then((m) => ({
    default: m.NotificationsPage,
  }))
);
const DoctorDashboardPage = lazy(() =>
  import('../pages/DoctorPortal/DoctorDashboardPage').then((m) => ({
    default: m.DoctorDashboardPage,
  }))
);
const DoctorAppointmentsPage = lazy(() =>
  import('../pages/DoctorPortal/DoctorAppointmentsPage').then((m) => ({
    default: m.DoctorAppointmentsPage,
  }))
);
const DoctorAvailabilityPage = lazy(() =>
  import('../pages/DoctorPortal/DoctorAvailabilityPage').then((m) => ({
    default: m.DoctorAvailabilityPage,
  }))
);
const DoctorProfilePage = lazy(() =>
  import('../pages/DoctorPortal/DoctorProfilePage').then((m) => ({
    default: m.DoctorProfilePage,
  }))
);

function LazyRoute({ children }) {
  return (
    <Suspense fallback={<LoadingSpinner label="Loading module..." />}>
      {children}
    </Suspense>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/about" element={<Navigate to="/#about" replace />} />
      <Route path="/features" element={<Navigate to="/#features" replace />} />
      <Route path="/how-it-works" element={<Navigate to="/#how-it-works" replace />} />
      <Route path="/contact" element={<Navigate to="/#contact" replace />} />

      {/* Patient & Doctor Path Aliases */}
      <Route path="/patient" element={<Navigate to="/dashboard" replace />} />
      <Route path="/patient/dashboard" element={<Navigate to="/dashboard" replace />} />
      <Route path="/patient/hospitals" element={<Navigate to="/hospitals" replace />} />
      <Route path="/patient/doctors" element={<Navigate to="/doctors" replace />} />
      <Route path="/patient/appointments" element={<Navigate to="/appointments" replace />} />
      <Route path="/patient/symptoms" element={<Navigate to="/symptom-analysis" replace />} />
      <Route path="/patient/symptom-analysis" element={<Navigate to="/symptom-analysis" replace />} />
      <Route path="/patient/chat" element={<Navigate to="/chat" replace />} />
      <Route path="/patient/reports" element={<Navigate to="/medical-reports" replace />} />
      <Route path="/patient/medical-reports" element={<Navigate to="/medical-reports" replace />} />
      <Route path="/patient/treatments" element={<Navigate to="/treatments" replace />} />
      <Route path="/patient/insights" element={<Navigate to="/health-insights" replace />} />
      <Route path="/patient/health-insights" element={<Navigate to="/health-insights" replace />} />
      <Route path="/patient/history" element={<Navigate to="/health-history" replace />} />
      <Route path="/patient/health-history" element={<Navigate to="/health-history" replace />} />
      <Route path="/patient/notifications" element={<Navigate to="/notifications" replace />} />
      <Route path="/patient/profile" element={<Navigate to="/profile" replace />} />
      <Route path="/doctor" element={<Navigate to="/doctor/dashboard" replace />} />
      <Route path="/doctor/notes" element={<Navigate to="/doctor/appointments" replace />} />

      {/* Public & Shared Directories */}
      <Route path="/hospitals" element={<HospitalsPage />} />
      <Route path="/hospitals/:id" element={<HospitalDetailPage />} />
      <Route path="/doctors" element={<DoctorsPage />} />
      <Route path="/doctors/:id" element={<DoctorDetailPage />} />
      <Route path="/treatments" element={<TreatmentsPage />} />

      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/doctor-onboarding" element={<DoctorOnboardingPage />} />
      </Route>

      {/* Authenticated Portals (Patient & Doctor ONLY; No Admin Panel) */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AuthenticatedLayout />}>
          {/* Shared Authenticated Pages */}
          <Route
            path="/chat"
            element={
              <LazyRoute>
                <ChatPage />
              </LazyRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <LazyRoute>
                <NotificationsPage />
              </LazyRoute>
            }
          />

          {/* Patient Portal */}
          <Route element={<RoleRoute allowedRoles={['patient']} />}>
            <Route
              path="/dashboard"
              element={
                <LazyRoute>
                  <DashboardPage />
                </LazyRoute>
              }
            />
            <Route
              path="/appointments"
              element={
                <LazyRoute>
                  <AppointmentsPage />
                </LazyRoute>
              }
            />
            <Route
              path="/symptom-analysis"
              element={
                <LazyRoute>
                  <SymptomAnalysisPage />
                </LazyRoute>
              }
            />
            <Route
              path="/medical-reports"
              element={
                <LazyRoute>
                  <MedicalReportsPage />
                </LazyRoute>
              }
            />
            <Route
              path="/health-insights"
              element={
                <LazyRoute>
                  <HealthInsightsPage />
                </LazyRoute>
              }
            />
            <Route
              path="/health-history"
              element={
                <LazyRoute>
                  <HealthHistoryPage />
                </LazyRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <LazyRoute>
                  <ProfilePage />
                </LazyRoute>
              }
            />
          </Route>

          {/* Doctor Portal */}
          <Route element={<RoleRoute allowedRoles={['doctor']} />}>
            <Route
              path="/doctor/dashboard"
              element={
                <LazyRoute>
                  <DoctorDashboardPage />
                </LazyRoute>
              }
            />
            <Route
              path="/doctor/appointments"
              element={
                <LazyRoute>
                  <DoctorAppointmentsPage />
                </LazyRoute>
              }
            />
            <Route
              path="/doctor/availability"
              element={
                <LazyRoute>
                  <DoctorAvailabilityPage />
                </LazyRoute>
              }
            />
            <Route
              path="/doctor/profile"
              element={
                <LazyRoute>
                  <DoctorProfilePage />
                </LazyRoute>
              }
            />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

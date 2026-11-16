import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastProvider } from '../context/ToastContext';
import { AuthProvider } from '../context/AuthContext';
import { AppRoutes } from '../routes/AppRoutes';
import { authService } from '../services/authService';
import { chatService } from '../services/chatAndReportService';
import { healthService } from '../services/healthService';
import { healthcareService } from '../services/healthcareService';

vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    doctorRegister: vi.fn(),
    getMe: vi.fn(),
    logout: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
  },
}));

vi.mock('../services/chatAndReportService', () => ({
  chatService: {
    getAIHealth: vi.fn(),
    listConversations: vi.fn(),
    createConversation: vi.fn(),
    getConversation: vi.fn(),
    renameConversation: vi.fn(),
    deleteConversation: vi.fn(),
    sendMessage: vi.fn(),
  },
  reportService: {
    listReports: vi.fn(),
    uploadReport: vi.fn(),
    getReport: vi.fn(),
    analyzeReport: vi.fn(),
    downloadReport: vi.fn(),
    deleteReport: vi.fn(),
  },
}));

vi.mock('../services/healthService', () => ({
  healthService: {
    getDashboardSummary: vi.fn(),
    getDashboardActivity: vi.fn(),
    getSymptomCatalog: vi.fn(),
    assessSymptoms: vi.fn(),
    getSymptomHistory: vi.fn(),
    deleteSymptomAssessment: vi.fn(),
    getInsightsSummary: vi.fn(),
    getInsightsTrends: vi.fn(),
    getHistory: vi.fn(),
    deleteHistoryRecord: vi.fn(),
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
}));

vi.mock('../services/healthcareService', () => ({
  healthcareService: {
    getPublicOverview: vi.fn(),
    submitContactEnquiry: vi.fn(),
    listTreatments: vi.fn(),
    getTreatmentDetail: vi.fn(),
    getHospitalFilters: vi.fn(),
    listHospitals: vi.fn(),
    getHospitalDetail: vi.fn(),
    listDoctors: vi.fn(),
    getDoctorDetail: vi.fn(),
    getDoctorSlots: vi.fn(),
    bookAppointment: vi.fn(),
    listMyAppointments: vi.fn(),
    cancelAppointment: vi.fn(),
    rescheduleAppointment: vi.fn(),
    listNotifications: vi.fn(),
    markNotificationRead: vi.fn(),
    markAllNotificationsRead: vi.fn(),
    getDoctorDashboard: vi.fn(),
    listDoctorAppointments: vi.fn(),
    updateDoctorAppointmentStatus: vi.fn(),
    getDoctorAppointmentReports: vi.fn(),
    addConsultationNote: vi.fn(),
    getDoctorAvailability: vi.fn(),
    saveDoctorAvailability: vi.fn(),
    listDoctorLeaves: vi.fn(),
    addDoctorLeave: vi.fn(),
    deleteDoctorLeave: vi.fn(),
    getDoctorOwnProfile: vi.fn(),
    updateDoctorOwnProfile: vi.fn(),
  },
}));

function renderAt(route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <ToastProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ToastProvider>
    </MemoryRouter>
  );
}

describe('HealthAssist AI Frontend', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.clearAllMocks();
    healthcareService.getPublicOverview.mockResolvedValue({
      stats: {
        verified_hospitals: 21,
        verified_doctors: 0,
        specialties: 12,
        departments: 126,
        appointments: 0,
      },
      featured_hospitals: [
        {
          id: 1,
          name: 'AIIMS Mangalagiri',
          slug: 'aiims-mangalagiri',
          hospital_type: 'Autonomous Tertiary Hospital',
          address: 'Mangalagiri',
          city: 'Mangalagiri',
          district: 'Guntur',
          state: 'Andhra Pradesh',
          verification_status: 'verified',
          department_count: 10,
          treatment_count: 4,
          doctor_count: 0,
        },
      ],
      featured_doctors: [],
      support: {},
    });
  });

  it('renders public landing page with clean hero, DB stats, contact support, minimal footer and no hospital/doctor showcase', async () => {
    const user = userEvent.setup();
    healthcareService.submitContactEnquiry = vi.fn().mockResolvedValue({
      id: 101,
      message: 'Thank you, Ravi! Your enquiry has been delivered successfully to our support team at nslohitha2924@gmail.com.',
      email_delivered: true,
      delivery_status: 'sent',
    });

    renderAt('/');

    expect(
      screen.getByRole('heading', { name: /Your Health, Our Intelligence\./i })
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Get Started/i })).toHaveAttribute(
      'href',
      '/register'
    );

    await waitFor(() => {
      expect(screen.getByText('21')).toBeInTheDocument();
    });

    // Hospitals and Doctors showcase sections are NOT on public home page
    expect(screen.queryByRole('heading', { name: /Verified Hospitals Showcase/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /Doctors Showcase/i })).not.toBeInTheDocument();

    // Contact Support section exists with email link
    expect(screen.getByRole('heading', { name: /Contact Support/i })).toBeInTheDocument();
    const emailLinks = screen.getAllByRole('link', { name: /nslohitha2924@gmail\.com/i });
    expect(emailLinks.length).toBeGreaterThanOrEqual(1);
    expect(emailLinks[0]).toHaveAttribute('href', 'mailto:nslohitha2924@gmail.com');

    // Minimal footer displays dynamic copyright
    const currentYear = new Date().getFullYear();
    expect(
      screen.getByText(new RegExp(`© ${currentYear} HealthAssist AI\\. All Rights Reserved\\.`, 'i'))
    ).toBeInTheDocument();

    // No Admin Panel anywhere
    expect(screen.queryByText(/Admin Panel/i)).not.toBeInTheDocument();

    // Contact form submission
    await user.type(screen.getByLabelText(/Full Name/i), 'Ravi Varma');
    await user.type(screen.getByLabelText(/Email Address/i), 'ravi@example.com');
    await user.type(screen.getByLabelText(/Subject/i), 'Hospital enquiry');
    await user.type(screen.getByLabelText(/Message/i), 'Looking for cardiology specialist appointment timings.');
    await user.click(screen.getByRole('button', { name: /Submit Enquiry/i }));

    await waitFor(() => {
      expect(healthcareService.submitContactEnquiry).toHaveBeenCalledWith({
        name: 'Ravi Varma',
        email: 'ravi@example.com',
        subject: 'Hospital enquiry',
        message: 'Looking for cardiology specialist appointment timings.',
      });
    });
  });

  it('redirects unauthenticated users from protected routes to login', async () => {
    renderAt('/dashboard');
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();
    });
  });

  it('validates login and navigates patient to dashboard with sidebar modules', async () => {
    const user = userEvent.setup();
    const fakeUser = {
      id: 1,
      full_name: 'Maya Patel',
      email: 'maya@example.com',
      role: 'patient',
      is_active: true,
      created_at: '2026-11-10T10:00:00Z',
    };
    authService.login.mockResolvedValue({
      access_token: 'access-123',
      refresh_token: 'refresh-123',
      user: fakeUser,
    });
    healthService.getDashboardSummary.mockResolvedValue({
      user: fakeUser,
      stats: {
        total_assessments: 2,
        total_reports: 1,
        total_conversations: 3,
        total_activities: 5,
      },
      recent_assessments: [],
      recent_reports: [],
      recent_activities: [],
      ai_status: {
        available: false,
        provider: 'auto',
        configured_provider: 'auto',
        status: 'offline',
        detail: 'Offline',
        setup_hint: 'Run llama-server',
        checked_at: '2026-11-10T10:00:00Z',
      },
      notifications: [],
    });

    renderAt('/login');

    await user.type(screen.getByLabelText('Email Address'), 'maya@example.com');
    await user.type(screen.getByLabelText('Password'), 'HealthPass123');
    await user.click(screen.getByRole('checkbox', { name: /Remember me/i }));
    await user.click(screen.getByRole('button', { name: /Sign In/i }));

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: /Welcome back, Maya Patel/i })
      ).toBeInTheDocument();
    });

    expect(sessionStorage.getItem('ha_access_token')).toBe('access-123');
    expect(screen.getByRole('link', { name: 'Hospitals' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Appointments' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Medical Reports' })).toBeInTheDocument();
  });

  it('routes verified doctor login to Doctor Portal with doctor sidebar', async () => {
    const fakeDoc = {
      id: 9,
      full_name: 'Dr. Priya Rao',
      email: 'priya@example.com',
      role: 'doctor',
      is_active: true,
      created_at: '2026-11-10T10:00:00Z',
    };
    localStorage.setItem('ha_access_token', 'doc-token');
    localStorage.setItem('ha_user', JSON.stringify(fakeDoc));
    authService.getMe.mockResolvedValue(fakeDoc);
    healthcareService.getDoctorDashboard.mockResolvedValue({
      doctor: {
        id: 3,
        full_name: 'Dr. Priya Rao',
        email: 'priya@example.com',
        specialization: 'Cardiology',
        qualification: 'MBBS, MD',
        verification_status: 'verified',
        hospital_name: 'AIIMS Mangalagiri',
      },
      stats: {
        today_appointments: 1,
        upcoming_appointments: 4,
        pending_requests: 2,
        confirmed_appointments: 2,
        completed_appointments: 5,
        cancelled_appointments: 0,
        patient_count: 6,
      },
      recent_appointments: [],
    });

    renderAt('/doctor/dashboard');

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Welcome, Dr\. Priya Rao/i })).toBeInTheDocument();
    });
    expect(screen.getByRole('link', { name: 'Availability & Leave' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Doctor Profile' })).toBeInTheDocument();
  });

  it('supports chat creation and Enter-to-send', async () => {
    const user = userEvent.setup();
    const fakeUser = {
      id: 1,
      full_name: 'Alex Rivera',
      email: 'alex@example.com',
      role: 'patient',
      is_active: true,
      created_at: '2026-11-10T10:00:00Z',
    };
    localStorage.setItem('ha_access_token', 'access-123');
    localStorage.setItem('ha_user', JSON.stringify(fakeUser));
    authService.getMe.mockResolvedValue(fakeUser);
    chatService.getAIHealth.mockResolvedValue({
      available: true,
      provider: 'llamacpp',
      configured_provider: 'auto',
      model: 'qwen2.5-1.5b',
      status: 'online',
      detail: 'Ready',
      setup_hint: 'Ready',
      checked_at: '2026-11-10T10:00:00Z',
    });
    chatService.listConversations.mockResolvedValue([]);
    chatService.createConversation.mockResolvedValue({
      id: 10,
      title: 'New Conversation',
      message_count: 0,
      created_at: '2026-11-10T10:00:00Z',
      updated_at: '2026-11-10T10:00:00Z',
    });
    chatService.sendMessage.mockResolvedValue({
      conversation: {
        id: 10,
        title: 'Explain REST APIs',
        message_count: 2,
        last_message_preview: 'REST uses HTTP...',
        created_at: '2026-11-10T10:00:00Z',
        updated_at: '2026-11-10T10:01:00Z',
      },
      user_message: {
        id: 1,
        conversation_id: 10,
        role: 'user',
        content: 'Explain REST APIs',
        created_at: '2026-11-10T10:01:00Z',
      },
      assistant_message: {
        id: 2,
        conversation_id: 10,
        role: 'assistant',
        content: 'REST uses HTTP methods cleanly.',
        model_name: 'qwen2.5-1.5b',
        created_at: '2026-11-10T10:01:02Z',
      },
    });

    renderAt('/chat');

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'AI Chat Assistant' })).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText('Chat message input'), 'Explain REST APIs{Enter}');

    await waitFor(() => {
      expect(screen.getByText('REST uses HTTP methods cleanly.')).toBeInTheDocument();
    });
  });

  it('validates registration form and navigates to patient dashboard', async () => {
    const user = userEvent.setup();
    const fakeUser = {
      id: 2,
      full_name: 'Sam Taylor',
      email: 'sam@example.com',
      role: 'patient',
      is_active: true,
      created_at: '2026-11-10T10:00:00Z',
    };
    authService.register.mockResolvedValue({
      message: 'Registration successful',
      access_token: 'a1',
      refresh_token: 'r1',
      user: fakeUser,
    });
    healthService.getDashboardSummary.mockResolvedValue({
      user: fakeUser,
      stats: {
        total_assessments: 0,
        total_reports: 0,
        total_conversations: 0,
        total_activities: 1,
      },
      recent_assessments: [],
      recent_reports: [],
      recent_activities: [],
      ai_status: {
        available: false,
        provider: 'auto',
        configured_provider: 'auto',
        status: 'offline',
        detail: 'Offline',
        setup_hint: 'Run llama-server',
        checked_at: '2026-11-10T10:00:00Z',
      },
      notifications: [],
    });

    renderAt('/register');

    await user.type(screen.getByLabelText('Full Name *'), 'Sam Taylor');
    await user.type(screen.getByLabelText('Email Address *'), 'sam@example.com');
    await user.type(screen.getByLabelText('Password *'), 'PassWord123');
    await user.type(screen.getByLabelText('Confirm Password *'), 'PassWord999');
    await user.click(screen.getByRole('button', { name: /Get Started/i }));

    expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();

    await user.clear(screen.getByLabelText('Confirm Password *'));
    await user.type(screen.getByLabelText('Confirm Password *'), 'PassWord123');
    await user.click(screen.getByRole('button', { name: /Get Started/i }));

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: /Welcome back, Sam Taylor/i })
      ).toBeInTheDocument();
    });
  });
});

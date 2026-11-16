import apiClient from './apiClient';

export const healthcareService = {
  // Public & Education
  async getPublicOverview() {
    const { data } = await apiClient.get('/public/overview');
    return data;
  },
  async submitContactEnquiry(payload) {
    const { data } = await apiClient.post('/contact', payload);
    return data;
  },
  async listTreatments() {
    const { data } = await apiClient.get('/treatments');
    return data;
  },
  async getTreatmentDetail(slug) {
    const { data } = await apiClient.get(`/treatments/${slug}`);
    return data;
  },

  // Hospitals
  async getHospitalFilters() {
    const { data } = await apiClient.get('/hospitals/filters');
    return data;
  },
  async listHospitals(params = {}) {
    const { data } = await apiClient.get('/hospitals', { params });
    return data;
  },
  async getHospitalDetail(id) {
    const { data } = await apiClient.get(`/hospitals/${id}`);
    return data;
  },

  // Doctors
  async listDoctors(params = {}) {
    const { data } = await apiClient.get('/doctors', { params });
    return data;
  },
  async getDoctorDetail(id) {
    const { data } = await apiClient.get(`/doctors/${id}`);
    return data;
  },
  async getDoctorSlots(id, dateStr) {
    const { data } = await apiClient.get(`/doctors/${id}/slots`, {
      params: { date: dateStr },
    });
    return data;
  },

  // Patient Appointments & Notifications
  async bookAppointment(payload) {
    const { data } = await apiClient.post('/appointments', payload);
    return data;
  },
  async listMyAppointments(statusFilter = 'all') {
    const { data } = await apiClient.get('/appointments/my', {
      params: statusFilter && statusFilter !== 'all' ? { status_filter: statusFilter } : {},
    });
    return data;
  },
  async cancelAppointment(id, cancellationReason) {
    const { data } = await apiClient.patch(`/appointments/${id}/cancel`, {
      cancellation_reason: cancellationReason,
    });
    return data;
  },
  async rescheduleAppointment(id, payload) {
    const { data } = await apiClient.patch(`/appointments/${id}/reschedule`, payload);
    return data;
  },
  async listNotifications() {
    const { data } = await apiClient.get('/notifications');
    return data;
  },
  async markNotificationRead(id) {
    const { data } = await apiClient.patch(`/notifications/${id}/read`);
    return data;
  },
  async markAllNotificationsRead() {
    const { data } = await apiClient.post('/notifications/read-all');
    return data;
  },

  // Doctor Portal
  async getDoctorDashboard() {
    const { data } = await apiClient.get('/doctor/dashboard');
    return data;
  },
  async listDoctorAppointments(statusFilter = 'all') {
    const { data } = await apiClient.get('/doctor/appointments', {
      params: statusFilter && statusFilter !== 'all' ? { status_filter: statusFilter } : {},
    });
    return data;
  },
  async updateDoctorAppointmentStatus(id, payload) {
    const { data } = await apiClient.patch(`/doctor/appointments/${id}/status`, payload);
    return data;
  },
  async getDoctorAppointmentReports(appointmentId) {
    const { data } = await apiClient.get(`/doctor/appointments/${appointmentId}/reports`);
    return data;
  },
  async addConsultationNote(appointmentId, payload) {
    const { data } = await apiClient.post(`/doctor/appointments/${appointmentId}/notes`, payload);
    return data;
  },
  async getDoctorAvailability() {
    const { data } = await apiClient.get('/doctor/availability');
    return data;
  },
  async saveDoctorAvailability(rules) {
    const { data } = await apiClient.put('/doctor/availability', rules);
    return data;
  },
  async listDoctorLeaves() {
    const { data } = await apiClient.get('/doctor/leaves');
    return data;
  },
  async addDoctorLeave(payload) {
    const { data } = await apiClient.post('/doctor/leaves', payload);
    return data;
  },
  async deleteDoctorLeave(id) {
    const { data } = await apiClient.delete(`/doctor/leaves/${id}`);
    return data;
  },
  async getDoctorOwnProfile() {
    const { data } = await apiClient.get('/doctor/profile');
    return data;
  },
  async updateDoctorOwnProfile(payload) {
    const { data } = await apiClient.patch('/doctor/profile', payload);
    return data;
  },
};

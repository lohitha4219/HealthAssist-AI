import apiClient from './apiClient';

export const healthService = {
  async getDashboardSummary() {
    const { data } = await apiClient.get('/dashboard/summary');
    return data;
  },
  async getDashboardActivity(limit = 15) {
    const { data } = await apiClient.get('/dashboard/activity', { params: { limit } });
    return data;
  },
  async getSymptomCatalog() {
    const { data } = await apiClient.get('/symptoms/catalog');
    return data;
  },
  async assessSymptoms(payload) {
    const { data } = await apiClient.post('/symptoms/assess', payload);
    return data;
  },
  async getSymptomHistory(page = 1, pageSize = 10) {
    const { data } = await apiClient.get('/symptoms/history', {
      params: { page, page_size: pageSize },
    });
    return data;
  },
  async deleteSymptomAssessment(id) {
    const { data } = await apiClient.delete(`/symptoms/${id}`);
    return data;
  },
  async getInsightsSummary() {
    const { data } = await apiClient.get('/insights/summary');
    return data;
  },
  async getInsightsTrends() {
    const { data } = await apiClient.get('/insights/trends');
    return data;
  },
  async getHistory(params) {
    const { data } = await apiClient.get('/history', { params });
    return data;
  },
  async deleteHistoryRecord(recordType, id) {
    const { data } = await apiClient.delete(`/history/${recordType}/${id}`);
    return data;
  },
  async getProfile() {
    const { data } = await apiClient.get('/profile');
    return data;
  },
  async updateProfile(payload) {
    const { data } = await apiClient.patch('/profile', payload);
    return data;
  },
  async changePassword(payload) {
    const { data } = await apiClient.post('/profile/change-password', payload);
    return data;
  },
};

import apiClient from './apiClient';

export const authService = {
  async register(payload) {
    const { data } = await apiClient.post('/auth/register', payload);
    return data;
  },
  async doctorRegister(payload) {
    const { data } = await apiClient.post('/auth/doctor-register', payload);
    return data;
  },
  async login(payload) {
    const { data } = await apiClient.post('/auth/login', payload);
    return data;
  },
  async getMe() {
    const { data } = await apiClient.get('/auth/me');
    return data;
  },
  async logout(refreshToken) {
    const { data } = await apiClient.post('/auth/logout', {
      refresh_token: refreshToken || null,
    });
    return data;
  },
  async forgotPassword(email) {
    const { data } = await apiClient.post('/auth/forgot-password', { email });
    return data;
  },
  async resetPassword(payload) {
    const { data } = await apiClient.post('/auth/reset-password', payload);
    return data;
  },
};

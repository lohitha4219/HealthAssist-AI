import apiClient, { getStoredTokens } from './apiClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const chatService = {
  async getAIHealth() {
    const { data } = await apiClient.get('/chat/health');
    return data;
  },
  async listConversations() {
    const { data } = await apiClient.get('/chat/conversations');
    return data;
  },
  async createConversation(title) {
    const { data } = await apiClient.post('/chat/conversations', title ? { title } : {});
    return data;
  },
  async getConversation(id) {
    const { data } = await apiClient.get(`/chat/conversations/${id}`);
    return data;
  },
  async renameConversation(id, title) {
    const { data } = await apiClient.patch(`/chat/conversations/${id}`, { title });
    return data;
  },
  async deleteConversation(id) {
    const { data } = await apiClient.delete(`/chat/conversations/${id}`);
    return data;
  },
  async sendMessage(conversationId, content) {
    const { data } = await apiClient.post(
      `/chat/conversations/${conversationId}/messages`,
      { content }
    );
    return data;
  },
  async streamMessage(conversationId, content, onChunk, onDone, onError) {
    const { accessToken } = getStoredTokens();
    const res = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify({ content }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const err = new Error(errData.detail || `Server error (${res.status})`);
      if (onError) onError(err);
      throw err;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let streamError = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();
      for (const block of lines) {
        if (block.startsWith('data: ')) {
          let payload;
          try {
            payload = JSON.parse(block.slice(6));
          } catch {
            continue;
          }
          if (payload.chunk && onChunk) {
            onChunk(payload.chunk);
          }
          if (payload.error) {
            streamError = new Error(payload.error);
            if (onError) onError(streamError);
            break;
          }
          if (payload.done && onDone) {
            onDone(payload);
          }
        }
      }
      if (streamError) break;
    }

    if (streamError) {
      throw streamError;
    }
  },
};

export const reportService = {
  async listReports(params) {
    const { data } = await apiClient.get('/reports', { params });
    return data;
  },
  async uploadReport(file, category, notes) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category || 'General Report');
    if (notes) formData.append('notes', notes);

    const { data } = await apiClient.post('/reports/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
  async getReport(id) {
    const { data } = await apiClient.get(`/reports/${id}`);
    return data;
  },
  async analyzeReport(id) {
    const { data } = await apiClient.post(`/reports/${id}/analyze`);
    return data;
  },
  async downloadReport(id, originalFilename) {
    const response = await apiClient.get(`/reports/${id}/download`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', originalFilename || 'medical-report');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
  async deleteReport(id) {
    const { data } = await apiClient.delete(`/reports/${id}`);
    return data;
  },
};

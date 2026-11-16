import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const STORAGE_KEYS = {
  ACCESS: 'ha_access_token',
  REFRESH: 'ha_refresh_token',
  USER: 'ha_user',
};

function getActiveStorage() {
  if (localStorage.getItem(STORAGE_KEYS.ACCESS) || localStorage.getItem(STORAGE_KEYS.REFRESH)) {
    return localStorage;
  }
  if (sessionStorage.getItem(STORAGE_KEYS.ACCESS) || sessionStorage.getItem(STORAGE_KEYS.REFRESH)) {
    return sessionStorage;
  }
  return localStorage;
}

export function getStoredTokens() {
  const storage = getActiveStorage();
  return {
    accessToken: storage.getItem(STORAGE_KEYS.ACCESS),
    refreshToken: storage.getItem(STORAGE_KEYS.REFRESH),
  };
}

export function setStoredSession({ access_token, refresh_token, user }, rememberMe) {
  let target;
  if (rememberMe === true) {
    target = localStorage;
    sessionStorage.removeItem(STORAGE_KEYS.ACCESS);
    sessionStorage.removeItem(STORAGE_KEYS.REFRESH);
    sessionStorage.removeItem(STORAGE_KEYS.USER);
  } else if (rememberMe === false) {
    target = sessionStorage;
    localStorage.removeItem(STORAGE_KEYS.ACCESS);
    localStorage.removeItem(STORAGE_KEYS.REFRESH);
    localStorage.removeItem(STORAGE_KEYS.USER);
  } else {
    target = getActiveStorage();
  }

  if (access_token) target.setItem(STORAGE_KEYS.ACCESS, access_token);
  if (refresh_token) target.setItem(STORAGE_KEYS.REFRESH, refresh_token);
  if (user) target.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
}

export function clearStoredSession() {
  for (const store of [localStorage, sessionStorage]) {
    store.removeItem(STORAGE_KEYS.ACCESS);
    store.removeItem(STORAGE_KEYS.REFRESH);
    store.removeItem(STORAGE_KEYS.USER);
  }
}

export function getStoredUser() {
  for (const store of [localStorage, sessionStorage]) {
    try {
      const raw = store.getItem(STORAGE_KEYS.USER);
      if (raw) return JSON.parse(raw);
    } catch {
      // ignore corrupted entry
    }
  }
  return null;
}

let onSessionExpiredCallback = null;
export function registerSessionExpiredHandler(handler) {
  onSessionExpiredCallback = handler;
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const { accessToken } = getStoredTokens();
  if (accessToken && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let refreshPromise = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;

    if (
      status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/register') &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      const { refreshToken } = getStoredTokens();
      if (!refreshToken) {
        clearStoredSession();
        if (onSessionExpiredCallback) onSessionExpiredCallback();
        return Promise.reject(error);
      }

      originalRequest._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
            .then((res) => {
              setStoredSession(res.data);
              return res.data.access_token;
            })
            .finally(() => {
              refreshPromise = null;
            });
        }
        const newAccessToken = await refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        clearStoredSession();
        if (onSessionExpiredCallback) onSessionExpiredCallback();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export function extractApiError(error, fallback = 'Something went wrong. Please try again.') {
  if (!error?.response) {
    if (error?.code === 'ECONNABORTED') {
      return 'Request timed out. Please verify the backend service is responsive.';
    }
    return 'Unable to connect to the server. Please check your network connection or verify the backend is running.';
  }

  const status = error.response.status;
  const detail = error.response?.data?.detail;

  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        const msg = item?.msg || 'Invalid input';
        return msg.replace(/^Value error,\s*/i, '');
      })
      .join('. ');
  }
  if (status === 429) {
    return 'Too many attempts. Please wait a moment before trying again.';
  }
  if (status >= 500) {
    return 'The server encountered an unexpected error. Please try again shortly.';
  }
  return fallback;
}

export default apiClient;

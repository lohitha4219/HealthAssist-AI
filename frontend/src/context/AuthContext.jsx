import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  clearStoredSession,
  getStoredTokens,
  getStoredUser,
  registerSessionExpiredHandler,
  setStoredSession,
} from '../services/apiClient';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser());
  const [initializing, setInitializing] = useState(true);

  const clearSession = useCallback(() => {
    clearStoredSession();
    setUser(null);
  }, []);

  useEffect(() => {
    registerSessionExpiredHandler(() => {
      setUser(null);
    });
  }, []);

  useEffect(() => {
    let active = true;
    async function hydrateSession() {
      const { accessToken } = getStoredTokens();
      if (!accessToken) {
        if (active) {
          setUser(null);
          setInitializing(false);
        }
        return;
      }
      try {
        const me = await authService.getMe();
        if (active) {
          setUser(me);
          setStoredSession({ user: me });
        }
      } catch {
        if (active) {
          clearStoredSession();
          setUser(null);
        }
      } finally {
        if (active) setInitializing(false);
      }
    }
    hydrateSession();
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async ({ email, password, rememberMe = true }) => {
    const data = await authService.login({
      email,
      password,
      remember_me: rememberMe,
    });
    setStoredSession(data, rememberMe);
    setUser(data.user);
    return data;
  }, []);

  const register = useCallback(async (payload) => {
    const data = await authService.register(payload);
    setStoredSession(data, true);
    setUser(data.user);
    return data;
  }, []);

  const doctorRegister = useCallback(async (payload) => {
    const data = await authService.doctorRegister(payload);
    setStoredSession(data, true);
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(async () => {
    const { refreshToken } = getStoredTokens();
    try {
      if (refreshToken) {
        await authService.logout(refreshToken);
      }
    } catch {
      // Clear local session regardless of server response
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const refreshUser = useCallback(async () => {
    const me = await authService.getMe();
    setUser(me);
    setStoredSession({ user: me });
    return me;
  }, []);

  const updateUserLocal = useCallback((updatedUser) => {
    setUser(updatedUser);
    setStoredSession({ user: updatedUser });
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      initializing,
      login,
      register,
      doctorRegister,
      logout,
      refreshUser,
      updateUserLocal,
    }),
    [user, initializing, login, register, doctorRegister, logout, refreshUser, updateUserLocal]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}

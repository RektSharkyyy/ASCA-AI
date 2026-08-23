/**
 * ASCA AI — Authentication Context
 *
 * Provides login / logout state to the whole React tree.
 * Tokens are persisted to localStorage so a page refresh keeps the user logged in.
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { loginUser, getMe, refreshToken as apiRefreshToken } from '../api/client';

const AuthContext = createContext(null);

const TOKEN_KEY   = 'asca_access_token';
const REFRESH_KEY = 'asca_refresh_token';
const USER_KEY    = 'asca_user';

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(() => {
    try { return JSON.parse(localStorage.getItem(USER_KEY)) || null; } catch { return null; }
  });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const isAuthenticated = !!user && !!localStorage.getItem(TOKEN_KEY);

  // -------------------------------------------------------------------------
  // login(email, password) → stores tokens + user in localStorage
  // -------------------------------------------------------------------------
  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const data = await loginUser(email, password);
      localStorage.setItem(TOKEN_KEY,   data.access_token);
      localStorage.setItem(REFRESH_KEY, data.refresh_token);
      const profile = {
        email:     data.user_email,
        full_name: data.user_name,
        role:      data.role,
      };
      localStorage.setItem(USER_KEY, JSON.stringify(profile));
      setUser(profile);
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  // -------------------------------------------------------------------------
  // logout() → clears everything from localStorage
  // -------------------------------------------------------------------------
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    setError(null);
  }, []);

  // -------------------------------------------------------------------------
  // On mount: verify the stored token is still valid
  // -------------------------------------------------------------------------
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;
    getMe()
      .then(profile => setUser({
        email:     profile.email,
        full_name: profile.full_name,
        role:      profile.role,
      }))
      .catch(() => logout());   // token expired or invalid → force logout
  }, [logout]);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Hook to consume the auth context anywhere in the tree. */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}

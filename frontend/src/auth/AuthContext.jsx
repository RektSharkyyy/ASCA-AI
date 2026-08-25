/**
 * ASCA AI — Authentication Context
 *
 * Provides login / logout state to the whole React tree.
 * Tokens are persisted to localStorage so a page refresh keeps the user logged in.
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { loginUser, getMe } from '../api/client';

const AuthContext = createContext(null);

const TOKEN_KEY   = 'asca_access_token';
const REFRESH_KEY = 'asca_refresh_token';
const USER_KEY    = 'asca_user';

export function AuthProvider({ children }) {
  // Initialise user directly from localStorage — no async blocking
  const [user,    setUser]    = useState(() => {
    try {
      const token  = localStorage.getItem(TOKEN_KEY);
      const cached = JSON.parse(localStorage.getItem(USER_KEY));
      return token && cached ? cached : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  // isAuthenticated is pure React state — every setUser() triggers a re-render
  const isAuthenticated = !!user;

  // -------------------------------------------------------------------------
  // login(email, password) → stores tokens + user in localStorage + state
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
      setUser(profile);   // immediately shows dashboard
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  // -------------------------------------------------------------------------
  // logout() → clears everything + replaces history so back button is blocked
  // -------------------------------------------------------------------------
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    setError(null);
    // Replace the current history entry so the browser back button
    // cannot navigate back to the authenticated dashboard
    window.history.replaceState(null, '', window.location.href);
  }, []);

  // -------------------------------------------------------------------------
  // On mount: silently validate the stored token in the background.
  // We already trusted localStorage above — if the token is expired the
  // server will return 401 and we force-logout the user.
  // -------------------------------------------------------------------------
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;   // no token → nothing to validate

    getMe()
      .then(profile => {
        // Refresh user profile in case role/name changed server-side
        setUser({
          email:     profile.email,
          full_name: profile.full_name,
          role:      profile.role,
        });
      })
      .catch(() => {
        // Token expired or invalid → logout silently
        logout();
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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

/**
 * ASCA AI — HTTP API client
 *
 * All backend calls go through this module so the base URL and auth header
 * live in one place. The Bearer token is read from localStorage on every call
 * so that login/logout changes are reflected immediately without a page reload.
 */

const BASE = '/api';

function getToken() {
  return localStorage.getItem('asca_access_token');
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { detail = (await res.json()).detail || detail; } catch { /* ignore */ }
    throw Object.assign(new Error(detail), { status: res.status });
  }
  return res.json();
}

// --------------------------------------------------------------------------- //
// Health / meta
// --------------------------------------------------------------------------- //
export const getHealth = () => fetch('/health').then(r => r.json()).catch(() => null);
export const getMeta   = () => request('/meta');

// --------------------------------------------------------------------------- //
// Auth
// --------------------------------------------------------------------------- //
export const loginUser    = (email, password) =>
  request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

export const registerUser = (email, full_name, password, role = 'viewer') =>
  request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, full_name, password, role }),
  });

export const refreshToken = (refresh_token) =>
  request('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token }),
  });

export const getMe = () => request('/auth/me');

// --------------------------------------------------------------------------- //
// Chat
// --------------------------------------------------------------------------- //
export const postChat = (message, centreId = 'DAMBULLA', sessionId = null) =>
  request('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, centre_id: centreId, session_id: sessionId }),
  });

/** Fetch all conversation sessions for the current user (newest first). */
export const getChatSessions = () => request('/chat/history');

/** Fetch all messages inside a specific session. */
export const getChatSessionMessages = (sessionId) =>
  request(`/chat/history/${encodeURIComponent(sessionId)}`);

/** Delete a specific conversation session. */
export const deleteChatSession = (sessionId) =>
  request(`/chat/history/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });

/** Wipe ALL chat history for the current user. */
export const clearAllChatHistory = () =>
  request('/chat/history', { method: 'DELETE' });


// --------------------------------------------------------------------------- //
// Market analytics
// --------------------------------------------------------------------------- //
export const getForecast = (centreId, crop) =>
  request(`/market/forecast?centre_id=${centreId}&crop=${crop}`);

export const getInsights = (centreId) =>
  request(`/market/insights?centre_id=${centreId}`);

// --------------------------------------------------------------------------- //
// B2B
// --------------------------------------------------------------------------- //
export const getBuyers    = (centreId) =>
  request(`/b2b/buyers?centre_id=${centreId}`);

export const getB2BMatches = (centreId, crops = null) =>
  request('/b2b/match', {
    method: 'POST',
    body: JSON.stringify({ centre_id: centreId, crops }),
  });

// --------------------------------------------------------------------------- //
// Market Price Sync (Scraper)
// --------------------------------------------------------------------------- //

/** Trigger HARTI/CBSL scraper → Supabase upsert for one or all centres. */
export const syncMarketPrices = (centreId = null) =>
  request('/market/sync-prices', {
    method: 'POST',
    body: JSON.stringify({ centre_id: centreId }),
  });

/** Admin: manually set a specific crop price in Supabase. */
export const manualUpdatePrice = (centreId, cropName, priceLkr, supplyTons, date = null) =>
  request('/market/manual-update', {
    method: 'POST',
    body: JSON.stringify({
      centre_id:   centreId,
      crop_name:   cropName,
      price_lkr:   priceLkr,
      supply_tons: supplyTons,
      date,
    }),
  });

/** Admin: seed N days of historical baseline data into Supabase. */
export const seedBaseline = (days = 60) =>
  request('/market/seed-baseline', {
    method: 'POST',
    body: JSON.stringify({ days }),
  });


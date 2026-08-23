import { useState, useEffect, useCallback } from 'react';
import {
  MessageSquare, TrendingUp, Users, FileText, Settings,
  Plus, Clock, Loader, Trash2
} from 'lucide-react';
import { CENTERS } from '../../data/mockData';
import { getChatSessions, deleteChatSession } from '../../api/client';

const NAV_ITEMS = [
  { id: 'chat',       label: '💬  AI Advisory Chat',       badge: null },
  { id: 'analytics',  label: '📈  Price Forecast Curves',   badge: null },
  { id: 'b2b',        label: '🤝  B2B Match Directory',     badge: '6'  },
  { id: 'blueprints', label: '📄  Executive Blueprints',    badge: null },
  { id: 'settings',   label: '⚙️  System Settings',         badge: null },
];

function formatSessionDate(isoStr) {
  if (!isoStr) return '';
  const d   = new Date(isoStr);
  const now = new Date();
  const diffMs = now - d;
  const diffH  = diffMs / 3600000;
  const diffD  = diffMs / 86400000;
  if (diffH  < 1)  return 'Just now';
  if (diffH  < 24) return 'Today';
  if (diffD  < 2)  return 'Yesterday';
  if (diffD  < 7)  return d.toLocaleDateString('en-GB', { weekday: 'short' });
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

export default function Sidebar({
  activeView,
  onViewChange,
  activeCenter,
  onCenterChange,
  activeSessionId,
  onNewSession,
  onSelectSession,
  onSessionDeleted,
  sessionsRefreshKey,
}) {
  const [sessions, setSessions]   = useState([]);
  const [loading,  setLoading]    = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  // Fetch sessions whenever the refresh key increments or component mounts
  const fetchSessions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getChatSessions();
      setSessions(Array.isArray(data) ? data : []);
    } catch {
      setSessions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions, sessionsRefreshKey]);

  const handleDelete = async (e, sessionId) => {
    e.stopPropagation();
    setDeletingId(sessionId);
    try {
      await deleteChatSession(sessionId);
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));
      // If the deleted session was active, start a fresh chat
      if (activeSessionId === sessionId) onNewSession?.();
      onSessionDeleted?.();
    } catch {
      /* ignore */
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <aside className="sidebar">
      {/* New session button */}
      <button
        className="new-session-btn"
        onClick={() => { onNewSession?.(); onViewChange('chat'); }}
      >
        <Plus size={14} />
        New Session
      </button>

      {/* Center selector */}
      <div className="center-selector">
        <div className="center-selector-label">Economic Centre</div>
        {CENTERS.map(c => (
          <div
            key={c.id}
            className={`center-option ${activeCenter === c.id ? 'active' : ''}`}
            onClick={() => onCenterChange(c.id)}
          >
            <div className="center-option-dot" />
            <span>{c.label}</span>
          </div>
        ))}
      </div>

      <div className="sidebar-divider" />

      {/* Navigation */}
      <div className="sidebar-section-label">Navigation</div>
      {NAV_ITEMS.map(item => (
        <div
          key={item.id}
          className={`nav-item ${activeView === item.id ? 'active' : ''}`}
          onClick={() => onViewChange(item.id)}
        >
          <span style={{ fontSize: 13 }}>{item.label}</span>
          {item.badge && <span className="nav-item-badge">{item.badge}</span>}
        </div>
      ))}

      <div className="sidebar-divider" />

      {/* Recent Sessions — dynamic from Supabase */}
      <div className="sidebar-section-label">
        <Clock size={10} style={{ display: 'inline', marginRight: 4 }} />
        Recent Sessions
        {loading && (
          <Loader
            size={9}
            style={{ display: 'inline', marginLeft: 6, opacity: 0.5, animation: 'spin 1s linear infinite' }}
          />
        )}
      </div>

      {!loading && sessions.length === 0 && (
        <div className="sidebar-sessions-empty">No recent sessions</div>
      )}

      <div className="sidebar-sessions-list">
        {sessions.map(s => (
          <div
            key={s.session_id}
            className={`session-history-item ${activeSessionId === s.session_id ? 'active' : ''}`}
            onClick={() => { onSelectSession?.(s.session_id); onViewChange('chat'); }}
          >
            <div className="session-item-body">
              <div className="title truncate">{s.title}</div>
              <div className="meta">
                {formatSessionDate(s.last_message_at)}
                {s.centre_id && (
                  <span className="session-centre-badge">{s.centre_id.slice(0, 3)}</span>
                )}
                <span className="session-msg-count">{s.message_count} msg{s.message_count !== 1 ? 's' : ''}</span>
              </div>
            </div>
            <button
              className={`session-delete-btn ${deletingId === s.session_id ? 'deleting' : ''}`}
              title="Delete session"
              onClick={(e) => handleDelete(e, s.session_id)}
              disabled={deletingId === s.session_id}
            >
              <Trash2 size={11} />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}

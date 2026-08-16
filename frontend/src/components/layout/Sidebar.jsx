import {
  MessageSquare, TrendingUp, Users, FileText, Settings,
  Plus, ChevronDown, Clock
} from 'lucide-react';
import { CENTERS, SESSION_HISTORY } from '../../data/mockData';

const NAV_ITEMS = [
  { id: 'chat',       icon: MessageSquare, label: '💬  AI Advisory Chat',       badge: null  },
  { id: 'analytics',  icon: TrendingUp,    label: '📈  Price Forecast Curves',   badge: null  },
  { id: 'b2b',        icon: Users,         label: '🤝  B2B Match Directory',     badge: '6'   },
  { id: 'blueprints', icon: FileText,      label: '📄  Executive Blueprints',    badge: null  },
  { id: 'settings',   icon: Settings,      label: '⚙️  System Settings',         badge: null  },
];

export default function Sidebar({ activeView, onViewChange, activeCenter, onCenterChange }) {
  return (
    <aside className="sidebar">
      {/* New session */}
      <button className="new-session-btn" onClick={() => onViewChange('chat')}>
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

      {/* Recent sessions */}
      <div className="sidebar-section-label"><Clock size={10} style={{ display:'inline', marginRight:4 }} />Recent Sessions</div>
      {SESSION_HISTORY.map(s => (
        <div key={s.id} className="session-history-item" onClick={() => onViewChange('chat')}>
          <div className="title truncate">{s.title}</div>
          <div className="meta">{s.date} · {s.center}</div>
        </div>
      ))}
    </aside>
  );
}

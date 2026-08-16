import { Bell, PanelRight, Wifi, Activity, Cpu } from 'lucide-react';
import { CENTERS } from '../../data/mockData';

export default function Header({ activeCenter, onCenterChange, panelOpen, onPanelToggle }) {
  const center = CENTERS.find(c => c.id === activeCenter);

  return (
    <header className="header">
      {/* Logo */}
      <div className="header-logo">
        <div className="header-logo-icon">🌾</div>
        <div>
          <div className="header-logo-text">ASCA AI</div>
          <div className="header-logo-sub">Supply Chain Advisory</div>
        </div>
      </div>

      {/* Center + status */}
      <div className="header-center">
        <div className="center-badge" onClick={() => onCenterChange(activeCenter === 'DAMBULLA' ? 'THAMBUTHTHEGAMA' : 'DAMBULLA')}>
          <div className="center-dot" />
          {center?.label}
        </div>
        <div className="header-status-list">
          <div className="status-chip online"><Wifi size={10} /> Market Scout: Online</div>
          <div className="status-chip purple"><Cpu size={10} /> Llama 3.1 8B: Ready</div>
          <div className="status-chip amber"><Activity size={10} /> Prophet: Idle</div>
        </div>
      </div>

      {/* Right actions */}
      <div className="header-right">
        <button className="icon-btn" title="Notifications">
          <Bell size={14} />
        </button>
        <button className={`icon-btn ${panelOpen ? 'active' : ''}`} onClick={onPanelToggle} title="Toggle Artifact Panel" style={panelOpen ? { background: 'var(--accent-dim)', borderColor: 'var(--border-active)', color: 'var(--accent)' } : {}}>
          <PanelRight size={14} />
        </button>
      </div>
    </header>
  );
}

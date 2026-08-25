import { useState } from 'react';
import { Cpu, Bell, Radio, Key, LogOut, User } from 'lucide-react';
import { BROADCAST_LOGS } from '../data/mockData';
import { useAuth } from '../auth/AuthContext';

function Toggle({ value, onChange }) {
  return (
    <div className={`toggle ${value ? 'on' : ''}`} onClick={() => onChange(!value)}>
      <div className="toggle-knob" />
    </div>
  );
}

export default function SettingsView() {
  const { user, logout } = useAuth();
  const [settings, setSettings] = useState({
    sms: true,
    whatsapp: true,
    anomaly: true,
    autoRun: false,
    chromaSync: true,
    llmFallback: true,
  });

  const set = key => val => setSettings(s => ({ ...s, [key]: val }));

  return (
    <div className="settings-view">
      <div>
        <div className="view-title">⚙️ System Settings &amp; Broadcast Logs</div>
        <div className="view-subtitle" style={{ marginTop: 4 }}>Real-time Telegram delivery trackers &amp; agent configuration</div>
      </div>

      {/* Agent Config */}
      <div className="settings-card">
        <div className="settings-card-title"><Cpu size={14} /> Agent Configuration</div>
        {[
          { key: 'autoRun', label: 'Auto-Run Market Scout', sub: 'Automatically scout all crops every morning at 06:00' },
          { key: 'anomaly', label: 'Anomaly Detection Alerts', sub: 'Trigger alerts when surplus >25% price deviation detected' },
          { key: 'llmFallback', label: 'Fail-Open Guardrail', sub: 'Default to in_scope on OpenRouter network failures' },
          { key: 'chromaSync', label: 'ChromaDB Auto-Sync', sub: 'Sync B2B buyer vector embeddings nightly' },
        ].map(r => (
          <div key={r.key} className="settings-row">
            <div>
              <div className="settings-row-label">{r.label}</div>
              <div className="settings-row-sub">{r.sub}</div>
            </div>
            <Toggle value={settings[r.key]} onChange={set(r.key)} />
          </div>
        ))}
      </div>

      {/* Notification Config */}
      <div className="settings-card">
        <div className="settings-card-title"><Bell size={14} /> Telegram Broadcast Settings</div>
        {[
          { key: 'sms', label: 'Telegram SMS Alerts', sub: 'Send surplus and price alerts via Telegram Bot API' },
          { key: 'whatsapp', label: 'WhatsApp Notifications', sub: 'Send B2B match notifications to farmer WhatsApp groups' },
        ].map(r => (
          <div key={r.key} className="settings-row">
            <div>
              <div className="settings-row-label">{r.label}</div>
              <div className="settings-row-sub">{r.sub}</div>
            </div>
            <Toggle value={settings[r.key]} onChange={set(r.key)} />
          </div>
        ))}
        <div className="settings-row">
          <div>
            <div className="settings-row-label">Model</div>
            <div className="settings-row-sub">OpenRouter · meta-llama/llama-3.1-8b-instruct</div>
          </div>
          <span style={{ fontSize: 11, color: 'var(--accent)', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>Llama 3.1 8B</span>
        </div>
      </div>

      {/* Broadcast log */}
      <div className="settings-card">
        <div className="settings-card-title"><Radio size={14} /> Live Broadcast Log</div>
        {BROADCAST_LOGS.map((log, i) => (
          <div key={i} className="log-entry">
            <span className="log-ts">{log.ts}</span>
            <span className={`log-level ${log.level}`}>{log.level}</span>
            <span className="log-msg">{log.msg}</span>
          </div>
        ))}
      </div>

      {/* API keys */}
      <div className="settings-card">
        <div className="settings-card-title"><Key size={14} /> API &amp; Integration Keys</div>
        {[
          { label: 'OpenRouter API Key', val: 'sk-or-v1-••••••••••••••3a8f' },
          { label: 'Telegram Bot Token', val: '7412••••••:AAF••••••••••Bk8' },
          { label: 'Tavily Search Key', val: 'tvly-••••••••••••••••zQ9' },
        ].map((row, i) => (
          <div key={i} className="settings-row">
            <div className="settings-row-label">{row.label}</div>
            <span className="font-mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>{row.val}</span>
          </div>
        ))}
      </div>

      {/* ── Account & Logout ── */}
      <div className="settings-card settings-logout-card">
        <div className="settings-card-title"><User size={14} /> Account</div>
        <div className="settings-logout-row">
          <div className="settings-user-info">
            <div className="settings-user-avatar">
              {user?.full_name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || '?'}
            </div>
            <div>
              <div className="settings-user-name">{user?.full_name || 'User'}</div>
              <div className="settings-user-email">{user?.email}</div>
              <div className="settings-user-role">
                {user?.role === 'admin' ? '🔑 Administrator' : '👁 Viewer'}
              </div>
            </div>
          </div>
          <button className="settings-logout-btn" onClick={logout}>
            <LogOut size={15} />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

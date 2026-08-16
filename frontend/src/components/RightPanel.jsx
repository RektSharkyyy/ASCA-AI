import { useState } from 'react';
import { X } from 'lucide-react';
import { FORECAST_DATA } from '../data/mockData';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  Tooltip, CartesianGrid
} from 'recharts';

export default function RightPanel({ artifact, onClose }) {
  if (!artifact) {
    return (
      <div className="right-panel slide-in">
        <div className="right-panel-header">
          <span style={{ color: 'var(--text-secondary)' }}>Artifact Panel</span>
        </div>
        <div className="right-panel-body">
          <div className="artifact-placeholder">
            <div className="artifact-placeholder-icon">🎨</div>
            <div className="artifact-placeholder-text">
              Contextual visualizations appear here when you request charts, PDFs, or B2B match summaries in the chat.
              <br /><br />
              Try asking: <strong style={{ color: 'var(--text-secondary)' }}>"Show 14-day Tomato price curve"</strong>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (artifact.type === 'chart') {
    const data = FORECAST_DATA[artifact.crop] || FORECAST_DATA['Tomato'];
    return (
      <div className="right-panel slide-in">
        <div className="right-panel-header">
          <span>📈 {artifact.crop} Forecast</span>
          <button className="icon-btn" onClick={onClose}><X size={14} /></button>
        </div>
        <div className="right-panel-body">
          <div className="forecast-panel-card">
            <div className="forecast-panel-card-title">{artifact.crop} — 14-Day Prophet Forecast (LKR/kg)</div>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -16 }}>
                <defs>
                  <linearGradient id="rpa" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#38bdf8" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="rpf" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#818cf8" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" tick={{ fill: '#475569', fontSize: 9 }} tickLine={false} axisLine={false} interval={3} />
                <YAxis tick={{ fill: '#475569', fontSize: 9 }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Area type="monotone" dataKey="actual"   stroke="#38bdf8" strokeWidth={2} fill="url(#rpa)" name="Actual"   dot={false} connectNulls={false} />
                <Area type="monotone" dataKey="forecast" stroke="#818cf8" strokeWidth={2} strokeDasharray="5 3" fill="url(#rpf)" name="Forecast" dot={false} connectNulls={false} />
              </AreaChart>
            </ResponsiveContainer>
            <div className="forecast-legend" style={{ marginTop: 8 }}>
              <div className="legend-item"><div className="legend-dot" style={{ background: '#38bdf8' }} />Actual</div>
              <div className="legend-item"><div className="legend-dot" style={{ background: '#818cf8' }} />Forecast</div>
            </div>
          </div>

          {/* Extra info cards */}
          {['Day 7 Projection', 'Day 14 Projection', 'Anomaly Status'].map((label, i) => (
            <div key={i} className="forecast-panel-card">
              <div className="forecast-panel-card-title">{label}</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: i === 2 ? 'var(--red)' : 'var(--accent)' }}>
                {i === 0 ? 'LKR 103/kg' : i === 1 ? 'LKR 98/kg' : '● SURPLUS DETECTED'}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                {i === 0 ? '↓ 12.7% from today' : i === 1 ? '↓ 16.9% from today' : '51.08 T above absorption'}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
}

import { AgentThoughtLog } from './AgentThoughtLog';
import { FileDown, Radio, ExternalLink, TrendingUp } from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  Tooltip, CartesianGrid
} from 'recharts';

function InlineChart({ data, cropName }) {
  if (!data) return null;
  return (
    <div className="price-forecast-card">
      <div className="price-forecast-card-title">📈 {cropName} — 14-Day Price Forecast (LKR/kg)</div>
      <ResponsiveContainer width="100%" height={140}>
        <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
          <defs>
            <linearGradient id="ga" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gf" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#818cf8" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="date" tick={{ fill: '#475569', fontSize: 9 }} tickLine={false} axisLine={false} interval={3} />
          <YAxis tick={{ fill: '#475569', fontSize: 9 }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
            labelStyle={{ color: '#94a3b8' }}
          />
          <Area type="monotone" dataKey="actual" stroke="#38bdf8" strokeWidth={2} fill="url(#ga)" name="Actual" connectNulls={false} dot={false} />
          <Area type="monotone" dataKey="forecast" stroke="#818cf8" strokeWidth={2} strokeDasharray="4 2" fill="url(#gf)" name="Forecast" connectNulls={false} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
      <div className="forecast-legend">
        <div className="legend-item"><div className="legend-dot" style={{ background: '#38bdf8' }} />Actual</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: '#818cf8' }} />14-Day Forecast</div>
      </div>
    </div>
  );
}

export default function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'user' : 'agent'} fade-in`}>
      <div className={`message-avatar ${isUser ? 'user' : 'agent'}`}>
        {isUser ? '👤' : '🌾'}
      </div>
      <div className="message-content">
        <div className="message-meta">
          {isUser ? 'You' : 'ASCA AI'} · {msg.time}
        </div>
        <div className={`message-bubble ${isUser ? 'user' : 'agent'}`}>
          {msg.text}
          {msg.chart && <InlineChart data={msg.chart.data} cropName={msg.chart.crop} />}
        </div>
        {msg.thoughts && <AgentThoughtLog steps={msg.thoughts} />}
        {msg.actions && (
          <div className="inline-actions">
            {msg.actions.map((a, i) => (
              <button key={i} className={`action-btn ${a.primary ? 'primary' : ''}`}>
                {a.icon === 'pdf'   && <FileDown size={12} />}
                {a.icon === 'sms'   && <Radio size={12} />}
                {a.icon === 'chart' && <TrendingUp size={12} />}
                {a.icon === 'ext'   && <ExternalLink size={12} />}
                {a.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

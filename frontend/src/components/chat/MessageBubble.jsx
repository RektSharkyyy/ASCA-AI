import { AgentThoughtLog } from './AgentThoughtLog';
import { FileDown, Radio, ExternalLink, TrendingUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  Tooltip, CartesianGrid
} from 'recharts';
import { generateChatAdvisoryPDF } from '../../utils/pdfGenerator';

function InlineChart({ data, cropName }) {
  if (!data) return null;
  return (
    <div className="price-forecast-card">
      <div className="price-forecast-card-title">📈 {cropName} — 14-Day Price Forecast (LKR/kg)</div>
      <ResponsiveContainer width="100%" height={150}>
        <AreaChart data={data} margin={{ top: 6, right: 10, bottom: 0, left: -10 }}>
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
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} interval={3} />
          <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
          <Tooltip
            contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
            labelStyle={{ color: '#94a3b8' }}
          />
          <Area type="monotone" dataKey="actual" stroke="#38bdf8" strokeWidth={2.5} fill="url(#ga)" name="Actual Price" connectNulls={false} dot={false} />
          <Area type="monotone" dataKey="forecast" stroke="#818cf8" strokeWidth={2.5} strokeDasharray="4 3" fill="url(#gf)" name="14-Day Forecast" connectNulls={false} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
      <div className="forecast-legend">
        <div className="legend-item"><div className="legend-dot" style={{ background: '#38bdf8' }} />Observed Wholesale Price</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: '#818cf8' }} />Prophet Forecast</div>
      </div>
    </div>
  );
}

export default function MessageBubble({ msg, onAction, activeCenter }) {
  const isUser = msg.role === 'user';

  const handleActionClick = (a) => {
    if (a.icon === 'pdf' || (a.label && (a.label.includes('Blueprint') || a.label.includes('PDF')))) {
      generateChatAdvisoryPDF(msg, { activeCenter, title: a.label });
    } else if (onAction && a.prompt) {
      onAction(a.prompt);
    }
  };

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
          {isUser ? (
            <div className="user-message-text">{msg.text}</div>
          ) : (
            <div className="markdown-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ node, ...props }) => (
                    <a {...props} target="_blank" rel="noopener noreferrer" className="chat-link" />
                  ),
                }}
              >
                {msg.text}
              </ReactMarkdown>
            </div>
          )}
          {msg.chart && <InlineChart data={msg.chart.data} cropName={msg.chart.crop} />}
        </div>
        {msg.thoughts && <AgentThoughtLog steps={msg.thoughts} />}
        {msg.actions && msg.actions.length > 0 && (
          <div className="inline-actions">
            {msg.actions.map((a, i) => (
              <button
                key={i}
                className={`action-btn ${a.primary ? 'primary' : ''}`}
                onClick={() => handleActionClick(a)}
                title={a.icon === 'pdf' ? 'Download this advisory as a PDF dossier' : ''}
              >
                {a.icon === 'pdf'   && <FileDown size={12} />}
                {a.icon === 'sms'   && <Radio size={12} />}
                {a.icon === 'chart' && <TrendingUp size={12} />}
                {a.icon === 'ext'   && <ExternalLink size={12} />}
                {a.icon === 'pdf' ? '📄 Download Advisory PDF' : a.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

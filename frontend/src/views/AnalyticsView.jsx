import { useState } from 'react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceLine, Legend
} from 'recharts';
import { FORECAST_DATA, CROPS } from '../data/mockData';

const CROP_STATS = {
  Tomato:        { cur: 118, d7: 103, d14: 98,  change: -16.9, supply: 51.1, risk: 'HIGH',   color: '#f87171' },
  Carrot:        { cur: 87,  d7: 90,  d14: 94,  change: +8.0,  supply: 24.5, risk: 'LOW',    color: '#fb923c' },
  Beans:         { cur: 145, d7: 138, d14: 130, change: -10.3, supply: 38.2, risk: 'MEDIUM', color: '#4ade80' },
  Eggplant:      { cur: 76,  d7: 72,  d14: 69,  change: -9.2,  supply: 18.0, risk: 'MEDIUM', color: '#a78bfa' },
  Cabbage:       { cur: 58,  d7: 61,  d14: 65,  change: +12.1, supply: 12.3, risk: 'LOW',    color: '#38bdf8' },
  'Green Chilli':{ cur: 295, d7: 278, d14: 260, change: -11.9, supply: 9.8,  risk: 'HIGH',   color: '#fbbf24' },
};

const RISK_COLOR = { HIGH: 'var(--red)', CRITICAL: 'var(--red)', MEDIUM: 'var(--amber)', LOW: 'var(--green)' };

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#111827', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, padding: '8px 12px', fontSize: 11 }}>
      <div style={{ color: '#94a3b8', marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: <span style={{ color: '#f1f5f9' }}>LKR {p.value}/kg</span>
        </div>
      ))}
    </div>
  );
};

export default function AnalyticsView({ activeCenter }) {
  const [activeCrop, setActiveCrop] = useState('Tomato');
  const data   = FORECAST_DATA[activeCrop] || FORECAST_DATA['Tomato'];
  const stats  = CROP_STATS[activeCrop] || CROP_STATS['Tomato'];
  const todayIdx = 7;

  return (
    <div className="analytics-view">
      {/* Header */}
      <div className="analytics-header">
        <div>
          <div className="view-title">📈 Price Forecast Curves</div>
          <div className="view-subtitle">{activeCenter === 'DAMBULLA' ? 'Dambulla' : 'Thambuththegama'} Economic Centre · Prophet 14-Day Projection</div>
        </div>
        <div className="crop-tabs">
          {CROPS.map(c => (
            <button key={c} className={`crop-tab ${activeCrop === c ? 'active' : ''}`} onClick={() => setActiveCrop(c)}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Stats row */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-label">Current Price</div>
          <div className="stat-card-value accent">LKR {stats.cur}</div>
          <div className="stat-card-sub">per kg today</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Day 7 Forecast</div>
          <div className={`stat-card-value ${stats.d7 < stats.cur ? 'red' : 'green'}`}>LKR {stats.d7}</div>
          <div className="stat-card-sub">7-day projection</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Day 14 Forecast</div>
          <div className={`stat-card-value ${stats.d14 < stats.cur ? 'red' : 'green'}`}>LKR {stats.d14}</div>
          <div className="stat-card-sub">14-day projection</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Price Change</div>
          <div className={`stat-card-value ${stats.change < 0 ? 'red' : 'green'}`}>
            {stats.change > 0 ? '+' : ''}{stats.change}%
          </div>
          <div className="stat-card-sub">14-day delta</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Supply Volume</div>
          <div className="stat-card-value amber">{stats.supply} T</div>
          <div className="stat-card-sub">Current surplus</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Risk Level</div>
          <div className="stat-card-value" style={{ color: RISK_COLOR[stats.risk], fontSize: 16 }}>● {stats.risk}</div>
          <div className="stat-card-sub">Anomaly status</div>
        </div>
      </div>

      {/* Main chart */}
      <div className="chart-card">
        <div className="chart-card-header">
          <div>
            <div className="chart-card-title">{activeCrop} — Historical & 14-Day Forecast (LKR/kg)</div>
            <div className="chart-card-sub">Prophet model with uncertainty bands · Vertical line = Today</div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="gActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#38bdf8" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gForecast" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#818cf8" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#818cf8" stopOpacity={0.08} />
                <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="date" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} interval={2} />
            <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `${v}`} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine x={data[todayIdx]?.date} stroke="rgba(251,191,36,0.5)" strokeDasharray="4 2" label={{ value: 'Today', fill: '#fbbf24', fontSize: 10 }} />
            <Area type="monotone" dataKey="upper"    stroke="none" fill="url(#gBand)" name="Upper Band" connectNulls={false} />
            <Area type="monotone" dataKey="actual"   stroke="#38bdf8" strokeWidth={2.5} fill="url(#gActual)"   name="Actual"   dot={false} connectNulls={false} />
            <Area type="monotone" dataKey="forecast" stroke="#818cf8" strokeWidth={2} strokeDasharray="5 3" fill="url(#gForecast)" name="Forecast" dot={false} connectNulls={false} />
            <Area type="monotone" dataKey="lower"    stroke="none" fill="none" name="Lower Band" connectNulls={false} />
          </AreaChart>
        </ResponsiveContainer>
        <div className="forecast-legend" style={{ marginTop: 12 }}>
          <div className="legend-item"><div className="legend-dot" style={{ background: '#38bdf8' }} />Actual Price</div>
          <div className="legend-item"><div className="legend-dot" style={{ background: '#818cf8' }} />Prophet Forecast</div>
          <div className="legend-item"><div className="legend-dot" style={{ background: 'rgba(129,140,248,0.3)', border: '1px dashed #818cf8' }} />Uncertainty Band</div>
        </div>
      </div>
    </div>
  );
}

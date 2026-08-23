import { useState, useEffect, useCallback } from 'react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceLine,
} from 'recharts';
import { getForecast, getInsights, syncMarketPrices } from '../api/client';

const CROP_LIST = [
  { id: 'tomato',       label: 'Tomato',       color: '#f87171' },
  { id: 'carrot',       label: 'Carrot',        color: '#fb923c' },
  { id: 'beans',        label: 'Beans',         color: '#4ade80' },
  { id: 'eggplant',     label: 'Eggplant',      color: '#a78bfa' },
  { id: 'cabbage',      label: 'Cabbage',        color: '#38bdf8' },
  { id: 'green_chilli', label: 'Green Chilli',  color: '#fbbf24' },
];

const RISK_COLOR = {
  HIGH: 'var(--red)', CRITICAL: 'var(--red)',
  MEDIUM: 'var(--amber)', LOW: 'var(--green)',
};

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

const Spinner = () => (
  <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', fontSize: 13 }}>
    ⏳ Loading from backend…
  </div>
);

export default function AnalyticsView({ activeCenter }) {
  const [activeCrop, setActiveCrop] = useState('tomato');
  const [forecast, setForecast]     = useState(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [chartError, setChartError]     = useState(null);

  // Sync state
  const [syncing,    setSyncing]    = useState(false);
  const [syncStatus, setSyncStatus] = useState(null); // { type: 'success'|'error', msg: string }

  const fetchForecast = useCallback(async () => {
    setLoadingChart(true);
    setChartError(null);
    try {
      const data = await getForecast(activeCenter, activeCrop);
      setForecast(data);
    } catch (err) {
      setChartError(err.message);
    } finally {
      setLoadingChart(false);
    }
  }, [activeCenter, activeCrop]);

  useEffect(() => { fetchForecast(); }, [fetchForecast]);

  // ---- Sync handler -------------------------------------------------------
  const handleSync = useCallback(async () => {
    if (syncing) return;
    setSyncing(true);
    setSyncStatus(null);
    try {
      const res = await syncMarketPrices(activeCenter);
      const totals = res.results.reduce(
        (acc, r) => ({ ins: acc.ins + r.inserted, upd: acc.upd + r.updated }), { ins: 0, upd: 0 }
      );
      setSyncStatus({
        type: 'success',
        msg:  `✅ Sync complete — ${totals.ins} new records, ${totals.upd} updated. Refreshing charts…`,
      });
      // Refresh the forecast chart after DB is updated
      await fetchForecast();
    } catch (err) {
      setSyncStatus({ type: 'error', msg: `❌ Sync failed: ${err.message}` });
    } finally {
      setSyncing(false);
      // Auto-clear the status banner after 8 s
      setTimeout(() => setSyncStatus(null), 8000);
    }
  }, [activeCenter, syncing, fetchForecast]);

  const crop    = CROP_LIST.find(c => c.id === activeCrop) || CROP_LIST[0];
  const series  = forecast?.series ?? [];
  const todayIdx = series.findIndex(p => p.actual != null && p.forecast != null);
  const todayLabel = todayIdx >= 0 ? series[todayIdx]?.date : series[Math.floor(series.length / 2)]?.date;

  return (
    <div className="analytics-view">
      {/* Sync status banner */}
      {syncStatus && (
        <div className={`sync-banner sync-banner-${syncStatus.type}`}>
          {syncStatus.msg}
        </div>
      )}

      {/* Header */}
      <div className="analytics-header">
        <div>
          <div className="view-title">📈 Price Forecast Curves</div>
          <div className="view-subtitle">
            {activeCenter === 'DAMBULLA' ? 'Dambulla' : 'Thambuththegama'} Economic Centre · Prophet 14-Day Projection
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            className={`sync-btn ${syncing ? 'syncing' : ''}`}
            onClick={handleSync}
            disabled={syncing}
            title="Fetch today's prices from HARTI/CBSL and update Supabase"
          >
            <span className={`sync-icon ${syncing ? 'spinning' : ''}`}>🔄</span>
            {syncing ? 'Syncing…' : 'Sync Live Prices'}
          </button>
          <div className="crop-tabs">
            {CROP_LIST.map(c => (
              <button
                key={c.id}
                className={`crop-tab ${activeCrop === c.id ? 'active' : ''}`}
                onClick={() => setActiveCrop(c.id)}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-label">Current Price</div>
          <div className="stat-card-value accent">
            {forecast ? `LKR ${forecast.current_price_lkr}` : '—'}
          </div>
          <div className="stat-card-sub">per kg today</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Day 7 Forecast</div>
          <div className={`stat-card-value ${forecast && forecast.day7_price_lkr < forecast.current_price_lkr ? 'red' : 'green'}`}>
            {forecast ? `LKR ${forecast.day7_price_lkr}` : '—'}
          </div>
          <div className="stat-card-sub">7-day projection</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Day 14 Forecast</div>
          <div className={`stat-card-value ${forecast && forecast.day14_price_lkr < forecast.current_price_lkr ? 'red' : 'green'}`}>
            {forecast ? `LKR ${forecast.day14_price_lkr}` : '—'}
          </div>
          <div className="stat-card-sub">14-day projection</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Price Change</div>
          <div className={`stat-card-value ${forecast && forecast.price_change_pct < 0 ? 'red' : 'green'}`}>
            {forecast ? `${forecast.price_change_pct > 0 ? '+' : ''}${forecast.price_change_pct}%` : '—'}
          </div>
          <div className="stat-card-sub">14-day delta</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Supply Volume</div>
          <div className="stat-card-value amber">
            {forecast ? `${forecast.supply_volume_tons} T` : '—'}
          </div>
          <div className="stat-card-sub">Current supply</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Risk Level</div>
          <div className="stat-card-value" style={{ color: RISK_COLOR[forecast?.risk_level ?? 'LOW'], fontSize: 16 }}>
            ● {forecast?.risk_level ?? '—'}
          </div>
          <div className="stat-card-sub">Anomaly status</div>
        </div>
      </div>

      {/* Main chart */}
      <div className="chart-card">
        <div className="chart-card-header">
          <div>
            <div className="chart-card-title">{crop.label} — Historical &amp; 14-Day Forecast (LKR/kg)</div>
            <div className="chart-card-sub">Prophet model with uncertainty bands · Vertical line = Today</div>
          </div>
        </div>

        {loadingChart && <Spinner />}
        {chartError  && (
          <div style={{ color: 'var(--red)', padding: 20, fontSize: 12 }}>
            ⚠️ Could not load forecast: {chartError}
          </div>
        )}
        {!loadingChart && !chartError && (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={series} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
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
              <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              {todayLabel && (
                <ReferenceLine
                  x={todayLabel}
                  stroke="rgba(251,191,36,0.5)"
                  strokeDasharray="4 2"
                  label={{ value: 'Today', fill: '#fbbf24', fontSize: 10 }}
                />
              )}
              <Area type="monotone" dataKey="upper"    stroke="none" fill="url(#gBand)"     name="Upper Band" connectNulls={false} />
              <Area type="monotone" dataKey="actual"   stroke="#38bdf8" strokeWidth={2.5} fill="url(#gActual)"   name="Actual"   dot={false} connectNulls={false} />
              <Area type="monotone" dataKey="forecast" stroke="#818cf8" strokeWidth={2} strokeDasharray="5 3" fill="url(#gForecast)" name="Forecast" dot={false} connectNulls={false} />
              <Area type="monotone" dataKey="lower"    stroke="none" fill="none" name="Lower Band" connectNulls={false} />
            </AreaChart>
          </ResponsiveContainer>
        )}

        <div className="forecast-legend" style={{ marginTop: 12 }}>
          <div className="legend-item"><div className="legend-dot" style={{ background: '#38bdf8' }} />Actual Price</div>
          <div className="legend-item"><div className="legend-dot" style={{ background: '#818cf8' }} />Prophet Forecast</div>
          <div className="legend-item"><div className="legend-dot" style={{ background: 'rgba(129,140,248,0.3)', border: '1px dashed #818cf8' }} />Uncertainty Band</div>
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { X, FileDown, CheckCircle } from 'lucide-react';
import { FORECAST_DATA } from '../data/mockData';
import { generateCropForecastPDF } from '../utils/pdfGenerator';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  Tooltip, CartesianGrid
} from 'recharts';

export default function RightPanel({ artifact, activeCenter = 'DAMBULLA', onClose }) {
  const [downloading, setDownloading] = useState(false);
  const [downloaded, setDownloaded]   = useState(false);

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
    const data = artifact.data || FORECAST_DATA[artifact.crop] || FORECAST_DATA['Tomato'];
    const cropName = artifact.crop || 'Tomato';
    const centre = artifact.centre || activeCenter || 'DAMBULLA';

    // Calculate or extract key figures from data if available
    const firstActual = data.find(d => d.actual != null)?.actual || 249.39;
    const day7Forecast = data[7]?.forecast || data[7]?.actual || 103.0;
    const day14Forecast = data[data.length - 1]?.forecast || data[data.length - 1]?.actual || 245.48;

    const handleDownloadPDF = () => {
      setDownloading(true);
      setDownloaded(false);
      setTimeout(() => {
        try {
          generateCropForecastPDF({
            crop: cropName,
            centre: centre,
            currentPrice: firstActual,
            day7Price: day7Forecast,
            day14Price: day14Forecast,
            anomalyStatus: 'SURPLUS DETECTED',
            anomalyDetail: '51.08 T above absorption',
            forecastData: data,
            analysisText: artifact.analysisText || '',
          });
          setDownloaded(true);
          setTimeout(() => setDownloaded(false), 3000);
        } finally {
          setDownloading(false);
        }
      }, 100);
    };

    return (
      <div className="right-panel slide-in">
        <div className="right-panel-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>📈 {cropName} Forecast</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <button
              className="panel-pdf-quick-btn"
              onClick={handleDownloadPDF}
              disabled={downloading}
              title="Download 14-Day Forecast PDF"
            >
              <FileDown size={13} />
              <span>{downloading ? '…' : 'PDF'}</span>
            </button>
            <button className="icon-btn" onClick={onClose}><X size={14} /></button>
          </div>
        </div>

        <div className="right-panel-body">
          <div className="forecast-panel-card">
            <div className="forecast-panel-card-title">{cropName} — 14-Day Prophet Forecast (LKR/kg)</div>
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

          {/* Key Metric cards */}
          <div className="forecast-panel-card">
            <div className="forecast-panel-card-title">Day 7 Projection</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent)' }}>
              LKR {typeof day7Forecast === 'number' ? day7Forecast.toFixed(0) : '103'}/kg
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              ↓ 12.7% from today
            </div>
          </div>

          <div className="forecast-panel-card">
            <div className="forecast-panel-card-title">Day 14 Projection</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent)' }}>
              LKR {typeof day14Forecast === 'number' ? day14Forecast.toFixed(0) : '98'}/kg
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              ↓ 16.9% from today
            </div>
          </div>

          <div className="forecast-panel-card">
            <div className="forecast-panel-card-title">Anomaly Status</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--red)' }}>
              ● SURPLUS DETECTED
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              51.08 T above absorption
            </div>
          </div>

          {/* Dedicated PDF Download Action Block */}
          <div className="forecast-download-card">
            <div className="forecast-download-title">📥 Export Official Advisory Dossier</div>
            <div className="forecast-download-sub">
              Includes 14-day Prophet forecast curve, price bands, market anomalies &amp; stakeholder recommendations.
            </div>
            <button
              className={`download-forecast-full-btn ${downloading ? 'loading' : ''} ${downloaded ? 'success' : ''}`}
              onClick={handleDownloadPDF}
              disabled={downloading}
            >
              {downloaded ? <CheckCircle size={15} /> : <FileDown size={15} />}
              <span>
                {downloading
                  ? 'Generating PDF Report…'
                  : downloaded
                  ? 'Downloaded Successfully!'
                  : `Download ${cropName} Forecast PDF`}
              </span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}


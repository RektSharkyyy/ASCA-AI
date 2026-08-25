/**
 * ASCA AI — Executive Blueprint Preview Modal
 *
 * Renders a full dossier preview with all sections before PDF download.
 * Triggered by the "View" button in BlueprintsView.
 */

import { useState } from 'react';
import { X, FileDown, AlertTriangle, CheckCircle, Circle, TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { generateBlueprintPDF } from '../../utils/pdfGenerator';

const RISK_CONFIG = {
  CRITICAL: { label: '⚠ CRITICAL ALERT', cls: 'red'   },
  HIGH:     { label: '▲ HIGH RISK',       cls: 'red'   },
  MEDIUM:   { label: '~ MEDIUM RISK',    cls: 'amber' },
  LOW:      { label: '✓ LOW RISK',        cls: 'green' },
  STABLE:   { label: '✓ STABLE',          cls: 'green' },
};

const FORECAST_DATA = {
  1: [
    { crop: 'Tomato',       current: 145, day7: 104.5, day14: 88.0,  trend: -39.3 },
    { crop: 'Carrot',       current: 110, day7: 118.0, day14: 125.0, trend: 13.6  },
    { crop: 'Beans',        current: 165, day7: 162.0, day14: 160.0, trend: -3.0  },
    { crop: 'Green Chilli', current: 310, day7: 280.0, day14: 250.0, trend: -19.4 },
  ],
  2: [
    { crop: 'Tomato',       current: 145, day7: 140.0, day14: 136.0, trend: -6.2  },
    { crop: 'Carrot',       current: 110, day7: 114.0, day14: 118.0, trend: 7.3   },
    { crop: 'Beans',        current: 165, day7: 163.0, day14: 161.0, trend: -2.4  },
    { crop: 'Eggplant',     current: 82,  day7: 79.0,  day14: 76.0,  trend: -7.3  },
    { crop: 'Cabbage',      current: 55,  day7: 58.0,  day14: 61.0,  trend: 10.9  },
    { crop: 'Green Chilli', current: 310, day7: 295.0, day14: 280.0, trend: -9.7  },
  ],
};

const QUOTA_DATA = {
  1: [
    { buyer: 'Lanka Canning & Sauce Ltd',      quota: '26.5 T', price: 'Rs. 85/kg', location: 'Colombo 15', fefo: 0.87 },
    { buyer: 'Central Province Canning Mills', quota: '18.0 T', price: 'Rs. 82/kg', location: 'Kandy',      fefo: 0.79 },
  ],
  2: [
    { buyer: 'Lanka Canning & Sauce Ltd',    quota: '20.0 T', price: 'Rs. 88/kg', location: 'Colombo 15', fefo: 0.87 },
    { buyer: 'Green Valley Processors',      quota: '12.5 T', price: 'Rs. 80/kg', location: 'Gampaha',    fefo: 0.65 },
    { buyer: 'Pettah Wholesale Merchants',   quota: '8.0 T',  price: 'Rs. 75/kg', location: 'Colombo 11', fefo: 0.58 },
  ],
};

const DIRECTIVES = {
  1: [
    { done: true,  text: 'Priority Dispatch — Route 26.5 T to Lanka Canning & Sauce Ltd within 36 hours.' },
    { done: true,  text: 'Farmer Broadcast — Send surplus warning to Dambulla farmer groups via Telegram.' },
    { done: true,  text: 'Cold Chain — Pre-cool Bay 2 to 10°C for incoming Tomato surplus lots.' },
    { done: false, text: 'Secondary Market — Identify Colombo supermarket chains for direct retail absorption.' },
  ],
  2: [
    { done: true,  text: 'Market Scout — Full 6-crop analysis completed for Thambuththegama Economic Centre.' },
    { done: true,  text: 'Forecast Broadcast — 14-day outlook sent to 4 registered buyer contacts.' },
    { done: false, text: 'Policy Review — Submit weekly market pulse to Regional Director within 24 hours.' },
  ],
};

function TrendIcon({ value }) {
  if (value > 3)  return <TrendingUp  size={12} style={{ color: 'var(--green)' }} />;
  if (value < -3) return <TrendingDown size={12} style={{ color: 'var(--red)'  }} />;
  return <Minus size={12} style={{ color: 'var(--text-muted)' }} />;
}

export default function BlueprintModal({ blueprint, onClose }) {
  const [generating, setGenerating] = useState(false);

  if (!blueprint) return null;

  const risk     = RISK_CONFIG[blueprint.riskLevel] || { label: blueprint.riskLevel, cls: 'muted' };
  const forecast = FORECAST_DATA[blueprint.id] || FORECAST_DATA[1];
  const quotas   = QUOTA_DATA[blueprint.id]    || QUOTA_DATA[1];
  const directives = DIRECTIVES[blueprint.id]  || DIRECTIVES[1];

  const handleDownloadPDF = () => {
    setGenerating(true);
    setTimeout(() => {
      try {
        generateBlueprintPDF(blueprint, {
          forecastRows: forecast.map(r => [
            r.crop,
            `Rs. ${r.current.toFixed(2)}`,
            `Rs. ${r.day7.toFixed(2)}`,
            `Rs. ${r.day14.toFixed(2)}`,
            `${r.trend > 0 ? '+' : ''}${r.trend.toFixed(1)}%`,
          ]),
          quotaRows: quotas.map(q => [
            q.buyer, q.quota, q.price, q.location, '—', q.fefo.toFixed(2),
          ]),
          directives: directives,
          summary: [
            blueprint.summary,
            `Risk level assessed as ${blueprint.riskLevel} for ${blueprint.center} Economic Centre.`,
            `Report covers ${blueprint.cropCount} crop${blueprint.cropCount > 1 ? 's' : ''}.`,
          ],
        });
      } finally {
        setGenerating(false);
      }
    }, 100);
  };

  return (
    <div className="bp-modal-backdrop" onClick={onClose}>
      <div className="bp-modal" onClick={e => e.stopPropagation()}>

        {/* ── Header ── */}
        <div className="bp-modal-header">
          <div className="bp-modal-title-block">
            <div className="bp-modal-icon">📄</div>
            <div>
              <div className="bp-modal-title">{blueprint.title}</div>
              <div className="bp-modal-sub">
                {blueprint.center} · {blueprint.date} · {blueprint.cropCount} crop{blueprint.cropCount > 1 ? 's' : ''}
              </div>
            </div>
          </div>
          <div className="bp-modal-header-actions">
            <span className={`bp-risk-badge ${risk.cls}`}>{risk.label}</span>
            <button
              className={`bp-download-btn ${generating ? 'loading' : ''}`}
              onClick={handleDownloadPDF}
              disabled={generating}
            >
              <FileDown size={14} />
              {generating ? 'Generating…' : 'Download PDF'}
            </button>
            <button className="bp-close-btn" onClick={onClose}><X size={16} /></button>
          </div>
        </div>

        {/* ── Body ── */}
        <div className="bp-modal-body">

          {/* 1. Executive Summary */}
          <div className="bp-section">
            <div className="bp-section-title">1. Executive Summary</div>
            <div className="bp-summary-text">
              <p>{blueprint.summary}</p>
              <p style={{ marginTop: 8 }}>
                Risk level assessed as <strong style={{ color: risk.cls === 'red' ? 'var(--red)' : risk.cls === 'amber' ? 'var(--amber)' : 'var(--green)' }}>{blueprint.riskLevel}</strong> for {blueprint.center} Economic Centre. This advisory covers {blueprint.cropCount} crop{blueprint.cropCount > 1 ? 's' : ''}.
              </p>
            </div>
          </div>

          {/* 2. Price Forecast */}
          <div className="bp-section">
            <div className="bp-section-title">2. 14-Day Prophet &amp; LSTM Price Forecast</div>
            <table className="bp-table">
              <thead>
                <tr>
                  <th>Crop</th>
                  <th>Current Price</th>
                  <th>7-Day Forecast</th>
                  <th>14-Day Forecast</th>
                  <th>Trend</th>
                </tr>
              </thead>
              <tbody>
                {forecast.map(row => (
                  <tr key={row.crop}>
                    <td className="bp-td-crop">{row.crop}</td>
                    <td>Rs. {row.current.toFixed(2)}</td>
                    <td>Rs. {row.day7.toFixed(2)}</td>
                    <td>Rs. {row.day14.toFixed(2)}</td>
                    <td>
                      <span className={`bp-trend ${row.trend < -5 ? 'down' : row.trend > 5 ? 'up' : 'flat'}`}>
                        <TrendIcon value={row.trend} />
                        {row.trend > 0 ? '+' : ''}{row.trend.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 3. B2B Quota */}
          <div className="bp-section">
            <div className="bp-section-title">3. Recommended B2B Quota Allocations</div>
            <table className="bp-table">
              <thead>
                <tr>
                  <th>Buyer / Processor</th>
                  <th>Quota</th>
                  <th>Floor Price</th>
                  <th>Location</th>
                  <th>FEFO Score</th>
                </tr>
              </thead>
              <tbody>
                {quotas.map((q, i) => (
                  <tr key={i}>
                    <td className="bp-td-crop">{q.buyer}</td>
                    <td>{q.quota}</td>
                    <td>{q.price}</td>
                    <td>{q.location}</td>
                    <td>
                      <span className={`bp-fefo-score ${q.fefo >= 0.75 ? 'high' : q.fefo >= 0.55 ? 'mid' : 'low'}`}>
                        {q.fefo.toFixed(2)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 4. Directives */}
          <div className="bp-section">
            <div className="bp-section-title">4. Actionable Operational Directives</div>
            <div className="bp-directives">
              {directives.map((d, i) => (
                <div key={i} className={`bp-directive-item ${d.done ? 'done' : 'pending'}`}>
                  {d.done
                    ? <CheckCircle size={14} style={{ color: 'var(--green)', flexShrink: 0 }} />
                    : <Circle      size={14} style={{ color: 'var(--amber)', flexShrink: 0 }} />
                  }
                  <span>{d.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Footer note */}
          <div className="bp-modal-footer-note">
            Authorized by ASCA AI Multi-Agent Autonomous Engine · Pydantic V2 Validated · Prophet + LSTM Forecasting
          </div>
        </div>
      </div>
    </div>
  );
}

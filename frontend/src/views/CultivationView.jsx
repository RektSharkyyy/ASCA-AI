/**
 * ASCA AI — 6-Month Crop Recommendation & Agronomy Planner
 *
 * Provides DOA-aligned:
 *   • AI-ranked crop recommendations by farm parameters
 *   • Step-by-step 6-stage cultivation lifecycle guide (24 weeks)
 *   • Fertilizer & nutrition schedule (Basal, Top Dressing 1/2/3)
 *   • Pest & disease identification with organic + IPM controls
 *   • Downloadable PDF cultivation booklet
 */

import { useState, useCallback } from 'react';
import {
  Leaf, FlaskConical, ShieldCheck, TrendingUp,
  ChevronRight, ChevronDown, Download, Search,
  Sprout, MapPin, Droplets, DollarSign,
} from 'lucide-react';
import { getCropRecommendations, getCultivationGuide } from '../api/client';
import { generateCultivationGuidePDF } from '../utils/pdfGenerator';

// ─── Constants ────────────────────────────────────────────────────────────
const SEASONS   = ['Maha', 'Yala'];
const SOIL_TYPES = [
  'Reddish Brown Earth',
  'Sandy Loam',
  'Clay Loam',
  'Alluvial',
];
const WATER_SOURCES = [
  'Agrowell / Tube Well',
  'Irrigation Canal',
  'Rainfed',
  'Drip Irrigation',
];

const RISK_COLORS = {
  'Very Low': 'var(--green)',
  'Low':      'var(--green)',
  'Medium':   'var(--amber)',
  'High':     'var(--red)',
};
const DEMAND_COLORS = {
  'Very High': 'var(--green)',
  'High':      'var(--accent)',
  'Medium':    'var(--amber)',
  'Low':       'var(--text-muted)',
};

const PEST_TYPE_COLOR = { pest: 'var(--amber)', disease: 'var(--red)' };
const PEST_TYPE_LABEL = { pest: '🐛 Pest', disease: '🦠 Disease' };

// ─── Sub-components ───────────────────────────────────────────────────────

function GuideTabTimeline({ stages }) {
  const [open, setOpen] = useState(0);
  return (
    <div className="cult-timeline">
      {stages.map((s, idx) => (
        <div key={idx} className={`cult-stage-block ${open === idx ? 'expanded' : ''}`}>
          <div className="cult-stage-header" onClick={() => setOpen(open === idx ? -1 : idx)}>
            <div className="stage-num">Stage {s.stage}</div>
            <div className="stage-title">{s.name}</div>
            <div className="stage-weeks">{s.weeks}</div>
            {open === idx ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </div>
          {open === idx && (
            <ul className="cult-stage-actions">
              {s.actions.map((a, i) => (
                <li key={i}>
                  <span className="stage-bullet">✓</span>
                  {a}
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

function GuideTabFertilizer({ schedule }) {
  const sections = Object.entries(schedule);
  return (
    <div className="cult-fertilizer">
      {sections.map(([key, val]) => (
        <div key={key} className="fert-section">
          <div className="fert-title">
            <FlaskConical size={13} />
            {key === 'basal'
              ? '🌱 Basal Dressing (Foundation Nutrition)'
              : key === 'top_dressing_1'
              ? '💧 Top Dressing 1 (Early Growth)'
              : key === 'top_dressing_2'
              ? '🌸 Top Dressing 2 (Flowering Stage)'
              : '🌾 Top Dressing 3 (Post-First Harvest)'}
            <span className="fert-timing">— {val.timing}</span>
          </div>
          <div className="fert-table-wrap">
            <table className="fert-table">
              <thead>
                <tr>
                  <th>Input / Fertilizer</th>
                  <th>Quantity per Acre</th>
                  <th>Application Method</th>
                </tr>
              </thead>
              <tbody>
                {val.inputs.map((row, i) => (
                  <tr key={i}>
                    <td className="fert-name">{row.name}</td>
                    <td className="fert-qty">{row.quantity}</td>
                    <td className="fert-method">{row.method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}

function GuideTabPests({ pests }) {
  const [open, setOpen] = useState(null);
  return (
    <div className="cult-pest-list">
      {pests.map((p, i) => (
        <div key={i} className={`pest-block ${open === i ? 'open' : ''}`}>
          <div className="pest-header" onClick={() => setOpen(open === i ? null : i)}>
            <span className="pest-type-badge" style={{ color: PEST_TYPE_COLOR[p.type] }}>
              {PEST_TYPE_LABEL[p.type]}
            </span>
            <div>
              <div className="pest-name">{p.name}</div>
              {p.category && <div className="pest-sub">{p.category}</div>}
            </div>
            {open === i ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </div>
          {open === i && (
            <div className="pest-detail">
              <div className="pest-section symptoms">
                <div className="plabel">🔍 Symptoms & Identification</div>
                <div className="ptext">{p.symptoms}</div>
              </div>
              <div className="pest-section organic">
                <div className="plabel">🌿 Organic / Cultural Control</div>
                <div className="ptext">{p.organic_control}</div>
              </div>
              <div className="pest-section chemical">
                <div className="plabel">⚗️ Approved IPM / Chemical Control</div>
                <div className="ptext">{p.chemical_control}</div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function CropGuideModal({ guide, farmParams, onClose }) {
  const [tab, setTab] = useState('timeline');

  const handlePDF = () => generateCultivationGuidePDF(guide, farmParams);

  return (
    <div className="bp-modal-backdrop" onClick={onClose}>
      <div className="cult-guide-modal" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="cult-guide-header">
          <div className="cult-guide-crop-id">
            <span className="crop-emoji-lg">{guide.emoji}</span>
            <div>
              <div className="cult-guide-crop-name">{guide.name} — Cultivation Guide</div>
              <div className="cult-guide-crop-sub">
                {guide.botanical_name ? <em>{guide.botanical_name} · </em> : ''}Growth: {guide.growth_days} Days · Spacing: {guide.plant_spacing_cm} cm · pH: {guide.ideal_ph}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="cult-pdf-btn" onClick={handlePDF}>
              <Download size={13} /> Download PDF
            </button>
            <button className="bp-close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="cult-guide-tabs">
          <button className={`cult-tab ${tab === 'timeline' ? 'active' : ''}`} onClick={() => setTab('timeline')}>
            📅 Lifecycle Timeline
          </button>
          <button className={`cult-tab ${tab === 'fertilizer' ? 'active' : ''}`} onClick={() => setTab('fertilizer')}>
            🧪 Fertilizer Schedule
          </button>
          <button className={`cult-tab ${tab === 'pests' ? 'active' : ''}`} onClick={() => setTab('pests')}>
            🛡️ Pest &amp; Disease Shield
          </button>
        </div>

        {/* Tab content */}
        <div className="cult-guide-body">
          {tab === 'timeline'    && <GuideTabTimeline  stages={guide.timeline_stages} />}
          {tab === 'fertilizer'  && <GuideTabFertilizer schedule={guide.fertilizer_schedule} />}
          {tab === 'pests'       && <GuideTabPests pests={guide.pests_and_diseases} />}
        </div>
      </div>
    </div>
  );
}

// ─── Recommendation Card ─────────────────────────────────────────────────────

function CropCard({ rec, rank, onViewGuide }) {
  const fmt = (n) => `LKR ${Number(n).toLocaleString('en-LK')}`;
  return (
    <div className="cult-rec-card">
      <div className="rec-rank">#{rank}</div>
      <div className="rec-emoji">{rec.emoji}</div>
      <div className="rec-name">{rec.name}</div>
      {rec.botanical_name && <div className="rec-sub"><em>{rec.botanical_name}</em></div>}

      <div className="rec-badges">
        <span className="rec-badge" style={{ color: DEMAND_COLORS[rec.market_demand] || 'var(--accent)' }}>
          {rec.market_demand} Demand
        </span>
        <span className="rec-badge" style={{ color: RISK_COLORS[rec.risk_level] || 'var(--amber)' }}>
          {rec.risk_level} Risk
        </span>
        <span className="rec-badge" style={{ color: rec.seasonal_fit ? 'var(--green)' : 'var(--amber)' }}>
          {rec.seasonal_fit ? '✓ Season Fit' : '⚠ Off-Season'}
        </span>
      </div>

      <div className="rec-metrics">
        <div className="rec-metric">
          <span className="k">Avg Yield</span>
          <span className="v accent">{rec.avg_yield_tons} Tons</span>
        </div>
        <div className="rec-metric">
          <span className="k">Growth Days</span>
          <span className="v">{rec.growth_days} Days</span>
        </div>
        <div className="rec-metric">
          <span className="k">Wholesale Price</span>
          <span className="v">Rs. {rec.avg_wholesale_price_lkr_per_kg}/kg</span>
        </div>
        <div className="rec-metric">
          <span className="k">Est. ROI</span>
          <span className="v green">{rec.roi_estimate_pct}%</span>
        </div>
      </div>

      <div className="rec-financials">
        <div>
          <div className="fin-label">Gross Revenue</div>
          <div className="fin-val green">{fmt(rec.estimated_gross_revenue_lkr)}</div>
        </div>
        <div className="fin-div" />
        <div>
          <div className="fin-label">Est. Net Profit</div>
          <div className="fin-val accent">{fmt(rec.estimated_net_profit_lkr)}</div>
        </div>
        <div className="fin-div" />
        <div>
          <div className="fin-label">Input Cost</div>
          <div className="fin-val">{fmt(rec.estimated_cost_lkr)}</div>
        </div>
      </div>

      <button className="cult-view-btn" onClick={() => onViewGuide(rec.id)}>
        <Leaf size={13} /> View Full Cultivation Guide
      </button>
    </div>
  );
}

// ─── Main View ────────────────────────────────────────────────────────────────

export default function CultivationView({ activeCenter = 'DAMBULLA' }) {
  const [season,     setSeason]     = useState('Maha');
  const [soilType,   setSoilType]   = useState('Reddish Brown Earth');
  const [waterSrc,   setWaterSrc]   = useState('Agrowell / Tube Well');
  const [landAcres,  setLandAcres]  = useState(1.0);
  const [recs,       setRecs]       = useState([]);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);
  const [guide,      setGuide]      = useState(null);
  const [guideLoading, setGuideLoading] = useState(false);
  const [searched,   setSearched]   = useState(false);

  const farmParams = { centre_id: activeCenter, season, soil_type: soilType, water_source: waterSrc, land_area_acres: landAcres };

  const handleRecommend = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const data = await getCropRecommendations(farmParams);
      setRecs(data.recommendations || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [activeCenter, season, soilType, waterSrc, landAcres]);

  const handleViewGuide = async (cropId) => {
    setGuideLoading(true);
    try {
      const data = await getCultivationGuide(cropId);
      setGuide(data);
    } catch (err) {
      alert(`Could not load guide: ${err.message}`);
    } finally {
      setGuideLoading(false);
    }
  };

  return (
    <div className="cult-view">
      {/* Header */}
      <div className="analytics-header">
        <div>
          <div className="view-title">🌱 6-Month Crop Recommendation &amp; Agronomy Planner</div>
          <div className="view-subtitle">DOA-aligned cultivation guide · Seasonal planting intelligence · Fertilizer &amp; IPM protocols</div>
        </div>
      </div>

      {/* Farm Setup Panel */}
      <div className="cult-setup-panel">
        <div className="cult-setup-title">
          <Sprout size={15} /> Farm Setup — Configure Your Parameters
        </div>
        <div className="cult-setup-grid">
          <div className="cult-field">
            <label className="cult-label">
              <MapPin size={11} /> Economic Centre
            </label>
            <div className="cult-static-val">{activeCenter === 'DAMBULLA' ? 'Dambulla Economic Centre' : 'Thambuththegama Economic Centre'}</div>
          </div>
          <div className="cult-field">
            <label className="cult-label">🌦️ Target Season</label>
            <select className="cult-select" value={season} onChange={e => setSeason(e.target.value)}>
              {SEASONS.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div className="cult-field">
            <label className="cult-label">🪨 Primary Soil Type</label>
            <select className="cult-select" value={soilType} onChange={e => setSoilType(e.target.value)}>
              {SOIL_TYPES.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div className="cult-field">
            <label className="cult-label">
              <Droplets size={11} /> Water Source
            </label>
            <select className="cult-select" value={waterSrc} onChange={e => setWaterSrc(e.target.value)}>
              {WATER_SOURCES.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div className="cult-field">
            <label className="cult-label">📐 Cultivable Land Area</label>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input
                type="number"
                className="cult-input"
                min="0.1"
                max="100"
                step="0.25"
                value={landAcres}
                onChange={e => setLandAcres(Number(e.target.value))}
              />
              <span className="cult-unit">Acres</span>
            </div>
            <input
              type="range"
              min="0.25"
              max="20"
              step="0.25"
              value={landAcres}
              onChange={e => setLandAcres(Number(e.target.value))}
              className="quota-slider"
            />
          </div>
          <div className="cult-field" style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button
              className="cult-recommend-btn"
              onClick={handleRecommend}
              disabled={loading}
            >
              {loading ? '⏳ Analyzing…' : <><Search size={14} /> Get AI Crop Recommendations</>}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="login-error">⚠️ {error}</div>
      )}

      {guideLoading && (
        <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)', fontSize: 13 }}>
          ⏳ Loading cultivation guide…
        </div>
      )}

      {/* Results */}
      {!loading && searched && recs.length === 0 && !error && (
        <div className="quota-empty-state">
          <div className="icon">🌾</div>
          <div className="title">No recommendations found for these parameters</div>
          <div className="sub">Try changing the season or soil type and search again.</div>
        </div>
      )}

      {!loading && recs.length > 0 && (
        <>
          <div className="cult-results-header">
            <TrendingUp size={14} />
            <span>Top {recs.length} AI-Ranked Crop Recommendations for {landAcres} Acre{landAcres !== 1 ? 's' : ''} — {season} Season, {activeCenter === 'DAMBULLA' ? 'Dambulla' : 'Thambuththegama'}</span>
          </div>
          <div className="cult-rec-grid">
            {recs.map((r, idx) => (
              <CropCard
                key={r.id}
                rec={r}
                rank={idx + 1}
                onViewGuide={handleViewGuide}
              />
            ))}
          </div>
        </>
      )}

      {/* Deep-dive guide modal */}
      {guide && (
        <CropGuideModal
          guide={guide}
          farmParams={farmParams}
          onClose={() => setGuide(null)}
        />
      )}
    </div>
  );
}

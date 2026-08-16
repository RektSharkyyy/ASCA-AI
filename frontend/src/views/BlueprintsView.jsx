import { FileDown, Eye, Calendar, AlertTriangle } from 'lucide-react';
import { BLUEPRINTS } from '../data/mockData';

const RISK_COLOR = { CRITICAL: 'var(--red)', HIGH: 'var(--red)', MEDIUM: 'var(--amber)', LOW: 'var(--green)' };
const RISK_BG = { CRITICAL: 'var(--red-dim)', HIGH: 'var(--red-dim)', MEDIUM: 'var(--amber-dim)', LOW: 'var(--green-dim)' };
const STATUS_COLOR = { Final: 'var(--green)', Draft: 'var(--amber)' };

export default function BlueprintsView() {
  return (
    <div className="blueprints-view">
      <div>
        <div className="view-title">📄 Executive Blueprints</div>
        <div className="view-subtitle" style={{ marginTop: 4 }}>Pydantic-validated advisory dossiers · PDF-exportable</div>
      </div>

      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="stat-card">
          <div className="stat-card-label">Total Blueprints</div>
          <div className="stat-card-value accent">{BLUEPRINTS.length}</div>
          <div className="stat-card-sub">All time</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Finalized</div>
          <div className="stat-card-value green">{BLUEPRINTS.filter(b => b.status === 'Final').length}</div>
          <div className="stat-card-sub">PDF-ready</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Critical Alerts</div>
          <div className="stat-card-value red">{BLUEPRINTS.filter(b => b.riskLevel === 'CRITICAL' || b.riskLevel === 'HIGH').length}</div>
          <div className="stat-card-sub">HIGH or CRITICAL</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Crops Analyzed</div>
          <div className="stat-card-value amber">14</div>
          <div className="stat-card-sub">This month</div>
        </div>
      </div>

      {BLUEPRINTS.map(bp => (
        <div key={bp.id} className="blueprint-item">
          <div className="blueprint-icon">📄</div>
          <div className="blueprint-info">
            <div className="blueprint-title">{bp.title}</div>
            <div className="blueprint-meta">
              <Calendar size={10} style={{ display: 'inline', marginRight: 3 }} />{bp.date}
              &nbsp;·&nbsp;{bp.center}
              &nbsp;·&nbsp;{bp.cropCount} crop{bp.cropCount > 1 ? 's' : ''}
              &nbsp;·&nbsp;
              <span style={{ color: STATUS_COLOR[bp.status], fontWeight: 600 }}>{bp.status}</span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>{bp.summary}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{
              padding: '2px 8px',
              borderRadius: 99,
              fontSize: 10,
              fontWeight: 700,
              background: RISK_BG[bp.riskLevel],
              color: RISK_COLOR[bp.riskLevel],
              whiteSpace: 'nowrap',
            }}>
              {bp.riskLevel === 'CRITICAL' && <AlertTriangle size={9} style={{ display: 'inline', marginRight: 3 }} />}
              {bp.riskLevel}
            </span>
          </div>
          <div className="blueprint-actions">
            <button className="action-btn primary"><Eye size={12} /> View</button>
            <button className="action-btn"><FileDown size={12} /> PDF</button>
          </div>
        </div>
      ))}
    </div>
  );
}

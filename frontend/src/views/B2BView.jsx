import { useState } from 'react';
import { MapPin, Mail, Phone, Package } from 'lucide-react';
import { B2B_BUYERS, CROPS } from '../data/mockData';

const fefoClass = score => score >= 0.75 ? 'high' : score >= 0.55 ? 'mid' : 'low';
const STATUS_COLOR = {
  'Active Negotiation': 'var(--green)',
  'Matched': 'var(--accent)',
  'Contract Pending': 'var(--amber)',
  'Available': 'var(--text-muted)',
};

export default function B2BView() {
  const [filter, setFilter] = useState('All');

  const crops = ['All', ...CROPS];
  const filtered = filter === 'All' ? B2B_BUYERS : B2B_BUYERS.filter(b => b.crop.toLowerCase().includes(filter.toLowerCase()));

  return (
    <div className="b2b-view">
      <div className="analytics-header">
        <div>
          <div className="view-title">🤝 B2B Match Directory</div>
          <div className="view-subtitle">FEFO-ranked food processors & buyers · Sorted by risk score</div>
        </div>
        <div className="crop-tabs">
          {crops.map(c => (
            <button key={c} className={`crop-tab ${filter === c ? 'active' : ''}`} onClick={() => setFilter(c)}>{c}</button>
          ))}
        </div>
      </div>

      {/* Summary row */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="stat-card">
          <div className="stat-card-label">Total Buyers</div>
          <div className="stat-card-value accent">{B2B_BUYERS.length}</div>
          <div className="stat-card-sub">Registered in ChromaDB</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Active Matches</div>
          <div className="stat-card-value green">4</div>
          <div className="stat-card-sub">This session</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Total Volume Matched</div>
          <div className="stat-card-value amber">119.5 T</div>
          <div className="stat-card-sub">Across all crops</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Avg FEFO Score</div>
          <div className="stat-card-value accent">0.75</div>
          <div className="stat-card-sub">FEFO Risk Engine</div>
        </div>
      </div>

      {/* Buyer cards */}
      <div className="b2b-grid">
        {filtered.map(buyer => (
          <div key={buyer.id} className="b2b-card">
            <div className="b2b-card-header">
              <div>
                <div className="b2b-card-name">{buyer.name}</div>
                <div className="b2b-card-location"><MapPin size={10} style={{ display: 'inline', marginRight: 3 }} />{buyer.location}</div>
              </div>
              <div className={`fefo-badge ${fefoClass(buyer.fefoScore)}`}>
                FEFO {buyer.fefoScore.toFixed(2)}
              </div>
            </div>

            <div style={{ fontSize: 11, color: STATUS_COLOR[buyer.status] || 'var(--text-muted)', fontWeight: 600, marginBottom: 6 }}>
              ● {buyer.status}
            </div>

            <div className="b2b-meta-grid">
              <div className="b2b-meta-item">
                <div className="key">Crop</div>
                <div className="val">{buyer.crop}</div>
              </div>
              <div className="b2b-meta-item">
                <div className="key">Volume</div>
                <div className="val">{buyer.volume} T</div>
              </div>
              <div className="b2b-meta-item">
                <div className="key">Shelf Days</div>
                <div className="val" style={{ color: buyer.shelfDaysRemain <= 6 ? 'var(--red)' : 'inherit' }}>
                  {buyer.shelfDaysRemain} days
                </div>
              </div>
              <div className="b2b-meta-item">
                <div className="key">Distance</div>
                <div className="val">{buyer.distanceKm} km</div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border)', marginTop: 10, paddingTop: 8, display: 'flex', gap: 10, fontSize: 11, color: 'var(--text-muted)' }}>
              <span><Mail size={10} style={{ marginRight: 3 }} />{buyer.contactEmail}</span>
            </div>

            <div className="inline-actions" style={{ marginTop: 8 }}>
              <button className="action-btn primary">🤝 Negotiate</button>
              <button className="action-btn">📱 Send Alert</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

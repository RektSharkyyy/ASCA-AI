import { useState, useEffect, useCallback } from 'react';
import { MapPin, Mail } from 'lucide-react';
import { getBuyers, getB2BMatches } from '../api/client';

const fefoClass = score => score >= 0.75 ? 'high' : score >= 0.55 ? 'mid' : 'low';

const CROP_FILTER_LIST = ['All', 'Tomato', 'Carrot', 'Beans', 'Eggplant', 'Cabbage', 'Green Chilli'];

const Spinner = () => (
  <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', fontSize: 13 }}>
    ⏳ Loading from backend…
  </div>
);

export default function B2BView({ activeCenter = 'DAMBULLA' }) {
  const [filter, setFilter]       = useState('All');
  const [buyers, setBuyers]       = useState([]);
  const [matches, setMatches]     = useState(null);   // B2BMatchResponse
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [buyersData, matchData] = await Promise.all([
        getBuyers(activeCenter),
        getB2BMatches(activeCenter),
      ]);
      setBuyers(buyersData.buyers ?? []);
      setMatches(matchData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [activeCenter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Filter buyers by preferred crop label
  const filtered = filter === 'All'
    ? buyers
    : buyers.filter(b =>
        b.preferred_crop_labels?.some(l =>
          l.toLowerCase().includes(filter.toLowerCase())
        )
      );

  return (
    <div className="b2b-view">
      <div className="analytics-header">
        <div>
          <div className="view-title">🤝 B2B Match Directory</div>
          <div className="view-subtitle">FEFO-ranked food processors &amp; buyers · Sorted by risk score</div>
        </div>
        <div className="crop-tabs">
          {CROP_FILTER_LIST.map(c => (
            <button key={c} className={`crop-tab ${filter === c ? 'active' : ''}`} onClick={() => setFilter(c)}>{c}</button>
          ))}
        </div>
      </div>

      {/* Summary row */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="stat-card">
          <div className="stat-card-label">Total Buyers</div>
          <div className="stat-card-value accent">{buyers.length}</div>
          <div className="stat-card-sub">Registered in ChromaDB</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Surplus Anomalies</div>
          <div className="stat-card-value green">{matches?.anomaly_count ?? '—'}</div>
          <div className="stat-card-sub">Detected this scan</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Total Volume Matched</div>
          <div className="stat-card-value amber">
            {matches?.total_volume_tons != null ? `${matches.total_volume_tons} T` : '—'}
          </div>
          <div className="stat-card-sub">Across all crops</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Avg FEFO Score</div>
          <div className="stat-card-value accent">
            {matches?.average_fefo_score != null ? matches.average_fefo_score.toFixed(2) : '—'}
          </div>
          <div className="stat-card-sub">FEFO Risk Engine</div>
        </div>
      </div>

      {loading && <Spinner />}
      {error   && (
        <div style={{ color: 'var(--red)', padding: 20, fontSize: 12 }}>
          ⚠️ Could not load B2B data: {error}
        </div>
      )}

      {/* Buyer cards */}
      {!loading && !error && (
        <div className="b2b-grid">
          {filtered.length === 0 && (
            <div style={{ color: 'var(--text-muted)', padding: 24, fontSize: 13 }}>
              No buyers found for the selected crop filter.
            </div>
          )}
          {filtered.map(buyer => (
            <div key={buyer.buyer_code} className="b2b-card">
              <div className="b2b-card-header">
                <div>
                  <div className="b2b-card-name">{buyer.company_name}</div>
                  <div className="b2b-card-location">
                    <MapPin size={10} style={{ display: 'inline', marginRight: 3 }} />
                    {buyer.location}
                  </div>
                </div>
                {/* Show FEFO score from matches if available */}
                {(() => {
                  const match = matches?.matches?.find(m => m.buyer_code === buyer.buyer_code);
                  const score = match?.fefo_risk_score;
                  return score != null ? (
                    <div className={`fefo-badge ${fefoClass(score)}`}>
                      FEFO {score.toFixed(2)}
                    </div>
                  ) : (
                    <div className="fefo-badge low">Registered</div>
                  );
                })()}
              </div>

              <div className="b2b-meta-grid">
                <div className="b2b-meta-item">
                  <div className="key">Type</div>
                  <div className="val">{buyer.buyer_type}</div>
                </div>
                <div className="b2b-meta-item">
                  <div className="key">Capacity</div>
                  <div className="val">{buyer.daily_capacity_tons} T/day</div>
                </div>
                <div className="b2b-meta-item">
                  <div className="key">Crops</div>
                  <div className="val">{(buyer.preferred_crop_labels ?? []).join(', ') || '—'}</div>
                </div>
                {buyer.distance_km != null && (
                  <div className="b2b-meta-item">
                    <div className="key">Distance</div>
                    <div className="val">{buyer.distance_km} km</div>
                  </div>
                )}
              </div>

              {/* Show match details if this buyer has an active match */}
              {(() => {
                const match = matches?.matches?.find(m => m.buyer_code === buyer.buyer_code);
                return match ? (
                  <div style={{ fontSize: 11, color: 'var(--green)', marginTop: 6, fontWeight: 600 }}>
                    ✅ Matched — {match.matched_volume_tons} T of {match.crop_label}
                  </div>
                ) : null;
              })()}

              <div className="inline-actions" style={{ marginTop: 8 }}>
                <button className="action-btn primary">🤝 Negotiate</button>
                <button className="action-btn">📱 Send Alert</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

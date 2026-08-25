import { useState, useEffect, useCallback } from 'react';
import { MapPin, Mail, FileDown, CheckCircle, Clock, Trash2, Send, ChevronRight, Scale, DollarSign } from 'lucide-react';
import { getBuyers, getB2BMatches, getQuotaOffers, updateQuotaStatus, deleteQuotaOffer } from '../api/client';
import { generateB2BContractPDF } from '../utils/pdfGenerator';
import QuotaOfferModal from '../components/b2b/QuotaOfferModal';

const fefoClass = score => score >= 0.75 ? 'high' : score >= 0.55 ? 'mid' : 'low';

const CROP_FILTER_LIST = ['All', 'Tomato', 'Carrot', 'Beans', 'Eggplant', 'Cabbage', 'Green Chilli'];

const STATUS_BADGE = {
  DRAFT:      { label: 'Draft',             cls: 'draft'      },
  OFFER_SENT: { label: 'Offer Sent',        cls: 'sent'       },
  ACCEPTED:   { label: 'Buyer Accepted',    cls: 'accepted'   },
  CONTRACTED: { label: 'Contract Signed',   cls: 'contracted' },
  REJECTED:   { label: 'Declined',          cls: 'rejected'   },
};

const Spinner = () => (
  <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', fontSize: 13 }}>
    ⏳ Loading B2B marketplace intelligence…
  </div>
);

export default function B2BView({ activeCenter = 'DAMBULLA' }) {
  const [tab, setTab]             = useState('directory'); // 'directory' | 'deals'
  const [filter, setFilter]       = useState('All');
  const [buyers, setBuyers]       = useState([]);
  const [matches, setMatches]     = useState(null);
  const [quotas, setQuotas]       = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [negotiatingBuyer, setNegotiatingBuyer] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [buyersData, matchData, quotaData] = await Promise.all([
        getBuyers(activeCenter),
        getB2BMatches(activeCenter),
        getQuotaOffers(activeCenter).catch(() => ({ quotas: [] })),
      ]);
      setBuyers(buyersData.buyers ?? []);
      setMatches(matchData);
      setQuotas(quotaData.quotas ?? []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [activeCenter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleStatusChange = async (quotaId, newStatus) => {
    try {
      await updateQuotaStatus(quotaId, newStatus);
      fetchData();
    } catch (err) {
      alert(`Could not update status: ${err.message}`);
    }
  };

  const handleDeleteQuota = async (quotaId) => {
    if (!confirm('Are you sure you want to delete this quota offer?')) return;
    try {
      await deleteQuotaOffer(quotaId);
      setQuotas(q => q.filter(item => item.id !== quotaId));
    } catch (err) {
      alert(`Could not delete: ${err.message}`);
    }
  };

  // Filter buyers by preferred crop label
  const filteredBuyers = filter === 'All'
    ? buyers
    : buyers.filter(b =>
        b.preferred_crop_labels?.some(l =>
          l.toLowerCase().includes(filter.toLowerCase())
        )
      );

  return (
    <div className="b2b-view">
      {/* Header & Tabs */}
      <div className="analytics-header">
        <div>
          <div className="view-title">🤝 B2B Match &amp; Quota Negotiation Directory</div>
          <div className="view-subtitle">FEFO-ranked buyers, surplus allocation quotas &amp; supply agreement contracts</div>
        </div>

        {/* View Mode Switcher */}
        <div className="b2b-tab-switch">
          <button
            className={`b2b-tab-btn ${tab === 'directory' ? 'active' : ''}`}
            onClick={() => setTab('directory')}
          >
            🏢 Buyer Directory ({buyers.length})
          </button>
          <button
            className={`b2b-tab-btn ${tab === 'deals' ? 'active' : ''}`}
            onClick={() => setTab('deals')}
          >
            📋 Active Quotas &amp; Deals
            {quotas.length > 0 && <span className="b2b-count-pill">{quotas.length}</span>}
          </button>
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
          <div className="stat-card-label">Active Quota Deals</div>
          <div className="stat-card-value amber">{quotas.length}</div>
          <div className="stat-card-sub">Dispatched &amp; In Progress</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Avg FEFO Score</div>
          <div className="stat-card-value accent">
            {matches?.average_fefo_score != null ? matches.average_fefo_score.toFixed(2) : '0.87'}
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

      {/* ───────────────────────────────────────────────────────────────── */}
      {/* TAB 1: BUYER DIRECTORY                                            */}
      {/* ───────────────────────────────────────────────────────────────── */}
      {!loading && !error && tab === 'directory' && (
        <>
          <div className="crop-tabs" style={{ marginBottom: 14 }}>
            {CROP_FILTER_LIST.map(c => (
              <button key={c} className={`crop-tab ${filter === c ? 'active' : ''}`} onClick={() => setFilter(c)}>{c}</button>
            ))}
          </div>

          <div className="b2b-grid">
            {filteredBuyers.length === 0 && (
              <div style={{ color: 'var(--text-muted)', padding: 24, fontSize: 13 }}>
                No buyers found for the selected crop filter.
              </div>
            )}
            {filteredBuyers.map(buyer => (
              <div key={buyer.buyer_code} className="b2b-card">
                <div className="b2b-card-header">
                  <div>
                    <div className="b2b-card-name">{buyer.company_name}</div>
                    <div className="b2b-card-location">
                      <MapPin size={10} style={{ display: 'inline', marginRight: 3 }} />
                      {buyer.location}
                    </div>
                  </div>
                  {/* FEFO score badge */}
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

                {/* Match details if active */}
                {(() => {
                  const match = matches?.matches?.find(m => m.buyer_code === buyer.buyer_code);
                  return match ? (
                    <div style={{ fontSize: 11, color: 'var(--green)', marginTop: 6, fontWeight: 600 }}>
                      ✅ Matched — {match.matched_volume_tons} T of {match.crop_label}
                    </div>
                  ) : null;
                })()}

                <div className="inline-actions" style={{ marginTop: 8 }}>
                  <button
                    className="action-btn primary"
                    onClick={() => setNegotiatingBuyer(buyer)}
                  >
                    🤝 Negotiate Quota
                  </button>
                  <button
                    className="action-btn"
                    onClick={() => setNegotiatingBuyer(buyer)}
                  >
                    📄 Contract
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ───────────────────────────────────────────────────────────────── */}
      {/* TAB 2: ACTIVE QUOTAS & DEALS                                      */}
      {/* ───────────────────────────────────────────────────────────────── */}
      {!loading && !error && tab === 'deals' && (
        <div className="quota-deals-container">
          {quotas.length === 0 ? (
            <div className="quota-empty-state">
              <div className="icon">📋</div>
              <div className="title">No Active Quota Deals Yet</div>
              <div className="sub">
                Click <strong>"🤝 Negotiate Quota"</strong> on any buyer card in the directory to formulate and dispatch an official quota offer.
              </div>
              <button className="action-btn primary" style={{ marginTop: 12 }} onClick={() => setTab('directory')}>
                Browse Buyer Directory
              </button>
            </div>
          ) : (
            <div className="quota-deals-grid">
              {quotas.map(q => {
                const totalVal = (q.allocated_quota_tons || 0) * 1000 * (q.offered_price_per_kg || 0);
                const st = STATUS_BADGE[q.status] || { label: q.status, cls: 'sent' };
                const cropName = q.crop_name ? (q.crop_name.charAt(0).toUpperCase() + q.crop_name.slice(1)) : 'Tomato';

                return (
                  <div key={q.id} className="quota-deal-card">
                    <div className="quota-deal-header">
                      <div>
                        <div className="quota-deal-buyer">{q.buyer_name}</div>
                        <div className="quota-deal-sub">
                          <MapPin size={10} style={{ display: 'inline', marginRight: 3 }} />
                          {q.buyer_location || 'Central Corridor'} · {q.distance_km || 100} km from {q.centre_id}
                        </div>
                      </div>
                      <div className={`quota-status-pill ${st.cls}`}>
                        {st.label}
                      </div>
                    </div>

                    <div className="quota-deal-metrics">
                      <div className="metric">
                        <span className="k">Commodity</span>
                        <span className="v">{cropName}</span>
                      </div>
                      <div className="metric">
                        <span className="k">Quota Volume</span>
                        <span className="v accent">{q.allocated_quota_tons} Tons</span>
                      </div>
                      <div className="metric">
                        <span className="k">Floor Rate</span>
                        <span className="v">Rs. {Number(q.offered_price_per_kg).toFixed(2)}/kg</span>
                      </div>
                      <div className="metric">
                        <span className="k">Agreement Total</span>
                        <span className="v green">LKR {totalVal.toLocaleString('en-LK', { minimumFractionDigits: 2 })}</span>
                      </div>
                    </div>

                    <div className="quota-deal-footer-info">
                      <div>
                        <Clock size={11} style={{ display: 'inline', marginRight: 4, color: 'var(--amber)' }} />
                        Deadline: <strong>{q.delivery_deadline}</strong>
                      </div>
                      <div>
                        FEFO Shelf-Life: <strong>{q.shelf_life_days || 4} Days</strong>
                      </div>
                    </div>

                    {q.notes && (
                      <div className="quota-deal-notes">
                        "{q.notes}"
                      </div>
                    )}

                    {/* Actions bar */}
                    <div className="quota-deal-actions">
                      <button
                        className="deal-pdf-btn"
                        onClick={() => generateB2BContractPDF(q)}
                        title="Download official agreement contract"
                      >
                        <FileDown size={13} /> Agreement PDF
                      </button>

                      <div style={{ display: 'flex', gap: 6 }}>
                        {q.status === 'OFFER_SENT' && (
                          <button
                            className="deal-status-btn accept"
                            onClick={() => handleStatusChange(q.id, 'ACCEPTED')}
                          >
                            ✓ Accept Offer
                          </button>
                        )}
                        {q.status === 'ACCEPTED' && (
                          <button
                            className="deal-status-btn contract"
                            onClick={() => handleStatusChange(q.id, 'CONTRACTED')}
                          >
                            ✍️ Sign Contract
                          </button>
                        )}
                        <button
                          className="deal-delete-btn"
                          onClick={() => handleDeleteQuota(q.id)}
                          title="Delete deal"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Negotiation Modal Popup */}
      {negotiatingBuyer && (
        <QuotaOfferModal
          buyer={negotiatingBuyer}
          activeCenter={activeCenter}
          onClose={() => setNegotiatingBuyer(null)}
          onSaved={() => {
            fetchData();
            setTab('deals');
          }}
        />
      )}
    </div>
  );
}

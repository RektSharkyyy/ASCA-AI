/**
 * ASCA AI — B2B Quota Offer & Supply Agreement Negotiation Modal
 *
 * Allows centre managers and suppliers to formulate and dispatch structured
 * quota allocation offers to verified food processors & buyers.
 */

import { useState } from 'react';
import { X, Send, FileDown, CheckCircle, MapPin, Truck, ShieldCheck, DollarSign, Calendar, Scale } from 'lucide-react';
import { generateB2BContractPDF } from '../../utils/pdfGenerator';
import { createQuotaOffer } from '../../api/client';

const CROPS = ['Tomato', 'Carrot', 'Beans', 'Eggplant', 'Cabbage', 'Green Chilli'];
const GRADES = [
  'Grade A (Processing Quality)',
  'Grade B (Standard Wholesale)',
  'Grade A+ (Premium Export)',
  'Industrial Grade (Puree / Canning)',
];

export default function QuotaOfferModal({ buyer, activeCenter = 'DAMBULLA', onClose, onSaved }) {
  // Pre-calculate default deadline (today + 4 days)
  const defaultDeadline = () => {
    const d = new Date();
    d.setDate(d.getDate() + (buyer?.min_shelf_life_days || 4));
    return d.toISOString().slice(0, 10);
  };

  const [crop, setCrop]                 = useState(buyer?.preferred_crops?.[0] ? (buyer.preferred_crops[0].charAt(0).toUpperCase() + buyer.preferred_crops[0].slice(1)) : 'Tomato');
  const [grade, setGrade]               = useState(GRADES[0]);
  const [totalSurplus, setTotalSurplus] = useState(25.0);
  const [quotaTons, setQuotaTons]       = useState(12.5);
  const [pricePerKg, setPricePerKg]     = useState(85.0);
  const [deadline, setDeadline]         = useState(defaultDeadline);
  const [notes, setNotes]               = useState('Immediate dispatch recommended via Colombo canning corridor. Pre-cooled consignment.');
  const [saving, setSaving]             = useState(false);
  const [error, setError]               = useState(null);
  const [success, setSuccess]           = useState(false);

  const totalValue = quotaTons * 1000 * pricePerKg;
  const distanceKm = buyer?.distance_km || 142;
  const fefoScore  = 0.87;

  const buildPayload = (status = 'OFFER_SENT') => ({
    centre_id: activeCenter,
    buyer_code: buyer?.buyer_code || 'BUYER-001',
    buyer_name: buyer?.company_name || 'Lanka Canning & Sauce Ltd',
    buyer_location: buyer?.location || 'Colombo 15',
    crop_name: crop.toLowerCase(),
    crop_grade: grade,
    total_surplus_tons: Number(totalSurplus),
    allocated_quota_tons: Number(quotaTons),
    offered_price_per_kg: Number(pricePerKg),
    delivery_deadline: deadline,
    shelf_life_days: 4,
    distance_km: Number(distanceKm),
    fefo_score: Number(fefoScore),
    status: status,
    notes: notes,
  });

  const handleSave = async (statusToSet = 'OFFER_SENT') => {
    setSaving(true);
    setError(null);
    try {
      const payload = buildPayload(statusToSet);
      await createQuotaOffer(payload);
      setSuccess(true);
      setTimeout(() => {
        onSaved?.();
        onClose();
      }, 1200);
    } catch (err) {
      setError(err.message || 'Failed to save quota offer.');
    } finally {
      setSaving(false);
    }
  };

  const handleExportPDF = () => {
    const payload = buildPayload('OFFER_SENT');
    generateB2BContractPDF(payload);
  };

  return (
    <div className="bp-modal-backdrop" onClick={onClose}>
      <div className="b2b-quota-modal" onClick={e => e.stopPropagation()}>

        {/* ── Modal Header ── */}
        <div className="b2b-quota-header">
          <div className="b2b-quota-title-block">
            <div className="b2b-quota-icon">🤝</div>
            <div>
              <div className="b2b-quota-title">B2B Quota Allocation &amp; Procurement Agreement</div>
              <div className="b2b-quota-sub">
                <MapPin size={11} style={{ display: 'inline', marginRight: 3 }} />
                {buyer?.company_name} · {buyer?.location} ({distanceKm} km from {activeCenter})
              </div>
            </div>
          </div>
          <button className="bp-close-btn" onClick={onClose}><X size={16} /></button>
        </div>

        {/* ── Modal Body ── */}
        <div className="b2b-quota-body">

          {/* Quick Buyer Intelligence Banner */}
          <div className="quota-buyer-banner">
            <div className="quota-buyer-stat">
              <span className="key">Buyer Type</span>
              <span className="val">{buyer?.buyer_type || 'Processing Plant'}</span>
            </div>
            <div className="quota-buyer-stat">
              <span className="key">Daily Capacity</span>
              <span className="val">{buyer?.daily_capacity_tons || 20} T/day</span>
            </div>
            <div className="quota-buyer-stat">
              <span className="key">FEFO Score</span>
              <span className="val" style={{ color: 'var(--green)' }}>0.87 (High Shelf-Life Fit)</span>
            </div>
            <div className="quota-buyer-stat">
              <span className="key">Corridor Distance</span>
              <span className="val">{distanceKm} km</span>
            </div>
          </div>

          {error && (
            <div className="login-error" style={{ margin: '0 0 10px 0' }}>
              ⚠️ {error}
            </div>
          )}

          {success && (
            <div className="quota-success-banner">
              <CheckCircle size={16} /> Quota offer dispatched successfully and logged to Active Deals!
            </div>
          )}

          <div className="quota-form-grid">

            {/* Crop Selector */}
            <div className="quota-form-group">
              <label className="quota-label">🌾 Target Commodity</label>
              <select className="quota-select" value={crop} onChange={e => setCrop(e.target.value)}>
                {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {/* Quality Grade */}
            <div className="quota-form-group">
              <label className="quota-label">🛡️ Commercial Quality Grade</label>
              <select className="quota-select" value={grade} onChange={e => setGrade(e.target.value)}>
                {GRADES.map(g => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>

            {/* Total Surplus Available */}
            <div className="quota-form-group">
              <label className="quota-label">📦 Total Identified Surplus at Hub (Tons)</label>
              <input
                type="number"
                step="0.5"
                min="1"
                className="quota-input"
                value={totalSurplus}
                onChange={e => setTotalSurplus(e.target.value)}
              />
            </div>

            {/* Allocated Quota */}
            <div className="quota-form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <label className="quota-label">⚖️ Allocated Quota to Buyer (Tons)</label>
                <span className="quota-calc-badge">{((quotaTons / (totalSurplus || 1)) * 100).toFixed(0)}% absorption</span>
              </div>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max={totalSurplus}
                className="quota-input"
                value={quotaTons}
                onChange={e => setQuotaTons(e.target.value)}
              />
              <input
                type="range"
                min="1"
                max={totalSurplus}
                step="0.5"
                value={quotaTons}
                onChange={e => setQuotaTons(Number(e.target.value))}
                className="quota-slider"
              />
            </div>

            {/* Wholesale Floor Price */}
            <div className="quota-form-group">
              <label className="quota-label">💰 Wholesale Floor Price (LKR / kg)</label>
              <div className="quota-input-wrap">
                <span className="quota-prefix">Rs.</span>
                <input
                  type="number"
                  step="1"
                  min="10"
                  className="quota-input with-prefix"
                  value={pricePerKg}
                  onChange={e => setPricePerKg(e.target.value)}
                />
              </div>
            </div>

            {/* Delivery Deadline */}
            <div className="quota-form-group">
              <label className="quota-label">📅 Delivery &amp; Receipt Deadline (FEFO Horizon)</label>
              <input
                type="date"
                className="quota-input"
                value={deadline}
                onChange={e => setDeadline(e.target.value)}
              />
            </div>

          </div>

          {/* Logistics & Special Directives */}
          <div className="quota-form-group" style={{ marginTop: 12 }}>
            <label className="quota-label">🚚 Logistics &amp; Packaging Instructions</label>
            <textarea
              className="quota-textarea"
              rows={2}
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="e.g. Standard plastic crates, pre-cooled at 12°C, direct delivery to plant intake..."
            />
          </div>

          {/* Deal Value Calculation Card */}
          <div className="quota-summary-card">
            <div className="quota-summary-col">
              <div className="label">Quota Weight</div>
              <div className="value accent">{(quotaTons * 1000).toLocaleString()} kg</div>
              <div className="sub">{quotaTons} Metric Tons</div>
            </div>
            <div className="quota-summary-divider" />
            <div className="quota-summary-col">
              <div className="label">Unit Floor Rate</div>
              <div className="value">Rs. {Number(pricePerKg).toFixed(2)}</div>
              <div className="sub">per kg Ex-Hub</div>
            </div>
            <div className="quota-summary-divider" />
            <div className="quota-summary-col">
              <div className="label">Gross Consideration</div>
              <div className="value green">
                LKR {totalValue.toLocaleString('en-LK', { minimumFractionDigits: 2 })}
              </div>
              <div className="sub">Official Agreement Total</div>
            </div>
          </div>

        </div>

        {/* ── Modal Footer Actions ── */}
        <div className="b2b-quota-footer">
          <button className="quota-btn secondary" onClick={handleExportPDF} title="Download Supply Agreement PDF">
            <FileDown size={14} /> Export Agreement PDF
          </button>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              className="quota-btn neutral"
              onClick={() => handleSave('DRAFT')}
              disabled={saving}
            >
              Save Draft
            </button>
            <button
              className="quota-btn primary"
              onClick={() => handleSave('OFFER_SENT')}
              disabled={saving}
            >
              <Send size={14} />
              {saving ? 'Dispatching…' : 'Dispatch Offer & Alert'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

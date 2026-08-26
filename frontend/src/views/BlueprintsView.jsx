import { useState, useEffect } from 'react';
import { FileDown, Eye, Calendar, AlertTriangle, Sparkles, X, Loader2, PlusCircle } from 'lucide-react';
import { BLUEPRINTS as FALLBACK_BLUEPRINTS } from '../data/mockData';
import { generateBlueprintPDF } from '../utils/pdfGenerator';
import { getBlueprints, generateBlueprint } from '../api/client';
import BlueprintModal from '../components/blueprints/BlueprintModal';

const RISK_COLOR = { CRITICAL: 'var(--red)', HIGH: 'var(--red)', MEDIUM: 'var(--amber)', LOW: 'var(--green)' };
const RISK_BG    = { CRITICAL: 'var(--red-dim)', HIGH: 'var(--red-dim)', MEDIUM: 'var(--amber-dim)', LOW: 'var(--green-dim)' };
const STATUS_COLOR = { Final: 'var(--green)', Draft: 'var(--amber)' };

export default function BlueprintsView() {
  const [blueprints,   setBlueprints]   = useState(FALLBACK_BLUEPRINTS);
  const [loading,      setLoading]      = useState(true);
  const [viewingBp,    setViewingBp]    = useState(null);
  const [generatingId, setGeneratingId] = useState(null);

  // New Blueprint Generator Modal State
  const [showGenModal, setShowGenModal] = useState(false);
  const [genCentre,    setGenCentre]    = useState('DAMBULLA');
  const [genCrop,      setGenCrop]      = useState('tomato');
  const [genHorizon,   setGenHorizon]   = useState(14);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchBlueprints();
  }, []);

  const fetchBlueprints = async () => {
    setLoading(true);
    try {
      const res = await getBlueprints();
      if (res?.blueprints?.length) {
        setBlueprints(res.blueprints);
      }
    } catch (err) {
      console.warn('Using fallback blueprints:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewPDF = (bp) => setViewingBp(bp);
  const handleCloseModal = () => setViewingBp(null);

  const handleQuickPDF = (e, bp) => {
    e.stopPropagation();
    setGeneratingId(bp.id);
    setTimeout(() => {
      try {
        generateBlueprintPDF(bp);
      } finally {
        setGeneratingId(null);
      }
    }, 100);
  };

  const handleCreateBlueprint = async () => {
    setIsGenerating(true);
    try {
      const newBp = await generateBlueprint({
        centre: genCentre,
        crop: genCrop,
        horizon_days: Number(genHorizon)
      });
      if (newBp) {
        setBlueprints(prev => [newBp, ...prev]);
        setShowGenModal(false);
        setViewingBp(newBp); // immediately show preview
      }
    } catch (err) {
      console.error('Failed to generate blueprint:', err);
      alert(`Failed to synthesize blueprint: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const criticalCount = blueprints.filter(b => b.riskLevel === 'CRITICAL' || b.riskLevel === 'HIGH').length;
  const finalizedCount = blueprints.filter(b => b.status === 'Final').length;

  return (
    <>
      <div className="blueprints-view">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div className="view-title">📄 Executive Blueprints</div>
            <div className="view-subtitle" style={{ marginTop: 4 }}>Pydantic-validated advisory dossiers · PDF-exportable</div>
          </div>
          <button
            className="action-btn primary"
            onClick={() => setShowGenModal(true)}
            style={{ padding: '8px 16px', fontSize: 13, gap: 6, display: 'flex', alignItems: 'center' }}
          >
            <Sparkles size={14} /> ⚡ Generate Dynamic Blueprint
          </button>
        </div>

        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <div className="stat-card">
            <div className="stat-card-label">Total Blueprints</div>
            <div className="stat-card-value accent">{blueprints.length}</div>
            <div className="stat-card-sub">Database records</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Finalized</div>
            <div className="stat-card-value green">{finalizedCount}</div>
            <div className="stat-card-sub">PDF-ready</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Critical Alerts</div>
            <div className="stat-card-value red">{criticalCount}</div>
            <div className="stat-card-sub">HIGH or CRITICAL</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Crops Analyzed</div>
            <div className="stat-card-value amber">14</div>
            <div className="stat-card-sub">Active catalogue</div>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Loader2 className="spinner" size={24} style={{ display: 'inline', marginRight: 8 }} /> Loading executive blueprints…
          </div>
        ) : (
          blueprints.map(bp => (
            <div key={bp.id} className="blueprint-item">
              <div className="blueprint-icon">📄</div>
              <div className="blueprint-info">
                <div className="blueprint-title">{bp.title}</div>
                <div className="blueprint-meta">
                  <Calendar size={10} style={{ display: 'inline', marginRight: 3 }} />{bp.date}
                  &nbsp;·&nbsp;{bp.center}
                  &nbsp;·&nbsp;{bp.cropCount || 1} crop{(bp.cropCount || 1) > 1 ? 's' : ''}
                  &nbsp;·&nbsp;
                  <span style={{ color: STATUS_COLOR[bp.status] || 'var(--green)', fontWeight: 600 }}>{bp.status || 'Final'}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>{bp.summary}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{
                  padding: '2px 8px',
                  borderRadius: 99,
                  fontSize: 10,
                  fontWeight: 700,
                  background: RISK_BG[bp.riskLevel] || 'var(--amber-dim)',
                  color: RISK_COLOR[bp.riskLevel] || 'var(--amber)',
                  whiteSpace: 'nowrap',
                }}>
                  {bp.riskLevel === 'CRITICAL' && <AlertTriangle size={9} style={{ display: 'inline', marginRight: 3 }} />}
                  {bp.riskLevel}
                </span>
              </div>
              <div className="blueprint-actions">
                <button
                  className="action-btn primary"
                  onClick={() => handleViewPDF(bp)}
                >
                  <Eye size={12} /> View
                </button>
                <button
                  className={`action-btn ${generatingId === bp.id ? 'loading' : ''}`}
                  onClick={(e) => handleQuickPDF(e, bp)}
                  disabled={generatingId === bp.id}
                  title="Download PDF instantly"
                >
                  <FileDown size={12} />
                  {generatingId === bp.id ? '…' : 'PDF'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Dynamic Blueprint Generator Modal */}
      {showGenModal && (
        <div className="bp-modal-backdrop" onClick={() => !isGenerating && setShowGenModal(false)}>
          <div className="bp-modal" style={{ maxWidth: 520 }} onClick={e => e.stopPropagation()}>
            <div className="bp-modal-header">
              <div className="bp-modal-title-block">
                <div className="bp-modal-icon">⚡</div>
                <div>
                  <div className="bp-modal-title">Generate Dynamic Executive Blueprint</div>
                  <div className="bp-modal-sub">Pydantic Guardrail & Time-Series AI Synthesis</div>
                </div>
              </div>
              <button className="bp-close-btn" onClick={() => setShowGenModal(false)} disabled={isGenerating}>
                <X size={16} />
              </button>
            </div>

            <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Target Economic Centre
                </label>
                <select
                  value={genCentre}
                  onChange={e => setGenCentre(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 13 }}
                  disabled={isGenerating}
                >
                  <option value="DAMBULLA">Dambulla Economic Centre</option>
                  <option value="THAMBUTHTHEGAMA">Thambuththegama Economic Centre</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Target Commodity Focus
                </label>
                <select
                  value={genCrop}
                  onChange={e => setGenCrop(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 13 }}
                  disabled={isGenerating}
                >
                  <option value="tomato">Tomato (Solanum lycopersicum)</option>
                  <option value="carrot">Carrot (Daucus carota)</option>
                  <option value="green_chilli">Green Chilli (Capsicum annuum)</option>
                  <option value="eggplant">Eggplant / Brinjal (Solanum melongena)</option>
                  <option value="beans">Beans (Phaseolus vulgaris)</option>
                  <option value="cabbage">Cabbage (Brassica oleracea)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Forecast Horizon
                </label>
                <select
                  value={genHorizon}
                  onChange={e => setGenHorizon(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontSize: 13 }}
                  disabled={isGenerating}
                >
                  <option value={14}>14 Days (Standard Prophet Horizon)</option>
                  <option value={21}>21 Days (Mid-term Outlook)</option>
                  <option value={30}>30 Days (Monthly Macro Cycle)</option>
                </select>
              </div>

              <div style={{ background: 'var(--surface-elevated)', padding: 12, borderRadius: 8, fontSize: 11, color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>
                💡 <strong>AI Pipeline:</strong> Executes Prophet time-series prediction, evaluates risk severity, queries ChromaDB for B2B buyer off-take quotas, and compiles operational directives.
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                <button
                  className="action-btn"
                  onClick={() => setShowGenModal(false)}
                  disabled={isGenerating}
                >
                  Cancel
                </button>
                <button
                  className="action-btn primary"
                  onClick={handleCreateBlueprint}
                  disabled={isGenerating}
                  style={{ minWidth: 160 }}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="spinner" size={14} /> Synthesizing…
                    </>
                  ) : (
                    '🚀 Synthesize Blueprint'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Blueprint Preview & Export Modal */}
      {viewingBp && (
        <BlueprintModal blueprint={viewingBp} onClose={handleCloseModal} />
      )}
    </>
  );
}

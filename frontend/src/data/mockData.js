// ─── Economic Centers ───────────────────────────────────────────
export const CENTERS = [
  { id: 'DAMBULLA', label: 'Dambulla Economic Centre', short: 'DMB' },
  { id: 'THAMBUTHTHEGAMA', label: 'Thambuththegama Economic Centre', short: 'THG' },
];

// ─── Crops ──────────────────────────────────────────────────────
export const CROPS = ['Tomato', 'Carrot', 'Beans', 'Eggplant', 'Cabbage', 'Green Chilli'];

// ─── 14-day price forecast mock data ────────────────────────────
export const generateForecastData = (basePriceMin = 80, basePriceMax = 160) => {
  const today = new Date();
  return Array.from({ length: 21 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - 7 + i);
    const base = basePriceMin + Math.random() * (basePriceMax - basePriceMin);
    const trend = i > 7 ? -0.5 * (i - 7) : 0;
    const actual = i <= 7 ? base + Math.sin(i) * 10 : null;
    const forecast = i >= 7 ? base + trend + Math.sin(i * 0.5) * 8 : null;
    const lower = forecast ? forecast * 0.88 : null;
    const upper = forecast ? forecast * 1.12 : null;
    return {
      date: d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
      actual: actual ? parseFloat(actual.toFixed(1)) : null,
      forecast: forecast ? parseFloat(forecast.toFixed(1)) : null,
      lower: lower ? parseFloat(lower.toFixed(1)) : null,
      upper: upper ? parseFloat(upper.toFixed(1)) : null,
    };
  });
};

export const FORECAST_DATA = {
  Tomato:        generateForecastData(90, 150),
  Carrot:        generateForecastData(70, 120),
  Beans:         generateForecastData(110, 180),
  Eggplant:      generateForecastData(60, 100),
  Cabbage:       generateForecastData(45, 80),
  'Green Chilli':generateForecastData(200, 380),
};

// ─── B2B Buyers mock ────────────────────────────────────────────
export const B2B_BUYERS = [
  {
    id: 1,
    name: 'Lanka Canning & Sauce Ltd',
    location: 'Colombo 15',
    fefoScore: 0.87,
    crop: 'Tomato',
    volume: 26.5,
    capacity: 40,
    distanceKm: 142,
    shelfDaysRemain: 9,
    contactEmail: 'procurement@lankacanning.lk',
    contactPhone: '+94 11 234 5678',
    status: 'Active Negotiation',
    category: 'Food Processing',
  },
  {
    id: 2,
    name: 'Central Province Canning Mills',
    location: 'Matale',
    fefoScore: 0.72,
    crop: 'Carrot',
    volume: 18.0,
    capacity: 25,
    distanceKm: 28,
    shelfDaysRemain: 7,
    contactEmail: 'buy@cpcanning.lk',
    contactPhone: '+94 66 222 3344',
    status: 'Matched',
    category: 'Preservation Factory',
  },
  {
    id: 3,
    name: 'Keells Food Products PLC',
    location: 'Ja-Ela',
    fefoScore: 0.91,
    crop: 'Beans',
    volume: 35.0,
    capacity: 60,
    distanceKm: 175,
    shelfDaysRemain: 12,
    contactEmail: 'supply@keells-food.lk',
    contactPhone: '+94 11 800 9000',
    status: 'Contract Pending',
    category: 'Export Processor',
  },
  {
    id: 4,
    name: 'Raigam Wayamba Agri Centre',
    location: 'Kurunegala',
    fefoScore: 0.55,
    crop: 'Cabbage',
    volume: 12.0,
    capacity: 20,
    distanceKm: 82,
    shelfDaysRemain: 5,
    contactEmail: 'agri@raigam.lk',
    contactPhone: '+94 37 222 5566',
    status: 'Available',
    category: 'Wholesale Aggregator',
  },
  {
    id: 5,
    name: 'Maliban Biscuit Manufactory',
    location: 'Peliyagoda',
    fefoScore: 0.68,
    crop: 'Green Chilli',
    volume: 8.0,
    capacity: 15,
    distanceKm: 160,
    shelfDaysRemain: 6,
    contactEmail: 'ingredients@maliban.lk',
    contactPhone: '+94 11 499 0000',
    status: 'Matched',
    category: 'Ingredient Sourcing',
  },
  {
    id: 6,
    name: 'Delmege Forsyth & Co.',
    location: 'Colombo 10',
    fefoScore: 0.79,
    crop: 'Eggplant',
    volume: 22.0,
    capacity: 35,
    distanceKm: 155,
    shelfDaysRemain: 10,
    contactEmail: 'agro@delmege.lk',
    contactPhone: '+94 11 232 0000',
    status: 'Active Negotiation',
    category: 'Export Processor',
  },
];

// ─── Executive Blueprints mock ───────────────────────────────────
export const BLUEPRINTS = [
  {
    id: 1,
    title: 'Tomato Surplus Advisory – Dambulla Q3',
    date: '2026-08-14',
    center: 'Dambulla',
    cropCount: 1,
    status: 'Final',
    riskLevel: 'HIGH',
    summary: '51 ton surplus detected. 2 B2B buyers matched. Broadcast initiated.',
  },
  {
    id: 2,
    title: 'Weekly Market Pulse Report – Week 32',
    date: '2026-08-08',
    center: 'Thambuththegama',
    cropCount: 6,
    status: 'Final',
    riskLevel: 'MEDIUM',
    summary: 'Price forecast for 6 crops, 14-day LSTM outlook, 4 buyer matches.',
  },
  {
    id: 3,
    title: 'Green Chilli Anomaly Alert – THG',
    date: '2026-08-05',
    center: 'Thambuththegama',
    cropCount: 1,
    status: 'Draft',
    riskLevel: 'CRITICAL',
    summary: 'Critical price anomaly detected. Immediate B2B matching required.',
  },
  {
    id: 4,
    title: 'Monthly Supply Chain Analysis – July',
    date: '2026-08-01',
    center: 'Dambulla',
    cropCount: 6,
    status: 'Final',
    riskLevel: 'LOW',
    summary: 'Stable month. Carrot supply up 18%. No major surplus detected.',
  },
];

// ─── Session history mock ───────────────────────────────────────
export const SESSION_HISTORY = [
  { id: 1, title: 'Tomato price forecast 14-day', date: '10 min ago', center: 'DMB' },
  { id: 2, title: 'B2B buyer match – Beans surplus', date: '2h ago', center: 'THG' },
  { id: 3, title: 'Weekly market pulse analysis', date: 'Yesterday', center: 'DMB' },
  { id: 4, title: 'Green Chilli anomaly alert', date: '3 days ago', center: 'THG' },
];

// ─── Broadcast logs mock ─────────────────────────────────────────
export const BROADCAST_LOGS = [
  { ts: '18:45:42', level: 'SUCCESS', msg: 'SMS sent to Lanka Canning & Sauce Ltd — Tomato 26.5T surplus offer.' },
  { ts: '18:45:41', level: 'SUCCESS', msg: 'WhatsApp alert dispatched to 3 Dambulla buyer contacts.' },
  { ts: '18:40:12', level: 'INFO',    msg: 'Prophet forecast completed for 4 crops concurrently. Semaphore released.' },
  { ts: '18:39:58', level: 'INFO',    msg: 'ChromaDB vector search: 6 B2B buyer candidates retrieved for Tomato.' },
  { ts: '18:37:01', level: 'WARN',    msg: 'Insufficient DB records for Eggplant. Synthetic data fallback used.' },
  { ts: '18:20:00', level: 'INFO',    msg: 'MarketScoutAgent scouting 4 crops concurrently for DAMBULLA.' },
  { ts: '17:55:30', level: 'ERROR',   msg: 'OpenRouter API timeout on attempt 1. Retrying (2/3)…' },
  { ts: '17:55:35', level: 'SUCCESS', msg: 'OpenRouter API retry successful. Guardrail validated response.' },
];

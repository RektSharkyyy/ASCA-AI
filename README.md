# 🌾 ASCA AI — Autonomous Agricultural Supply Chain Advisory System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB.svg?logo=react&logoColor=black)](https://vitejs.dev)
[![Prophet](https://img.shields.io/badge/Time%20Series-Prophet%20Forecasting-3776AB.svg?logo=python&logoColor=white)](https://facebook.github.io/prophet/)
[![ChromaDB](https://img.shields.io/badge/Vector%20Store-ChromaDB-FF6600.svg)](https://www.trychroma.com/)
[![Tests](https://img.shields.io/badge/Pytest-30%2F30%20Passed-brightgreen.svg?logo=pytest&logoColor=white)](https://docs.pytest.org)

**ASCA AI** is an enterprise-grade, multi-agent AI advisory platform built to stabilize agricultural perishable supply chains in Sri Lanka. It serves farmers, agricultural aggregators, commercial processing plants, and economic center directors across major hubs including **Dambulla** and **Thambuththegama**.

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────┐
                                  │      React (Vite)      │
                                  │   Tailored Dark UI     │
                                  └───────────┬────────────┘
                                              │ REST / JWT
                                              ▼
                                  ┌────────────────────────┐
                                  │   FastAPI Gateway      │
                                  └───────────┬────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
         ┌─────────────────────────┐                     ┌─────────────────────────┐
         │  Domain Intent Guardrail│                     │   Upstream Query Router │
         │  (Fail-Open / Security) │                     │ (Direct / Web / RAG)    │
         └────────────┬────────────┘                     └────────────┬────────────┘
                      │                                               │
    ┌─────────────────┼─────────────────────────┬─────────────────────┘
    ▼                 ▼                         ▼
┌───────────────┐ ┌───────────────────────┐ ┌────────────────────────┐
│ Market Scout  │ │ Demand-Supply Matcher │ │ Agricultural RAG Agent │
│ Parallel Scan │ │ FEFO Shelf-Life Risk  │ │ Scaled Fertilizer Math │
└───────┬───────┘ └───────────┬───────────┘ └───────────┬────────────┘
        │                     │                         │
        ▼                     ▼                         ▼
┌───────────────┐ ┌───────────────────────┐ ┌────────────────────────┐
│ Prophet Time- │ │ ChromaDB Buyer Store  │ │ DOA Agronomy Knowledge │
│ Series Engine │ │ Cosine Vector Index   │ │ & Sri Lankan Benchmarks│
└───────────────┘ └───────────────────────┘ └────────────────────────┘
```

---

## ✨ Core Features

1. **Agronomic Advisory & Scaled Fertilizer Calculator**:
   - Natural language land area parser (`acres`, `hectares`, `perches`, fractions).
   - Ministry of Agriculture (DOA) benchmark scaling with Basal, Top Dressing 1, and Top Dressing 2 phases.
   - Commercial 50kg bag procurement planning (Urea, TSP, MOP).
   - Client-side on-demand PDF advisory export.

2. **Prophet Time-Series Price Forecasting**:
   - 14-day price prediction with daily/weekly seasonalities.
   - Automated surplus anomaly detection (>25% price drop alert trigger).

3. **FEFO Demand-Supply Matcher (B2B Negotiator)**:
   - First-Expired, First-Out (FEFO) decay scoring combining perishability, transit distance, and buyer capacity.
   - ChromaDB semantic search over industrial processing plants and supermarket buyers.

4. **Live Dynamic Executive Blueprints**:
   - Real-time synthesis of Pydantic-validated executive dossiers for economic center directors.
   - Actionable directives, buyer off-take quotas, and vector-aligned PDF export.

5. **Cultivation & Agronomy Planner**:
   - Multi-factor crop ranking based on soil type, water source, season (Maha/Yala), and land acreage.
   - Estimated yield, revenue, net profit, and ROI calculations.

6. **Enterprise Security & Role-Based Access**:
   - Bcrypt password hashing and salt verification.
   - HS256 JWT access and refresh token authentication.
   - Strict session isolation and chat history management.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (OpenRouter/OpenAI/Google and Tavily)

# Launch Backend API Server
python run.py
```
*API will run at:* `http://localhost:8000` (Interactive Swagger docs: `http://localhost:8000/docs`)

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Frontend UI will run at:* `http://localhost:5173`

---

## 🧪 Automated Testing Suite

ASCA AI includes a comprehensive `pytest` test suite with **100% pass rate across 30 unit and integration tests**:

```bash
cd backend
./.venv/bin/python -m pytest tests -v
```

### Test Coverage Summary
* `tests/test_auth.py`: Bcrypt password hashing, JWT token creation/decoding, login API verification.
* `tests/test_intent_guardrail.py`: Binary intent classifier, domain boundaries, prompt injection defense.
* `tests/test_router.py`: Deterministic and lightweight LLM routing (`direct`, `web_search`, `rag`).
* `tests/test_market_forecasting.py`: Prophet forecasting models, anomaly detection, price trends.
* `tests/test_matcher_fefo.py`: FEFO perishability decay scores, capacity allocation, ChromaDB schemas.
* `tests/test_cultivation_calculator.py`: Land unit extraction regex, multi-acre fertilizer scaling math.
* `tests/test_api_routes.py`: End-to-end HTTP integration tests for all protected and public endpoints.

---

## 📂 Project Structure

```
├── backend/
│   ├── config/              # YAML domain parameters and model configs
│   ├── data/                # Local SQLite and ChromaDB vector store
│   ├── src/
│   │   ├── agents/          # Multi-agent implementations (RAG, Scout, Matcher, Guardrail)
│   │   ├── api/             # FastAPI routers (chat, market, b2b, cultivation, blueprints, auth)
│   │   ├── auth/            # JWT dependencies and bcrypt security
│   │   ├── infrastructure/  # Database models, LLM loaders, logging, config
│   │   └── services/        # Business logic facades & crop catalog
│   ├── tests/               # Pytest automated test suite (30 tests)
│   ├── .env.example         # Environment template
│   ├── requirements.txt     # Python dependencies
│   └── run.py               # Server entry point
├── frontend/
│   ├── src/
│   │   ├── api/             # HTTP client & auth interceptor
│   │   ├── components/      # Modular UI components (Chat, Charts, Modals, Layout)
│   │   ├── views/           # Views (Chat, Market, B2B, Blueprints, Cultivation, Login)
│   │   └── utils/           # Client-side PDF generator (jsPDF & AutoTable)
│   ├── package.json         # Frontend dependencies
│   └── vite.config.js       # Vite proxy & build configuration
└── .gitignore               # Clean repository exclusion rules
```

---

## 📜 License & Acknowledgements
Developed as part of the CSE6035 Development Project for Cardiff Metropolitan University.
Agricultural benchmarks and fertilizer formulations grounded in Department of Agriculture (DOA) Sri Lanka publications.

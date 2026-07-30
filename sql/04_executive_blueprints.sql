-- Executive Blueprints Table Schema

CREATE TABLE IF NOT EXISTS executive_blueprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    forecast_horizon_days INTEGER DEFAULT 14,
    summary_text TEXT NOT NULL,
    pydantic_validated BOOLEAN DEFAULT TRUE,
    confidence_score REAL DEFAULT 1.0,
    telegram_broadcast_status VARCHAR(50) DEFAULT 'PENDING'
);

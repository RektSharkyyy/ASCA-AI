-- Surplus Matches Table Schema

CREATE TABLE IF NOT EXISTS surplus_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    center_id VARCHAR(50) NOT NULL,
    crop_name VARCHAR(100) NOT NULL,
    surplus_volume_tons REAL NOT NULL,
    buyer_code VARCHAR(50) REFERENCES b2b_buyers(buyer_code),
    fefo_risk_score REAL NOT NULL,
    negotiation_status VARCHAR(50) DEFAULT 'PENDING'
);

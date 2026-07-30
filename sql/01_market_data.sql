-- Market Data Table Schema

CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    center_id VARCHAR(50) NOT NULL,
    crop_name VARCHAR(100) NOT NULL,
    wholesale_price_lkr REAL NOT NULL,
    supply_volume_tons REAL NOT NULL,
    predicted_price_lkr REAL,
    is_surplus_anomaly BOOLEAN DEFAULT FALSE
);

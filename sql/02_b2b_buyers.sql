-- B2B Buyers Table Schema

CREATE TABLE IF NOT EXISTS b2b_buyers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(150) NOT NULL,
    buyer_type VARCHAR(100),
    preferred_crops TEXT NOT NULL,
    daily_capacity_tons REAL NOT NULL,
    location VARCHAR(150) NOT NULL,
    max_distance_km REAL DEFAULT 150.0,
    min_shelf_life_days INTEGER DEFAULT 2,
    contact_phone VARCHAR(50),
    telegram_chat_id VARCHAR(50)
);

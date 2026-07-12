-- Migration: rename stocks to assets and add type column
BEGIN TRANSACTION;

-- 1. Rename existing table
ALTER TABLE stocks RENAME TO assets_old;

-- 2. Create new assets table with type column
CREATE TABLE assets (
    id INTEGER PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    exchange TEXT,
    sector TEXT,
    type TEXT NOT NULL DEFAULT 'equity'
);

-- 3. Copy data, set type='equity'
INSERT INTO assets (id, symbol, name, exchange, sector, type)
SELECT id, symbol, name, exchange, sector, 'equity' FROM assets_old;

-- 4. Drop old table
DROP TABLE assets_old;

-- 5. Recreate foreign keys
ALTER TABLE daily_prices RENAME TO daily_prices_old;
CREATE TABLE daily_prices (
    id INTEGER PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    adj_close REAL,
    volume REAL,
    FOREIGN KEY(asset_id) REFERENCES assets(id)
);
INSERT INTO daily_prices (id, asset_id, date, open, high, low, close, adj_close, volume)
SELECT id, stock_id, date, open, high, low, close, adj_close, volume FROM daily_prices_old;
DROP TABLE daily_prices_old;

ALTER TABLE suggestions RENAME TO suggestions_old;
CREATE TABLE suggestions (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    asset_id INTEGER NOT NULL,
    score REAL NOT NULL,
    reasoning TEXT,
    FOREIGN KEY(asset_id) REFERENCES assets(id)
);
INSERT INTO suggestions (id, date, asset_id, score, reasoning)
SELECT id, date, stock_id, score, reasoning FROM suggestions_old;
DROP TABLE suggestions_old;

COMMIT;
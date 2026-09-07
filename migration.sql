-- Migration: add range_key column to market_index_prices table
BEGIN TRANSACTION;

-- Check if column already exists before adding
ALTER TABLE market_index_prices ADD COLUMN range_key TEXT;

COMMIT;
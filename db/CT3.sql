-- CT3: Create Table orderbook_data
-- Run against the 'alpha_volume_db1' database:
--   psql -U postgres -d alpha_volume_db1 -f CT3.sql

-- bid_levels and ask_levels are JSONB arrays of 50 elements,
-- each element: {"price": numeric(18,8), "size": numeric(18,8)}
-- JSONB is stored compressed via TOAST by default.

CREATE TABLE IF NOT EXISTS orderbook_data (
    id         BIGINT      NOT NULL,
    ts         TIMESTAMPTZ NOT NULL,
    symbol_id  BIGINT,
    bid_levels JSONB,
    ask_levels JSONB,
    PRIMARY KEY (id, ts)
);

SELECT create_hypertable('orderbook_data', 'ts', if_not_exists => TRUE);

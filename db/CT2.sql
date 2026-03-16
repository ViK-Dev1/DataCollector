-- CT2: Create Table price_data
-- Run against the 'alpha_volume_db1' database:
--   psql -U postgres -d alpha_volume_db1 -f CT2.sql

-- Note: TimescaleDB requires the partition column (ts) to be part of
-- any unique/primary key constraint, so the PK is composite (id, ts).

CREATE TABLE IF NOT EXISTS price_data (
    id        BIGINT           NOT NULL,
    ts        TIMESTAMPTZ      NOT NULL,
    symbol_id BIGINT,
    o         NUMERIC(18, 8),  -- OPEN
    h         NUMERIC(18, 8),  -- HIGH
    l         NUMERIC(18, 8),  -- LOW
    c         NUMERIC(18, 8),  -- CLOSE
    vol       NUMERIC(18, 8),
    PRIMARY KEY (id, ts)
);

SELECT create_hypertable('price_data', 'ts', if_not_exists => TRUE);

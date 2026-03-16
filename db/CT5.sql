-- CT5: Create Table liquidations
-- Run against the 'alpha_volume_db1' database:
--   psql -U postgres -d alpha_volume_db1 -f CT5.sql

CREATE TABLE IF NOT EXISTS liquidations (
    id        BIGINT        NOT NULL,
    ts        TIMESTAMPTZ   NOT NULL,
    symbol_id BIGINT,
    side      VARCHAR(10),
    size1      NUMERIC(18, 8),
    price     NUMERIC(18, 8),
    PRIMARY KEY (id, ts)
);

SELECT create_hypertable('liquidations', 'ts', if_not_exists => TRUE);

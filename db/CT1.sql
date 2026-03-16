-- CT1: Create Table crypto_pairs
-- Run against the 'alpha_volume_db1' database:
--   psql -U postgres -d alpha_volume_db1 -f CT1.sql

CREATE TABLE IF NOT EXISTS crypto_pairs (
    id            BIGINT        PRIMARY KEY,
    symbol        VARCHAR(10),
    exchange      VARCHAR(10),
    base          VARCHAR(10),
    quote         VARCHAR(10),
    addet_at      TIMESTAMP,
    monitoring_on BOOLEAN
);

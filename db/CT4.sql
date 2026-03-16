-- CT4: Create Table orders
-- Run against the 'alpha_volume_db1' database:
--   psql -U postgres -d alpha_volume_db1 -f CT4.sql

CREATE TABLE IF NOT EXISTS orders (
    id             BIGINT        NOT NULL,
    ts             TIMESTAMPTZ   NOT NULL,
    symbol_id      BIGINT,
    trade_id       VARCHAR(50),
    side           VARCHAR(10),
    size1          NUMERIC(18, 8), -- renamed into size1 because size is reserved
    price          NUMERIC(18, 8),
    tick_direction VARCHAR(20),
    PRIMARY KEY (id, ts)
);

SELECT create_hypertable('orders', 'ts', if_not_exists => TRUE);

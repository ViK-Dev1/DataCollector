-- CDB1: Create Database
-- Run as superuser against the default 'postgres' database:
--   psql -U postgres -f CDB1.sql

-- Create DB
CREATE DATABASE alpha_volume_db1;

-- Switch to DB
\c alpha_volume_db1

-- Install timescaledb extention on top of my postgresql 
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

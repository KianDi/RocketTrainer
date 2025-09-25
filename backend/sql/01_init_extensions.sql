-- Initialize PostgreSQL extensions (TimescaleDB only for time-series tables)
-- This file runs automatically when the PostgreSQL container starts

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for password hashing and cryptographic functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Enable TimescaleDB extension (will only be used for specific time-series tables)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL extensions initialized successfully (TimescaleDB available for time-series data)';
END $$;

-- Create TimescaleDB hypertables ONLY for time-series data
-- Regular tables (matches, users) will use standard PostgreSQL
-- This file runs after extensions are loaded

-- Wait for tables to be created by Alembic migrations
-- This script will be run after the main application tables exist

-- Function to create hypertables safely (ONLY for time-series tables)
CREATE OR REPLACE FUNCTION create_hypertables() RETURNS void AS $$
BEGIN
    RAISE NOTICE 'Creating TimescaleDB hypertables for time-series data only';
    RAISE NOTICE 'Regular tables (matches, users) will use standard PostgreSQL';

    -- Check if player_stats table exists before converting to hypertable
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'player_stats') THEN
        -- First, drop the primary key constraint that conflicts with partitioning
        IF EXISTS (SELECT 1 FROM information_schema.table_constraints
                  WHERE table_name = 'player_stats' AND constraint_type = 'PRIMARY KEY') THEN
            ALTER TABLE player_stats DROP CONSTRAINT player_stats_pkey;
            RAISE NOTICE 'Dropped primary key constraint from player_stats';
        END IF;

        -- Convert player_stats to hypertable partitioned by time column
        -- Only create if not already a hypertable
        IF NOT EXISTS (SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = 'player_stats') THEN
            PERFORM create_hypertable('player_stats', 'time', if_not_exists => TRUE);
            RAISE NOTICE 'Created hypertable for player_stats partitioned by time';
        ELSE
            RAISE NOTICE 'player_stats hypertable already exists partitioned by time';
        END IF;
    ELSE
        RAISE NOTICE 'player_stats table does not exist yet - will be created by migrations';
    END IF;

    -- Create additional hypertables for other time-series tables if they exist
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'training_sessions') THEN
        IF NOT EXISTS (SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = 'training_sessions') THEN
            PERFORM create_hypertable('training_sessions', 'time', if_not_exists => TRUE);
            RAISE NOTICE 'Created hypertable for training_sessions partitioned by time';
        END IF;
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error creating hypertables: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Call the function to create hypertables
SELECT create_hypertables();

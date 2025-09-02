-- Migration: 001_initial_schema
-- Description: Create initial database schema for Neighborhood Insights IL
-- Created: 2024-09-02
-- Dependencies: PostGIS extension

-- Migration metadata
INSERT INTO schema_migrations (version, name, applied_at) 
VALUES ('001', 'initial_schema', NOW())
ON CONFLICT (version) DO NOTHING;

-- Load the complete schema
\i '../schema.sql'
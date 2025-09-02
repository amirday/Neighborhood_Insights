-- Initialize migration system before schema creation
-- This file runs automatically when PostgreSQL container starts

\echo 'Initializing Neighborhood Insights IL Database...'

-- Load migration system first
\i db/migrate.sql

\echo 'Migration system initialized'
\echo 'Loading initial schema...'

-- Apply initial schema
\i db/schema.sql

\echo 'Database initialization complete!'
\echo 'Run "SELECT * FROM migration_status;" to view applied migrations'
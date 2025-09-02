-- Database Migration System
-- Tracks applied migrations and provides rollback capability

-- Create migrations tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    applied_at TIMESTAMP DEFAULT NOW(),
    checksum TEXT, -- Optional: for integrity verification
    rollback_sql TEXT -- Optional: for rollback capability
);

-- Migration management functions
CREATE OR REPLACE FUNCTION get_current_schema_version()
RETURNS VARCHAR AS $$
BEGIN
    RETURN (SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1);
END;
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION list_pending_migrations(target_version VARCHAR DEFAULT NULL)
RETURNS TABLE(migration_file VARCHAR) AS $$
DECLARE
    current_ver VARCHAR;
    target_ver VARCHAR;
BEGIN
    current_ver := COALESCE(get_current_schema_version(), '000');
    target_ver := COALESCE(target_version, '999');
    
    -- Return migration files that should be applied
    -- This is a simplified version - in practice, you'd scan the migrations directory
    IF current_ver < '001' AND target_ver >= '001' THEN
        RETURN QUERY SELECT '001_initial_schema.sql'::VARCHAR;
    END IF;
    
    RETURN;
END;
$$ LANGUAGE 'plpgsql';

-- Migration status view
CREATE OR REPLACE VIEW migration_status AS
SELECT 
    version,
    name,
    applied_at,
    CASE 
        WHEN version = get_current_schema_version() THEN 'CURRENT'
        ELSE 'APPLIED'
    END as status
FROM schema_migrations
ORDER BY version;

-- Initial setup notification
DO $$
BEGIN
    RAISE NOTICE 'Migration system initialized';
    RAISE NOTICE 'Current schema version: %', COALESCE(get_current_schema_version(), 'NONE');
END;
$$;
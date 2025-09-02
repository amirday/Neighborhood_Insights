# Database Migrations

This directory contains database migration files for the Neighborhood Insights IL project.

## Migration System

Migrations are tracked using the `schema_migrations` table and managed through SQL scripts.

## Running Migrations

### Apply Initial Schema
```bash
# Apply migration system and initial schema
make migrate

# Or manually:
docker exec ni-postgres psql -U ni -d ni -f /path/to/migrate.sql
docker exec ni-postgres psql -U ni -d ni -f /path/to/schema.sql
```

### Check Migration Status
```sql
-- View current schema version
SELECT get_current_schema_version();

-- View all applied migrations
SELECT * FROM migration_status;

-- List pending migrations
SELECT * FROM list_pending_migrations();
```

## Migration Files

### 001_initial_schema.sql
- Creates complete initial database schema
- Includes all tables, indices, constraints, and functions
- Sets up PostGIS extensions and Israeli-specific data types

## Creating New Migrations

When adding new migrations:

1. Create new file: `002_migration_name.sql`
2. Include migration metadata:
```sql
INSERT INTO schema_migrations (version, name, applied_at) 
VALUES ('002', 'migration_name', NOW());
```
3. Add your schema changes
4. Update the `list_pending_migrations()` function if needed
5. Test migration on development database

## Migration Best Practices

- Always backup before running migrations
- Test migrations on development environment first
- Include rollback instructions in comments
- Keep migrations small and focused
- Use descriptive names for migration files

## File Naming Convention

Format: `{version}_{description}.sql`
- Version: 3-digit zero-padded number (001, 002, 003...)
- Description: snake_case description of changes
- Examples:
  - `001_initial_schema.sql`
  - `002_add_user_preferences.sql`  
  - `003_update_scoring_weights.sql`
-- Migration: Add project_id to lexique table
-- Date: 2026-01-26
-- Description: Adds project isolation to lexique entries

-- 1. Add project_id column (nullable initially for existing data)
ALTER TABLE lexique ADD COLUMN IF NOT EXISTS project_id UUID;

-- 2. Add foreign key constraint
ALTER TABLE lexique
    DROP CONSTRAINT IF EXISTS lexique_project_id_fkey,
    ADD CONSTRAINT lexique_project_id_fkey
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- 3. Drop old unique constraint on code
ALTER TABLE lexique DROP CONSTRAINT IF EXISTS lexique_code_key;

-- 4. Add new composite unique constraint on (code, project_id)
ALTER TABLE lexique DROP CONSTRAINT IF EXISTS lexique_code_project_unique;
ALTER TABLE lexique ADD CONSTRAINT lexique_code_project_unique UNIQUE (code, project_id);

-- 5. Create index for project_id queries
CREATE INDEX IF NOT EXISTS idx_lexique_project ON lexique (project_id);

-- 6. Update index for parent queries to include project_id
DROP INDEX IF EXISTS idx_lexique_parent;
CREATE INDEX idx_lexique_parent ON lexique (parent_code, project_id);

-- Note: After running this migration, you will need to:
-- 1. Assign existing lexique entries to their respective projects manually
-- 2. Or delete existing lexique entries and recreate them per project
--
-- Example to assign all existing lexique entries to a specific project:
-- UPDATE lexique SET project_id = 'your-project-uuid' WHERE project_id IS NULL;

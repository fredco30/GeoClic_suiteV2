-- =============================================================================
-- Migration 022: Appliquer project_id sur type_field_configs + peupler existants
-- Date: 2026-02-06
-- Description: La migration 003 n'avait jamais ete appliquee sur le serveur.
--              Cette migration ajoute la colonne project_id (idempotent) et
--              peuple les champs existants en les reliant a leur projet via
--              le lexique (type_name = code lexique -> project_id du lexique).
-- =============================================================================

-- 1. Ajouter la colonne project_id si elle n'existe pas
ALTER TABLE type_field_configs
ADD COLUMN IF NOT EXISTS project_id UUID;

-- 2. Ajouter la FK si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'type_field_configs_project_fkey'
        AND table_name = 'type_field_configs'
    ) THEN
        ALTER TABLE type_field_configs
        ADD CONSTRAINT type_field_configs_project_fkey
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;
END $$;

-- 3. Creer les index si absents
CREATE INDEX IF NOT EXISTS idx_type_field_configs_project
ON type_field_configs(project_id);

CREATE INDEX IF NOT EXISTS idx_type_field_configs_type_project
ON type_field_configs(type_name, project_id);

-- 4. Peupler project_id pour les champs existants qui n'en ont pas
-- On fait le lien via type_name (= code du lexique) pour recuperer le project_id
UPDATE type_field_configs tfc
SET project_id = l.project_id
FROM lexique l
WHERE tfc.type_name = l.code
  AND tfc.project_id IS NULL
  AND l.project_id IS NOT NULL;

-- 5. Verification
DO $$
DECLARE
    total_count INTEGER;
    with_project INTEGER;
    without_project INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM type_field_configs;
    SELECT COUNT(*) INTO with_project FROM type_field_configs WHERE project_id IS NOT NULL;
    SELECT COUNT(*) INTO without_project FROM type_field_configs WHERE project_id IS NULL;

    RAISE NOTICE 'Migration 022 terminee:';
    RAISE NOTICE '  Total champs: %', total_count;
    RAISE NOTICE '  Avec project_id: %', with_project;
    RAISE NOTICE '  Sans project_id: %', without_project;
END $$;

-- =============================================================================
-- NOTES:
-- - Idempotent: peut etre rejouee sans risque (IF NOT EXISTS partout)
-- - Les champs sans correspondance lexique garderont project_id = NULL
-- - champs.py et sync.py utilisent deja project_id dans leurs requetes
-- =============================================================================

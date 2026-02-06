-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 003: Ajout de project_id à type_field_configs
-- Date: 2026-01-26
-- Description: Isole les champs dynamiques par projet (comme le lexique)
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1. Ajouter la colonne project_id
ALTER TABLE type_field_configs
ADD COLUMN IF NOT EXISTS project_id UUID;

-- 2. Supprimer l'ancienne contrainte unique
ALTER TABLE type_field_configs
DROP CONSTRAINT IF EXISTS type_field_configs_type_name_field_name_key;

-- 3. Créer la nouvelle contrainte unique avec project_id
-- Permet d'avoir le même champ dans différents projets
ALTER TABLE type_field_configs
ADD CONSTRAINT type_field_configs_unique_per_project
UNIQUE(type_name, field_name, project_id);

-- 4. Ajouter la clé étrangère vers projects
ALTER TABLE type_field_configs
ADD CONSTRAINT type_field_configs_project_fkey
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- 5. Créer un index pour les requêtes par projet
CREATE INDEX IF NOT EXISTS idx_type_field_configs_project
ON type_field_configs(project_id);

-- 6. Créer un index composite pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_type_field_configs_type_project
ON type_field_configs(type_name, project_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- NOTES:
-- - Les champs existants sans project_id restent globaux (compatibilité)
-- - Les nouveaux champs créés via templates auront un project_id
-- - La synchronisation filtrera par project_id
-- ═══════════════════════════════════════════════════════════════════════════════

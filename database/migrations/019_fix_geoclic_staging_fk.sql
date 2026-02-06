-- Migration 019: Corrige les FK de geoclic_staging pour utiliser geoclic_users
-- Les colonnes created_by, updated_by, validated_by pointaient vers l'ancienne table "users"
-- Elles doivent maintenant pointer vers "geoclic_users" (auth unifiée)

BEGIN;

-- 1. Supprimer les anciennes FK
ALTER TABLE geoclic_staging DROP CONSTRAINT IF EXISTS geoclic_staging_created_by_fkey;
ALTER TABLE geoclic_staging DROP CONSTRAINT IF EXISTS geoclic_staging_updated_by_fkey;
ALTER TABLE geoclic_staging DROP CONSTRAINT IF EXISTS geoclic_staging_validated_by_fkey;

-- 2. Nettoyer les références orphelines (utilisateurs qui n'existent pas dans geoclic_users)
UPDATE geoclic_staging SET created_by = NULL
WHERE created_by IS NOT NULL
  AND created_by NOT IN (SELECT id FROM geoclic_users);

UPDATE geoclic_staging SET updated_by = NULL
WHERE updated_by IS NOT NULL
  AND updated_by NOT IN (SELECT id FROM geoclic_users);

UPDATE geoclic_staging SET validated_by = NULL
WHERE validated_by IS NOT NULL
  AND validated_by NOT IN (SELECT id FROM geoclic_users);

-- 3. Recréer les FK vers geoclic_users
ALTER TABLE geoclic_staging
    ADD CONSTRAINT geoclic_staging_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES geoclic_users(id) ON DELETE SET NULL;

ALTER TABLE geoclic_staging
    ADD CONSTRAINT geoclic_staging_updated_by_fkey
    FOREIGN KEY (updated_by) REFERENCES geoclic_users(id) ON DELETE SET NULL;

ALTER TABLE geoclic_staging
    ADD CONSTRAINT geoclic_staging_validated_by_fkey
    FOREIGN KEY (validated_by) REFERENCES geoclic_users(id) ON DELETE SET NULL;

COMMIT;

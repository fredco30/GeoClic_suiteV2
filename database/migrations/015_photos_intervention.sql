-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 015: Photos d'intervention pour agents terrain
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- Ajouter la colonne photos_intervention pour les photos prises par les agents terrain
ALTER TABLE demandes_citoyens
ADD COLUMN IF NOT EXISTS photos_intervention JSONB DEFAULT '[]';

COMMENT ON COLUMN demandes_citoyens.photos_intervention IS
'Photos prises par les agents terrain lors de l''intervention (format JSON array de URLs)';

COMMIT;

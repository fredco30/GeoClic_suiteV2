-- Migration 021: Création de la table sync_history pour la synchronisation mobile
-- Cette table manquait et causait une erreur 500 sur POST /api/sync
-- Note: Si la table existe déjà avec FK vers 'users', on corrige vers 'geoclic_users'

CREATE TABLE IF NOT EXISTS sync_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    device_id VARCHAR(255),
    sync_type VARCHAR(50) DEFAULT 'full',
    points_uploaded INTEGER DEFAULT 0,
    points_downloaded INTEGER DEFAULT 0,
    points_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Supprimer l'ancienne FK (vers users) si elle existe
ALTER TABLE sync_history DROP CONSTRAINT IF EXISTS sync_history_user_id_fkey;

-- Recréer la FK vers geoclic_users
ALTER TABLE sync_history ADD CONSTRAINT sync_history_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES geoclic_users(id);

CREATE INDEX IF NOT EXISTS idx_sync_history_user_id ON sync_history(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_history_completed_at ON sync_history(completed_at DESC);

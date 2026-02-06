-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration: Ajout de la table system_settings
-- Description: Stocke les paramètres système comme la connexion PostGIS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Table pour les paramètres système
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,  -- Stocké en JSON
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id)
);

-- Index pour recherche rapide par clé
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings (config_key);

-- Commentaire
COMMENT ON TABLE system_settings IS 'Paramètres système (connexion PostGIS, etc.)';

-- Exemple d'insertion (optionnel)
-- INSERT INTO system_settings (config_key, description) VALUES
-- ('postgis_connection', 'Configuration de connexion à la base PostGIS externe');

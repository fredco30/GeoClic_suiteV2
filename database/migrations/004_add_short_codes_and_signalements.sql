-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 004: Short Codes (QR) et Signalements (Portail Citoyen)
-- ═══════════════════════════════════════════════════════════════════════════════
-- Date: 2026-01-28
-- Description: Ajoute les tables pour les QR codes et le portail citoyen
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLE SHORT_CODES (QR Codes)
-- ═══════════════════════════════════════════════════════════════════════════════
-- Stocke les codes courts pour les QR codes (format GC-XXXXXX)

CREATE TABLE IF NOT EXISTS short_codes (
    id SERIAL PRIMARY KEY,
    short_code VARCHAR(10) UNIQUE NOT NULL,  -- Format: GC-XXXXXX
    point_id UUID REFERENCES geoclic_staging(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    scans_count INTEGER DEFAULT 0,
    last_scanned_at TIMESTAMPTZ
);

-- Index pour recherche rapide par code
CREATE INDEX IF NOT EXISTS idx_short_codes_code ON short_codes (short_code);
CREATE INDEX IF NOT EXISTS idx_short_codes_point ON short_codes (point_id);

-- Commentaire
COMMENT ON TABLE short_codes IS 'Codes courts pour QR codes (format GC-XXXXXX)';


-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLE SIGNALEMENTS (Portail Citoyen)
-- ═══════════════════════════════════════════════════════════════════════════════
-- Stocke les signalements des citoyens via le portail public

CREATE TYPE signalement_urgence AS ENUM ('faible', 'normal', 'urgent', 'critique');
CREATE TYPE signalement_statut AS ENUM ('nouveau', 'pris_en_compte', 'en_cours', 'traite', 'rejete', 'archive');

CREATE TABLE IF NOT EXISTS signalements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Lien avec un point existant (optionnel)
    point_id UUID REFERENCES geoclic_staging(id) ON DELETE SET NULL,

    -- Informations du signalement
    type_probleme VARCHAR(100) NOT NULL,  -- 'Dégradation', 'Panne', 'Danger', 'Autre'
    description TEXT,
    urgence signalement_urgence DEFAULT 'normal',

    -- Contact du signalant (requis)
    email VARCHAR(255),
    telephone VARCHAR(20),
    nom_signalant VARCHAR(255),

    -- Localisation (si nouveau lieu, pas de point_id)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    adresse TEXT,
    geom GEOMETRY(Point, 4326),

    -- Photos (JSONB array)
    photos JSONB DEFAULT '[]',

    -- Workflow de traitement
    statut signalement_statut DEFAULT 'nouveau',
    traite_par UUID REFERENCES users(id),
    traite_le TIMESTAMPTZ,
    commentaire_interne TEXT,
    commentaire_public TEXT,  -- Réponse visible par le citoyen

    -- Métadonnées
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    source VARCHAR(50) DEFAULT 'portail_citoyen'  -- 'portail_citoyen', 'qr_code', 'neocity'
);

-- Index
CREATE INDEX IF NOT EXISTS idx_signalements_point ON signalements (point_id);
CREATE INDEX IF NOT EXISTS idx_signalements_statut ON signalements (statut);
CREATE INDEX IF NOT EXISTS idx_signalements_created ON signalements (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signalements_geom ON signalements USING GIST (geom);

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_signalement_modtime()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_signalements_modtime ON signalements;
CREATE TRIGGER update_signalements_modtime
    BEFORE UPDATE ON signalements
    FOR EACH ROW EXECUTE FUNCTION update_signalement_modtime();

-- Trigger pour créer la géométrie depuis lat/lng
CREATE OR REPLACE FUNCTION set_signalement_geom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS signalement_set_geom ON signalements;
CREATE TRIGGER signalement_set_geom
    BEFORE INSERT OR UPDATE ON signalements
    FOR EACH ROW EXECUTE FUNCTION set_signalement_geom();

-- Commentaire
COMMENT ON TABLE signalements IS 'Signalements citoyens depuis le portail public';


-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLE POINT_VISIBILITY (Visibilité publique par type)
-- ═══════════════════════════════════════════════════════════════════════════════
-- Configure quels champs sont visibles sur le portail citoyen pour chaque type

CREATE TABLE IF NOT EXISTS point_visibility_config (
    id SERIAL PRIMARY KEY,
    lexique_code VARCHAR(100) NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Champs visibles
    show_name BOOLEAN DEFAULT TRUE,
    show_type BOOLEAN DEFAULT TRUE,
    show_subtype BOOLEAN DEFAULT TRUE,
    show_photos BOOLEAN DEFAULT TRUE,
    show_condition BOOLEAN DEFAULT FALSE,
    show_comment BOOLEAN DEFAULT FALSE,
    show_custom_fields JSONB DEFAULT '[]',  -- Liste des champs custom visibles

    -- Options
    allow_signalement BOOLEAN DEFAULT TRUE,  -- Peut-on signaler un problème ?

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(lexique_code, project_id)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_visibility_lexique ON point_visibility_config (lexique_code);
CREATE INDEX IF NOT EXISTS idx_visibility_project ON point_visibility_config (project_id);

-- Commentaire
COMMENT ON TABLE point_visibility_config IS 'Configuration de la visibilité publique par type de point';


-- ═══════════════════════════════════════════════════════════════════════════════
-- FONCTION UTILITAIRE: Incrémenter le compteur de scans
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION increment_scan_count(p_short_code VARCHAR)
RETURNS VOID AS $$
BEGIN
    UPDATE short_codes
    SET scans_count = scans_count + 1,
        last_scanned_at = CURRENT_TIMESTAMP
    WHERE short_code = p_short_code;
END;
$$ LANGUAGE plpgsql;


-- ═══════════════════════════════════════════════════════════════════════════════
-- DONNÉES PAR DÉFAUT
-- ═══════════════════════════════════════════════════════════════════════════════

-- Types de problèmes par défaut pour les signalements
-- (à utiliser dans le portail citoyen)
-- INSERT INTO ... si vous voulez prédéfinir des valeurs

-- ═══════════════════════════════════════════════════════════════════════════════
-- FIN DE LA MIGRATION 004
-- ═══════════════════════════════════════════════════════════════════════════════

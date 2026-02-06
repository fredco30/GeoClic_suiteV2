-- ═══════════════════════════════════════════════════════════════════════════════
-- GéoClic V12 Pro - Schéma SQL Complet
-- ═══════════════════════════════════════════════════════════════════════════════
-- Version : 1.0 | Date : Janvier 2026
-- Description : Schéma PostgreSQL/PostGIS pour GéoClic V12 Pro MVP
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. EXTENSIONS
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- Pour le hachage des mots de passe

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. TYPES ENUM
-- ═══════════════════════════════════════════════════════════════════════════════

-- Statuts de synchronisation (workflow de validation)
CREATE TYPE sync_status_enum AS ENUM (
    'draft',      -- Brouillon local
    'pending',    -- Soumis pour validation
    'validated',  -- Validé par modérateur
    'rejected',   -- Rejeté (corrections demandées)
    'published',  -- Publié dans OGS
    'syncing',    -- Synchronisation en cours
    'error'       -- Erreur de synchronisation
);

-- Statuts de projet
CREATE TYPE project_status_enum AS ENUM (
    'En cours',
    'Terminé',
    'Archivé',
    'Suspendu'
);

-- Rôles utilisateur
CREATE TYPE user_role_enum AS ENUM (
    'admin',       -- Administrateur (tout)
    'moderator',   -- Modérateur (valide les données)
    'contributor', -- Contributeur (saisie terrain)
    'viewer'       -- Lecteur seul
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. TABLE UTILISATEURS
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role user_role_enum DEFAULT 'contributor',
    is_active BOOLEAN DEFAULT TRUE,
    permissions JSONB DEFAULT NULL,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche par email
CREATE INDEX idx_users_email ON users (email);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. TABLE PROJETS
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status project_status_enum DEFAULT 'En cours',
    is_active BOOLEAN DEFAULT TRUE,

    -- Informations collectivité
    collectivite_name VARCHAR(255),
    collectivite_address TEXT,
    responsable_name VARCHAR(255),
    responsable_email VARCHAR(255),

    -- Emprise géographique
    min_lat DOUBLE PRECISION,
    max_lat DOUBLE PRECISION,
    min_lng DOUBLE PRECISION,
    max_lng DOUBLE PRECISION,

    -- Dates projet
    start_date DATE,
    end_date DATE,

    -- Métadonnées
    metadata JSONB,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. TABLE LEXIQUE (Menus en cascade)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE lexique (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL,
    label VARCHAR(255) NOT NULL,
    parent_code VARCHAR(100),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    level INTEGER DEFAULT 0,
    display_order INTEGER DEFAULT 0,
    triggers_form BOOLEAN DEFAULT FALSE,
    form_type_ref VARCHAR(100),
    icon_name VARCHAR(50),
    color_value INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, project_id)
);

-- Index pour navigation hiérarchique
CREATE INDEX idx_lexique_parent ON lexique (parent_code, project_id);
CREATE INDEX idx_lexique_level ON lexique (level);
CREATE INDEX idx_lexique_project ON lexique (project_id);

-- Fonction pour obtenir le chemin complet d'un code
CREATE OR REPLACE FUNCTION get_lexique_path(p_code VARCHAR, p_separator VARCHAR DEFAULT ' > ')
RETURNS TEXT AS $$
DECLARE
    result TEXT := '';
    current_code VARCHAR := p_code;
    current_label VARCHAR;
    current_parent VARCHAR;
BEGIN
    WHILE current_code IS NOT NULL LOOP
        SELECT label, parent_code INTO current_label, current_parent
        FROM lexique WHERE code = current_code;

        IF current_label IS NOT NULL THEN
            IF result = '' THEN
                result := current_label;
            ELSE
                result := current_label || p_separator || result;
            END IF;
        END IF;

        current_code := current_parent;
    END LOOP;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 6. TABLE TYPE_FIELD_CONFIGS (Champs dynamiques)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE type_field_configs (
    id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    field_label VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL, -- text, number, dropdown, date, checkbox, photo
    is_required BOOLEAN DEFAULT FALSE,
    dropdown_options JSONB,
    default_value TEXT,
    display_order INTEGER DEFAULT 0,
    unit VARCHAR(20),
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    is_standard_field BOOLEAN DEFAULT FALSE,
    help_text TEXT,
    UNIQUE(type_name, field_name)
);

-- Index pour récupérer les champs d'un type
CREATE INDEX idx_type_field_configs_type ON type_field_configs (type_name);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 7. TABLE ZONES (Jointure spatiale automatique)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    zone_type VARCHAR(50), -- commune, quartier, secteur...
    geom GEOMETRY(Polygon, 4326),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index spatial
CREATE INDEX idx_zones_geom ON zones USING GIST (geom);

-- Fonction pour trouver la zone d'un point
CREATE OR REPLACE FUNCTION get_zone_for_point(point_geom GEOMETRY)
RETURNS VARCHAR(255) AS $$
    SELECT name FROM zones
    WHERE ST_Contains(geom, point_geom)
    ORDER BY zone_type DESC
    LIMIT 1;
$$ LANGUAGE SQL;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 8. TABLE STAGING (Zone tampon avant publication OGS)
-- ═══════════════════════════════════════════════════════════════════════════════
-- Cette table stocke les données en cours de validation AVANT leur publication
-- dans les tables OGS de production.

CREATE TABLE geoclic_staging (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- ═══════════════════════════════════════════════════════════════════════
    -- IDENTIFICATION
    -- ═══════════════════════════════════════════════════════════════════════
    name VARCHAR(255) NOT NULL,
    lexique_code VARCHAR(100), -- Pas de FK car lexique.code n'est unique que par projet
    type VARCHAR(100) NOT NULL,
    subtype VARCHAR(100),

    -- ═══════════════════════════════════════════════════════════════════════
    -- GÉOMÉTRIE
    -- ═══════════════════════════════════════════════════════════════════════
    geom_type VARCHAR(20) DEFAULT 'POINT', -- POINT, LINESTRING, POLYGON
    geom GEOMETRY(Geometry, 4326),
    gps_precision DOUBLE PRECISION,
    gps_source VARCHAR(50),
    altitude DOUBLE PRECISION,

    -- ═══════════════════════════════════════════════════════════════════════
    -- ÉTAT & WORKFLOW
    -- ═══════════════════════════════════════════════════════════════════════
    condition_state VARCHAR(50) DEFAULT 'Neuf',
    point_status VARCHAR(50) DEFAULT 'Projet',
    sync_status sync_status_enum DEFAULT 'draft',
    rejection_comment TEXT,
    comment TEXT,

    -- ═══════════════════════════════════════════════════════════════════════
    -- PHOTOS (JSONB array)
    -- ═══════════════════════════════════════════════════════════════════════
    photos JSONB DEFAULT '[]'::JSONB,

    -- ═══════════════════════════════════════════════════════════════════════
    -- ATTRIBUTS TECHNIQUES STANDARDS
    -- ═══════════════════════════════════════════════════════════════════════
    materiau VARCHAR(100),
    hauteur DOUBLE PRECISION,
    largeur DOUBLE PRECISION,
    date_installation DATE,
    duree_vie_annees INTEGER,
    marque_modele VARCHAR(255),

    -- ═══════════════════════════════════════════════════════════════════════
    -- MAINTENANCE
    -- ═══════════════════════════════════════════════════════════════════════
    date_derniere_intervention DATE,
    date_prochaine_intervention DATE,
    priorite VARCHAR(50),
    cout_remplacement DOUBLE PRECISION,

    -- ═══════════════════════════════════════════════════════════════════════
    -- PROPRIÉTÉS DYNAMIQUES (champs custom)
    -- ═══════════════════════════════════════════════════════════════════════
    custom_properties JSONB,

    -- ═══════════════════════════════════════════════════════════════════════
    -- CONTEXTE & TRAÇABILITÉ
    -- ═══════════════════════════════════════════════════════════════════════
    zone_name VARCHAR(255),

    -- Table OGS cible pour publication
    target_table VARCHAR(255),
    target_schema VARCHAR(100) DEFAULT 'public',

    -- Traçabilité
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    validated_by UUID REFERENCES users(id),

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,

    -- ═══════════════════════════════════════════════════════════════════════
    -- AFFICHAGE
    -- ═══════════════════════════════════════════════════════════════════════
    color_value INTEGER,
    icon_name VARCHAR(50),
    stroke_width DOUBLE PRECISION
);

-- Index
CREATE INDEX idx_staging_geom ON geoclic_staging USING GIST (geom);
CREATE INDEX idx_staging_project ON geoclic_staging (project_id);
CREATE INDEX idx_staging_sync_status ON geoclic_staging (sync_status);
CREATE INDEX idx_staging_lexique ON geoclic_staging (lexique_code);
CREATE INDEX idx_staging_created_by ON geoclic_staging (created_by);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 9. TABLE SYSTEM_SETTINGS (Parametres systeme)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,  -- Stocke en JSON
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id)
);

-- Index pour recherche rapide par cle
CREATE INDEX idx_system_settings_key ON system_settings (config_key);

-- Commentaire
COMMENT ON TABLE system_settings IS 'Parametres systeme (connexion PostGIS externe, etc.)';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 10. TABLE SYNC_HISTORY (Historique de synchronisation)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE sync_history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    device_id VARCHAR(100),
    sync_type VARCHAR(50), -- upload, download, full
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    points_uploaded INTEGER DEFAULT 0,
    points_downloaded INTEGER DEFAULT 0,
    points_failed INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 10. TRIGGERS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_modtime
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_projects_modtime
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_staging_modtime
    BEFORE UPDATE ON geoclic_staging
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Trigger pour détecter la zone automatiquement
CREATE OR REPLACE FUNCTION detect_zone_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.geom IS NOT NULL AND NEW.zone_name IS NULL THEN
        NEW.zone_name := get_zone_for_point(NEW.geom);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER staging_detect_zone
    BEFORE INSERT OR UPDATE ON geoclic_staging
    FOR EACH ROW EXECUTE FUNCTION detect_zone_trigger();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 11. FONCTION D'ENRICHISSEMENT DES TABLES OGS
-- ═══════════════════════════════════════════════════════════════════════════════
-- Cette fonction ajoute les colonnes geoclic_* à une table OGS existante

CREATE OR REPLACE FUNCTION add_geoclic_columns(
    p_schema VARCHAR,
    p_table VARCHAR
) RETURNS TEXT AS $$
DECLARE
    columns_added TEXT := '';
BEGIN
    -- Colonnes système GéoClic
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_lexique_code VARCHAR(100)', p_schema, p_table);
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_sync_status VARCHAR(50) DEFAULT ''synced''', p_schema, p_table);
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP', p_schema, p_table);
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_updated_by VARCHAR(100)', p_schema, p_table);
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_source VARCHAR(50) DEFAULT ''geoclic_mobile''', p_schema, p_table);

    -- Colonnes métier
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_condition_state VARCHAR(50)', p_schema, p_table);
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_priorite VARCHAR(50)', p_schema, p_table);
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_photos JSONB DEFAULT ''[]''::JSONB', p_schema, p_table);
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_comment TEXT', p_schema, p_table);
    EXECUTE format('ALTER TABLE %I.%I ADD COLUMN IF NOT EXISTS geoclic_custom_properties JSONB', p_schema, p_table);

    -- Créer le trigger de mise à jour
    EXECUTE format('
        CREATE OR REPLACE FUNCTION geoclic_update_%I_modtime()
        RETURNS TRIGGER AS $t$
        BEGIN
            NEW.geoclic_updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $t$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS geoclic_update_%I_modtime ON %I.%I;

        CREATE TRIGGER geoclic_update_%I_modtime
            BEFORE UPDATE ON %I.%I
            FOR EACH ROW
            EXECUTE FUNCTION geoclic_update_%I_modtime();
    ', p_table, p_table, p_schema, p_table, p_table, p_schema, p_table, p_table);

    columns_added := 'Colonnes geoclic_* ajoutées à ' || p_schema || '.' || p_table;

    RETURN columns_added;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 12. FONCTION DE PUBLICATION VERS OGS
-- ═══════════════════════════════════════════════════════════════════════════════
-- Publie les données validées depuis geoclic_staging vers une table OGS

CREATE OR REPLACE FUNCTION publish_to_ogs(
    p_staging_id UUID,
    p_target_schema VARCHAR DEFAULT 'public',
    p_target_table VARCHAR DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    v_staging RECORD;
    v_result TEXT;
BEGIN
    -- Récupérer les données de staging
    SELECT * INTO v_staging FROM geoclic_staging WHERE id = p_staging_id;

    IF v_staging IS NULL THEN
        RETURN 'Erreur: Point non trouvé dans staging';
    END IF;

    IF v_staging.sync_status != 'validated' THEN
        RETURN 'Erreur: Point non validé (statut: ' || v_staging.sync_status || ')';
    END IF;

    -- Utiliser la table cible spécifiée ou celle du staging
    IF p_target_table IS NULL THEN
        p_target_table := v_staging.target_table;
    END IF;

    IF p_target_table IS NULL THEN
        RETURN 'Erreur: Table cible non spécifiée';
    END IF;

    -- Mettre à jour le statut
    UPDATE geoclic_staging
    SET sync_status = 'published', published_at = CURRENT_TIMESTAMP
    WHERE id = p_staging_id;

    v_result := 'Point publié vers ' || p_target_schema || '.' || p_target_table;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 13. DONNÉES DE DÉMONSTRATION
-- ═══════════════════════════════════════════════════════════════════════════════

-- Utilisateur admin par défaut (mot de passe: admin123 - À CHANGER EN PRODUCTION!)
INSERT INTO users (email, password_hash, name, role) VALUES
('admin@geoclic.local', crypt('admin123', gen_salt('bf')), 'Administrateur', 'admin');

-- Projet de démonstration
INSERT INTO projects (name, description, collectivite_name) VALUES
('Projet Démo V12 Pro', 'Projet de démonstration GéoClic V12 Pro', 'Mairie Demo');

-- Lexique Éclairage Public
INSERT INTO lexique (code, label, level, icon_name, color_value) VALUES
('ECLAIRAGE', 'Éclairage public', 0, 'lightbulb', 4294961915);

INSERT INTO lexique (code, label, parent_code, level) VALUES
('ECLAIRAGE_LUMINAIRE', 'Luminaire', 'ECLAIRAGE', 1),
('ECLAIRAGE_MAT', 'Mât', 'ECLAIRAGE', 1);

INSERT INTO lexique (code, label, parent_code, level, triggers_form, form_type_ref) VALUES
('ECLAIRAGE_LUMINAIRE_LED', 'LED', 'ECLAIRAGE_LUMINAIRE', 2, TRUE, 'luminaire_led'),
('ECLAIRAGE_LUMINAIRE_SODIUM', 'Sodium', 'ECLAIRAGE_LUMINAIRE', 2, TRUE, 'luminaire_sodium'),
('ECLAIRAGE_MAT_ACIER', 'Acier', 'ECLAIRAGE_MAT', 2, TRUE, 'mat_acier'),
('ECLAIRAGE_MAT_BETON', 'Béton', 'ECLAIRAGE_MAT', 2, TRUE, 'mat_beton');

-- Champs pour formulaire luminaire_led
INSERT INTO type_field_configs (type_name, field_name, field_label, field_type, is_required, dropdown_options, display_order, unit) VALUES
('luminaire_led', 'puissance', 'Puissance', 'dropdown', TRUE, '["30", "50", "75", "100", "150"]', 1, 'W'),
('luminaire_led', 'temperature_couleur', 'Température couleur', 'dropdown', FALSE, '["3000K (chaud)", "4000K (neutre)", "5000K (froid)"]', 2, NULL),
('luminaire_led', 'materiau', 'Matériau', 'dropdown', FALSE, '["Aluminium", "Polycarbonate", "Inox"]', 3, NULL),
('luminaire_led', 'condition_etat', 'État', 'dropdown', TRUE, '["Neuf", "Très bon", "Bon", "Moyen", "Mauvais", "Hors service"]', 4, NULL),
('luminaire_led', 'date_installation', 'Date installation', 'date', FALSE, NULL, 5, NULL);

-- Zone de démonstration
INSERT INTO zones (name, code, zone_type, geom) VALUES
('Centre-Ville', 'CENTRE', 'quartier',
 ST_GeomFromText('POLYGON((1.43 43.59, 1.45 43.59, 1.45 43.61, 1.43 43.61, 1.43 43.59))', 4326));

-- ═══════════════════════════════════════════════════════════════════════════════
-- 14. TABLE PERIMETRES (Zones géographiques pour quartiers, secteurs, etc.)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS perimetres (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    perimetre_type VARCHAR(50) DEFAULT 'zone', -- quartier, secteur, zone_travaux, iris
    geom GEOMETRY(Polygon, 4326),
    population INTEGER,
    code_iris VARCHAR(20),
    code_insee VARCHAR(10),
    project_id UUID REFERENCES projects(id),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_perimetres_geom ON perimetres USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_perimetres_type ON perimetres(perimetre_type);
CREATE INDEX IF NOT EXISTS idx_perimetres_project ON perimetres(project_id);

COMMENT ON TABLE perimetres IS 'Zones géographiques (quartiers, secteurs, zones de travaux)';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 15. TABLE SHORT_CODES (QR Codes)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS short_codes (
    id SERIAL PRIMARY KEY,
    short_code VARCHAR(10) UNIQUE NOT NULL,
    point_id UUID REFERENCES geoclic_staging(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    scans_count INTEGER DEFAULT 0,
    last_scanned_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_short_codes_code ON short_codes (short_code);
CREATE INDEX IF NOT EXISTS idx_short_codes_point ON short_codes (point_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 15. TABLE SIGNALEMENTS (Portail Citoyen)
-- ═══════════════════════════════════════════════════════════════════════════════

DO $$ BEGIN
    CREATE TYPE signalement_urgence AS ENUM ('faible', 'normal', 'urgent', 'critique');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE signalement_statut AS ENUM ('nouveau', 'pris_en_compte', 'en_cours', 'traite', 'rejete', 'archive');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS signalements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    point_id UUID REFERENCES geoclic_staging(id) ON DELETE SET NULL,
    type_probleme VARCHAR(100) NOT NULL,
    description TEXT,
    urgence signalement_urgence DEFAULT 'normal',
    email VARCHAR(255),
    telephone VARCHAR(20),
    nom_signalant VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    adresse TEXT,
    geom GEOMETRY(Point, 4326),
    photos JSONB DEFAULT '[]',
    statut signalement_statut DEFAULT 'nouveau',
    traite_par UUID REFERENCES users(id),
    traite_le TIMESTAMPTZ,
    commentaire_interne TEXT,
    commentaire_public TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    source VARCHAR(50) DEFAULT 'portail_citoyen'
);

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

-- ═══════════════════════════════════════════════════════════════════════════════
-- 16. TABLE POINT_VISIBILITY_CONFIG
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS point_visibility_config (
    id SERIAL PRIMARY KEY,
    lexique_code VARCHAR(100) NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    show_name BOOLEAN DEFAULT TRUE,
    show_type BOOLEAN DEFAULT TRUE,
    show_subtype BOOLEAN DEFAULT TRUE,
    show_photos BOOLEAN DEFAULT TRUE,
    show_condition BOOLEAN DEFAULT FALSE,
    show_comment BOOLEAN DEFAULT FALSE,
    show_custom_fields JSONB DEFAULT '[]',
    allow_signalement BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lexique_code, project_id)
);

CREATE INDEX IF NOT EXISTS idx_visibility_lexique ON point_visibility_config (lexique_code);
CREATE INDEX IF NOT EXISTS idx_visibility_project ON point_visibility_config (project_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 17. DEMANDES CITOYENS (Tables pour le portail citoyen)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES demandes_categories(id) ON DELETE CASCADE,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    icone VARCHAR(50) DEFAULT 'report_problem',
    couleur INTEGER DEFAULT 4288585374,
    actif BOOLEAN DEFAULT TRUE,
    ordre_affichage INTEGER DEFAULT 0,
    moderation_requise BOOLEAN DEFAULT FALSE,
    service_defaut_id UUID,
    delai_traitement_jours INTEGER DEFAULT 7,
    champs_config JSONB DEFAULT '[]',
    photo_obligatoire BOOLEAN DEFAULT FALSE,
    photo_max_count INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, nom)
);

CREATE INDEX IF NOT EXISTS idx_demandes_categories_project ON demandes_categories(project_id);
CREATE INDEX IF NOT EXISTS idx_demandes_categories_parent ON demandes_categories(parent_id);

CREATE TABLE IF NOT EXISTS demandes_citoyens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    numero_suivi VARCHAR(20) NOT NULL UNIQUE,
    categorie_id UUID NOT NULL REFERENCES demandes_categories(id),
    declarant_email VARCHAR(255) NOT NULL,
    declarant_telephone VARCHAR(20),
    declarant_nom VARCHAR(100),
    declarant_langue VARCHAR(5) DEFAULT 'fr',
    description TEXT NOT NULL,
    champs_supplementaires JSONB DEFAULT '{}',
    photos JSONB DEFAULT '[]',
    geom GEOMETRY(Point, 4326),
    adresse_approximative TEXT,
    quartier_id UUID REFERENCES perimetres(id),
    equipement_id UUID REFERENCES geoclic_staging(id),
    statut VARCHAR(30) DEFAULT 'nouveau',
    priorite VARCHAR(20) DEFAULT 'normale',
    service_assigne_id UUID,
    agent_assigne_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    date_prise_en_charge TIMESTAMPTZ,
    date_planification TIMESTAMPTZ,
    date_resolution TIMESTAMPTZ,
    date_cloture TIMESTAMPTZ,
    source VARCHAR(50) DEFAULT 'app_citoyen',
    user_agent TEXT,
    ip_hash VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_demandes_citoyens_project ON demandes_citoyens(project_id);
CREATE INDEX IF NOT EXISTS idx_demandes_citoyens_statut ON demandes_citoyens(statut);
CREATE INDEX IF NOT EXISTS idx_demandes_citoyens_categorie ON demandes_citoyens(categorie_id);
CREATE INDEX IF NOT EXISTS idx_demandes_citoyens_geom ON demandes_citoyens USING GIST(geom);

CREATE TABLE IF NOT EXISTS demandes_historique (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    demande_id UUID NOT NULL REFERENCES demandes_citoyens(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES users(id),
    agent_nom VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    ancien_statut VARCHAR(30),
    nouveau_statut VARCHAR(30),
    commentaire TEXT,
    commentaire_interne BOOLEAN DEFAULT FALSE,
    email_envoye BOOLEAN DEFAULT FALSE,
    email_destinataire VARCHAR(255),
    email_sujet VARCHAR(255),
    pieces_jointes JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_demandes_historique_demande ON demandes_historique(demande_id);

-- Séquence et fonction pour numéro de suivi
CREATE SEQUENCE IF NOT EXISTS demandes_numero_seq START 1;

CREATE OR REPLACE FUNCTION generate_numero_suivi()
RETURNS VARCHAR AS $$
BEGIN
    RETURN to_char(CURRENT_DATE, 'YYYY') || '-' || lpad(nextval('demandes_numero_seq')::TEXT, 5, '0');
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION auto_generate_numero_suivi()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.numero_suivi IS NULL OR NEW.numero_suivi = '' THEN
        NEW.numero_suivi := generate_numero_suivi();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auto_numero_suivi ON demandes_citoyens;
CREATE TRIGGER trg_auto_numero_suivi
    BEFORE INSERT ON demandes_citoyens
    FOR EACH ROW
    EXECUTE FUNCTION auto_generate_numero_suivi();

COMMENT ON TABLE demandes_categories IS 'Catégories pour les demandes citoyennes';
COMMENT ON TABLE demandes_citoyens IS 'Demandes/signalements des citoyens';
COMMENT ON TABLE demandes_historique IS 'Historique des actions sur les demandes';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 18. COMMENTAIRES SQL (Documentation)
-- ═══════════════════════════════════════════════════════════════════════════════

COMMENT ON TABLE users IS 'Utilisateurs GéoClic avec rôles (admin, moderator, contributor, viewer)';
COMMENT ON TABLE projects IS 'Projets/Chantiers de collecte de données';
COMMENT ON TABLE lexique IS 'Dictionnaire hiérarchique pour menus en cascade';
COMMENT ON TABLE type_field_configs IS 'Configuration des champs dynamiques par type';
COMMENT ON TABLE zones IS 'Zones géographiques pour jointure spatiale automatique';
COMMENT ON TABLE geoclic_staging IS 'Zone tampon pour validation avant publication OGS';
COMMENT ON TABLE sync_history IS 'Historique des synchronisations Mobile ↔ Serveur';
COMMENT ON TABLE short_codes IS 'Codes courts pour QR codes (format GC-XXXXXX)';
COMMENT ON TABLE signalements IS 'Signalements citoyens depuis le portail public';
COMMENT ON TABLE point_visibility_config IS 'Configuration de la visibilité publique par type de point';

COMMENT ON FUNCTION add_geoclic_columns IS 'Ajoute les colonnes geoclic_* à une table OGS existante';
COMMENT ON FUNCTION publish_to_ogs IS 'Publie un point validé depuis staging vers OGS';
COMMENT ON FUNCTION get_lexique_path IS 'Retourne le chemin complet d''un code Lexique';
COMMENT ON FUNCTION get_zone_for_point IS 'Détecte la zone contenant un point GPS';

-- ═══════════════════════════════════════════════════════════════════════════════
-- FIN DU SCHÉMA
-- ═══════════════════════════════════════════════════════════════════════════════

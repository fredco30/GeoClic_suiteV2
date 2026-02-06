-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 005: Demandes Citoyens (Portail Citoyen Phase 3)
-- GéoClic Suite V14
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. EXTENSION DE LA TABLE PERIMETRES POUR LES QUARTIERS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Ajouter le type de périmètre
ALTER TABLE perimetres ADD COLUMN IF NOT EXISTS perimetre_type VARCHAR(50) DEFAULT 'zone';
COMMENT ON COLUMN perimetres.perimetre_type IS 'Type: quartier, secteur, zone_travaux, iris, autre';

-- Ajouter les métadonnées pour les quartiers
ALTER TABLE perimetres ADD COLUMN IF NOT EXISTS population INTEGER;
ALTER TABLE perimetres ADD COLUMN IF NOT EXISTS code_iris VARCHAR(20);
ALTER TABLE perimetres ADD COLUMN IF NOT EXISTS code_insee VARCHAR(10);
ALTER TABLE perimetres ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);

-- Index pour filtrer par type
CREATE INDEX IF NOT EXISTS idx_perimetres_type ON perimetres(perimetre_type);
CREATE INDEX IF NOT EXISTS idx_perimetres_project ON perimetres(project_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. CATÉGORIES DE DÉCLARATIONS CITOYENNES
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES demandes_categories(id) ON DELETE CASCADE,

    -- Informations
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    icone VARCHAR(50) DEFAULT 'report_problem',
    couleur INTEGER DEFAULT 4288585374, -- Orange par défaut

    -- Configuration
    actif BOOLEAN DEFAULT TRUE,
    ordre_affichage INTEGER DEFAULT 0,

    -- Workflow
    moderation_requise BOOLEAN DEFAULT FALSE,
    service_defaut_id UUID, -- Référence vers une table services si elle existe
    delai_traitement_jours INTEGER DEFAULT 7,

    -- Champs du formulaire (JSONB flexible)
    champs_config JSONB DEFAULT '[]',
    -- Exemple: [{"nom": "taille", "label": "Taille estimée", "type": "select", "options": ["Petit", "Moyen", "Grand"], "requis": true}]

    -- Photo
    photo_obligatoire BOOLEAN DEFAULT FALSE,
    photo_max_count INTEGER DEFAULT 3,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, nom)
);

CREATE INDEX idx_demandes_categories_project ON demandes_categories(project_id);
CREATE INDEX idx_demandes_categories_parent ON demandes_categories(parent_id);
CREATE INDEX idx_demandes_categories_actif ON demandes_categories(actif);

COMMENT ON TABLE demandes_categories IS 'Catégories configurables pour les déclarations citoyennes';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. DEMANDES CITOYENNES
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_citoyens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Numéro de suivi (format: YYYY-NNNNN)
    numero_suivi VARCHAR(20) NOT NULL UNIQUE,

    -- Catégorisation
    categorie_id UUID NOT NULL REFERENCES demandes_categories(id),

    -- Déclarant (pas anonyme)
    declarant_email VARCHAR(255) NOT NULL,
    declarant_telephone VARCHAR(20),
    declarant_nom VARCHAR(100),
    declarant_langue VARCHAR(5) DEFAULT 'fr', -- fr, en, es, de, etc.

    -- Contenu
    description TEXT NOT NULL,
    champs_supplementaires JSONB DEFAULT '{}',

    -- Photos (URLs)
    photos JSONB DEFAULT '[]',
    -- Exemple: ["https://..../photo1.jpg", "https://..../photo2.jpg"]

    -- Géolocalisation
    geom GEOMETRY(Point, 4326),
    adresse_approximative TEXT,
    quartier_id UUID REFERENCES perimetres(id),

    -- Lien vers équipement existant (si signalement sur QR code)
    equipement_id UUID REFERENCES geoclic_staging(id),

    -- Workflow
    statut VARCHAR(30) DEFAULT 'nouveau',
    -- Statuts: nouveau, en_moderation, accepte, en_cours, planifie, traite, rejete, cloture

    priorite VARCHAR(20) DEFAULT 'normale',
    -- Priorités: basse, normale, haute, urgente

    -- Attribution
    service_assigne_id UUID,
    agent_assigne_id UUID REFERENCES users(id),

    -- Dates
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    date_prise_en_charge TIMESTAMP WITH TIME ZONE,
    date_planification TIMESTAMP WITH TIME ZONE,
    date_resolution TIMESTAMP WITH TIME ZONE,
    date_cloture TIMESTAMP WITH TIME ZONE,

    -- Métadonnées
    source VARCHAR(50) DEFAULT 'app_citoyen', -- app_citoyen, qr_code, web, email
    user_agent TEXT,
    ip_hash VARCHAR(64) -- Hash de l'IP pour anti-abus (pas l'IP en clair)
);

-- Index spatiaux et de recherche
CREATE INDEX idx_demandes_citoyens_project ON demandes_citoyens(project_id);
CREATE INDEX idx_demandes_citoyens_statut ON demandes_citoyens(statut);
CREATE INDEX idx_demandes_citoyens_categorie ON demandes_citoyens(categorie_id);
CREATE INDEX idx_demandes_citoyens_quartier ON demandes_citoyens(quartier_id);
CREATE INDEX idx_demandes_citoyens_email ON demandes_citoyens(declarant_email);
CREATE INDEX idx_demandes_citoyens_created ON demandes_citoyens(created_at DESC);
CREATE INDEX idx_demandes_citoyens_geom ON demandes_citoyens USING GIST(geom);

COMMENT ON TABLE demandes_citoyens IS 'Demandes/signalements des citoyens via le portail ou l''app';

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_demandes_citoyens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_demandes_citoyens_updated_at
    BEFORE UPDATE ON demandes_citoyens
    FOR EACH ROW
    EXECUTE FUNCTION update_demandes_citoyens_updated_at();

-- Trigger pour attribution automatique du quartier
CREATE OR REPLACE FUNCTION assign_quartier_to_demande()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.geom IS NOT NULL AND NEW.quartier_id IS NULL THEN
        SELECT id INTO NEW.quartier_id
        FROM perimetres
        WHERE perimetre_type = 'quartier'
          AND project_id = NEW.project_id
          AND ST_Contains(geom, NEW.geom)
        LIMIT 1;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_assign_quartier
    BEFORE INSERT OR UPDATE ON demandes_citoyens
    FOR EACH ROW
    EXECUTE FUNCTION assign_quartier_to_demande();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. HISTORIQUE DES DEMANDES (RÉPONSES ET ACTIONS)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_historique (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demande_id UUID NOT NULL REFERENCES demandes_citoyens(id) ON DELETE CASCADE,

    -- Auteur
    agent_id UUID REFERENCES users(id),
    agent_nom VARCHAR(100), -- Stocké pour historique même si user supprimé

    -- Action
    action VARCHAR(50) NOT NULL,
    -- Actions: creation, changement_statut, assignation, commentaire, reponse_citoyen,
    --          planification, resolution, rejet, cloture, reouverture

    ancien_statut VARCHAR(30),
    nouveau_statut VARCHAR(30),

    -- Contenu
    commentaire TEXT,
    commentaire_interne BOOLEAN DEFAULT FALSE, -- True = visible uniquement agents

    -- Email envoyé
    email_envoye BOOLEAN DEFAULT FALSE,
    email_destinataire VARCHAR(255),
    email_sujet VARCHAR(255),

    -- Pièces jointes
    pieces_jointes JSONB DEFAULT '[]',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_demandes_historique_demande ON demandes_historique(demande_id);
CREATE INDEX idx_demandes_historique_agent ON demandes_historique(agent_id);
CREATE INDEX idx_demandes_historique_created ON demandes_historique(created_at DESC);

COMMENT ON TABLE demandes_historique IS 'Historique complet des actions et réponses sur les demandes';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. TEMPLATES DE RÉPONSES
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Informations
    titre VARCHAR(100) NOT NULL,
    contenu TEXT NOT NULL,

    -- Contexte d'utilisation
    categorie_id UUID REFERENCES demandes_categories(id), -- NULL = toutes catégories
    statut_cible VARCHAR(30), -- Statut après utilisation du template

    -- Configuration
    actif BOOLEAN DEFAULT TRUE,
    ordre_affichage INTEGER DEFAULT 0,

    -- Multi-langue
    langue VARCHAR(5) DEFAULT 'fr',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_demandes_templates_project ON demandes_templates(project_id);
CREATE INDEX idx_demandes_templates_categorie ON demandes_templates(categorie_id);

COMMENT ON TABLE demandes_templates IS 'Templates de réponses pré-écrites pour les agents';

-- Insérer quelques templates par défaut (seront copiés pour chaque projet)
-- Note: Ces templates sont des exemples, ils seront créés via l'API pour chaque projet

-- ═══════════════════════════════════════════════════════════════════════════════
-- 6. CONFIGURATION EMAIL PAR PROJET
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_config_email (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,

    -- Provider: 'smtp' ou 'microsoft'
    provider VARCHAR(20) DEFAULT 'smtp',

    -- SMTP Configuration (pour provider='smtp')
    smtp_host VARCHAR(255),
    smtp_port INTEGER DEFAULT 587,
    smtp_user VARCHAR(255),
    smtp_password TEXT, -- Note: stocker chiffré en production
    smtp_use_tls BOOLEAN DEFAULT TRUE,

    -- Microsoft Graph API (pour provider='microsoft' - Office 365 / Outlook)
    -- Créer une App Registration dans Azure AD Portal
    ms_tenant_id VARCHAR(100),      -- ID du tenant Azure AD
    ms_client_id VARCHAR(100),      -- Application (client) ID
    ms_client_secret TEXT,          -- Client Secret (stocker chiffré)

    -- Expéditeur (commun aux deux providers)
    email_from VARCHAR(255),         -- Adresse email expéditeur
    email_from_name VARCHAR(100),    -- Nom affiché
    email_reply_to VARCHAR(255),

    -- Templates email (avec placeholders {numero_suivi}, {statut}, etc.)
    template_nouveau TEXT,
    template_pris_en_charge TEXT,
    template_planifie TEXT,
    template_traite TEXT,
    template_rejete TEXT,

    -- Options
    envoyer_notifications BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE demandes_config_email IS 'Configuration email par projet (SMTP ou Microsoft Graph API pour Office 365)';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 7. STATISTIQUES AGRÉGÉES (pour performance)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_stats_quotidiennes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    date_stat DATE NOT NULL,

    -- Compteurs
    total_nouvelles INTEGER DEFAULT 0,
    total_traitees INTEGER DEFAULT 0,
    total_rejetees INTEGER DEFAULT 0,

    -- Par catégorie (JSONB)
    par_categorie JSONB DEFAULT '{}',
    -- Exemple: {"voirie": 5, "proprete": 3}

    -- Par quartier (JSONB)
    par_quartier JSONB DEFAULT '{}',
    -- Exemple: {"centre-ville": 4, "les-hauts": 2}

    -- Temps de traitement moyen (en heures)
    temps_moyen_traitement_heures DECIMAL(10,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, date_stat)
);

CREATE INDEX idx_demandes_stats_project_date ON demandes_stats_quotidiennes(project_id, date_stat DESC);

COMMENT ON TABLE demandes_stats_quotidiennes IS 'Statistiques agrégées quotidiennes pour les tableaux de bord';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 8. ANTI-ABUS : RATE LIMITING
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identifiant (email ou hash IP)
    identifier VARCHAR(255) NOT NULL,
    identifier_type VARCHAR(20) NOT NULL, -- 'email' ou 'ip_hash'

    -- Compteur
    count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Blocage
    blocked_until TIMESTAMP WITH TIME ZONE,
    block_reason TEXT,

    UNIQUE(identifier, identifier_type)
);

CREATE INDEX idx_rate_limits_identifier ON demandes_rate_limits(identifier, identifier_type);
CREATE INDEX idx_rate_limits_window ON demandes_rate_limits(window_start);

COMMENT ON TABLE demandes_rate_limits IS 'Limitation du nombre de demandes par email/IP';

-- Fonction pour vérifier/incrémenter le rate limit
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_identifier VARCHAR,
    p_identifier_type VARCHAR,
    p_max_per_day INTEGER DEFAULT 5
)
RETURNS BOOLEAN AS $$
DECLARE
    v_record RECORD;
    v_window_start TIMESTAMP WITH TIME ZONE;
BEGIN
    v_window_start := date_trunc('day', CURRENT_TIMESTAMP);

    -- Vérifier si bloqué
    SELECT * INTO v_record
    FROM demandes_rate_limits
    WHERE identifier = p_identifier
      AND identifier_type = p_identifier_type;

    IF FOUND THEN
        -- Vérifier si blocage actif
        IF v_record.blocked_until IS NOT NULL AND v_record.blocked_until > CURRENT_TIMESTAMP THEN
            RETURN FALSE;
        END IF;

        -- Reset si nouvelle fenêtre
        IF v_record.window_start < v_window_start THEN
            UPDATE demandes_rate_limits
            SET count = 1, window_start = v_window_start, blocked_until = NULL
            WHERE identifier = p_identifier AND identifier_type = p_identifier_type;
            RETURN TRUE;
        END IF;

        -- Incrémenter
        IF v_record.count >= p_max_per_day THEN
            UPDATE demandes_rate_limits
            SET blocked_until = CURRENT_TIMESTAMP + INTERVAL '1 day',
                block_reason = 'Limite quotidienne atteinte'
            WHERE identifier = p_identifier AND identifier_type = p_identifier_type;
            RETURN FALSE;
        END IF;

        UPDATE demandes_rate_limits
        SET count = count + 1
        WHERE identifier = p_identifier AND identifier_type = p_identifier_type;
        RETURN TRUE;
    ELSE
        -- Créer l'entrée
        INSERT INTO demandes_rate_limits (identifier, identifier_type, count, window_start)
        VALUES (p_identifier, p_identifier_type, 1, v_window_start);
        RETURN TRUE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 9. SÉQUENCE POUR LES NUMÉROS DE SUIVI
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE SEQUENCE IF NOT EXISTS demandes_numero_seq START 1;

-- Fonction pour générer le numéro de suivi
CREATE OR REPLACE FUNCTION generate_numero_suivi()
RETURNS VARCHAR AS $$
DECLARE
    v_year VARCHAR(4);
    v_num INTEGER;
BEGIN
    v_year := to_char(CURRENT_DATE, 'YYYY');
    v_num := nextval('demandes_numero_seq');
    RETURN v_year || '-' || lpad(v_num::TEXT, 5, '0');
END;
$$ LANGUAGE plpgsql;

-- Trigger pour auto-générer le numéro de suivi
CREATE OR REPLACE FUNCTION auto_generate_numero_suivi()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.numero_suivi IS NULL OR NEW.numero_suivi = '' THEN
        NEW.numero_suivi := generate_numero_suivi();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_numero_suivi
    BEFORE INSERT ON demandes_citoyens
    FOR EACH ROW
    EXECUTE FUNCTION auto_generate_numero_suivi();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 10. VUES UTILES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Vue des demandes avec infos complètes
CREATE OR REPLACE VIEW v_demandes_completes AS
SELECT
    d.*,
    c.nom AS categorie_nom,
    c.icone AS categorie_icone,
    c.couleur AS categorie_couleur,
    p.name AS quartier_nom,
    ST_X(d.geom) AS longitude,
    ST_Y(d.geom) AS latitude,
    EXTRACT(EPOCH FROM (COALESCE(d.date_resolution, CURRENT_TIMESTAMP) - d.created_at))/3600 AS heures_depuis_creation
FROM demandes_citoyens d
LEFT JOIN demandes_categories c ON d.categorie_id = c.id
LEFT JOIN perimetres p ON d.quartier_id = p.id;

-- Vue des statistiques par quartier
CREATE OR REPLACE VIEW v_stats_par_quartier AS
SELECT
    p.project_id,
    p.id AS quartier_id,
    p.name AS quartier_nom,
    COUNT(d.id) AS total_demandes,
    COUNT(d.id) FILTER (WHERE d.statut = 'nouveau') AS nouvelles,
    COUNT(d.id) FILTER (WHERE d.statut IN ('en_cours', 'planifie')) AS en_cours,
    COUNT(d.id) FILTER (WHERE d.statut = 'traite') AS traitees,
    COUNT(d.id) FILTER (WHERE d.statut = 'rejete') AS rejetees,
    AVG(EXTRACT(EPOCH FROM (COALESCE(d.date_resolution, CURRENT_TIMESTAMP) - d.created_at))/3600)
        FILTER (WHERE d.date_resolution IS NOT NULL) AS temps_moyen_heures
FROM perimetres p
LEFT JOIN demandes_citoyens d ON d.quartier_id = p.id
WHERE p.perimetre_type = 'quartier'
GROUP BY p.project_id, p.id, p.name;

COMMENT ON VIEW v_demandes_completes IS 'Vue enrichie des demandes avec catégorie et quartier';
COMMENT ON VIEW v_stats_par_quartier IS 'Statistiques agrégées par quartier';

-- ═══════════════════════════════════════════════════════════════════════════════
-- FIN DE LA MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════════

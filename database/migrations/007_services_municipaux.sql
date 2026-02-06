-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 007: Services Municipaux et Affectation Automatique
-- GéoClic Suite V14 - Phase 3 GeoClic Demandes V2
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. TABLE DES SERVICES MUNICIPAUX
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Informations du service
    nom VARCHAR(100) NOT NULL,
    code VARCHAR(20), -- Code court (ex: "VOI", "ESP", "URB")
    description TEXT,

    -- Contact
    email VARCHAR(255),
    telephone VARCHAR(20),
    responsable_nom VARCHAR(100),

    -- Configuration
    actif BOOLEAN DEFAULT TRUE,
    ordre_affichage INTEGER DEFAULT 0,
    couleur VARCHAR(7) DEFAULT '#3b82f6', -- Couleur hex pour l'interface
    icone VARCHAR(50) DEFAULT 'business',

    -- Notifications
    notifier_nouvelle_demande BOOLEAN DEFAULT TRUE,
    notifier_changement_statut BOOLEAN DEFAULT FALSE,
    emails_notification JSONB DEFAULT '[]', -- Liste d'emails supplémentaires

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, nom),
    UNIQUE(project_id, code)
);

CREATE INDEX idx_demandes_services_project ON demandes_services(project_id);
CREATE INDEX idx_demandes_services_actif ON demandes_services(actif);

COMMENT ON TABLE demandes_services IS 'Services municipaux pour l''affectation des demandes citoyennes';

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_demandes_services_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_demandes_services_updated_at
    BEFORE UPDATE ON demandes_services
    FOR EACH ROW
    EXECUTE FUNCTION update_demandes_services_updated_at();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. AGENTS PAR SERVICE (TABLE DE LIAISON)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_services_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID NOT NULL REFERENCES demandes_services(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Rôle dans le service
    role VARCHAR(30) DEFAULT 'agent', -- 'responsable', 'agent'

    -- Configuration
    peut_assigner BOOLEAN DEFAULT FALSE, -- Peut assigner des demandes à d'autres
    reçoit_notifications BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(service_id, user_id)
);

CREATE INDEX idx_services_agents_service ON demandes_services_agents(service_id);
CREATE INDEX idx_services_agents_user ON demandes_services_agents(user_id);

COMMENT ON TABLE demandes_services_agents IS 'Agents appartenant à chaque service';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. AJOUTER LES CLÉS ÉTRANGÈRES MANQUANTES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Ajouter FK sur demandes_categories.service_defaut_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_categories_service_defaut'
    ) THEN
        ALTER TABLE demandes_categories
        ADD CONSTRAINT fk_categories_service_defaut
        FOREIGN KEY (service_defaut_id) REFERENCES demandes_services(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Ajouter FK sur demandes_citoyens.service_assigne_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_demandes_service_assigne'
    ) THEN
        ALTER TABLE demandes_citoyens
        ADD CONSTRAINT fk_demandes_service_assigne
        FOREIGN KEY (service_assigne_id) REFERENCES demandes_services(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Index sur service_assigne_id pour les requêtes
CREATE INDEX IF NOT EXISTS idx_demandes_service_assigne ON demandes_citoyens(service_assigne_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. TRIGGER POUR AFFECTATION AUTOMATIQUE DU SERVICE
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION auto_assign_service_to_demande()
RETURNS TRIGGER AS $$
DECLARE
    v_service_id UUID;
BEGIN
    -- Si pas de service assigné et qu'une catégorie est définie
    IF NEW.service_assigne_id IS NULL AND NEW.categorie_id IS NOT NULL THEN
        -- Récupérer le service par défaut de la catégorie
        SELECT service_defaut_id INTO v_service_id
        FROM demandes_categories
        WHERE id = NEW.categorie_id;

        -- Assigner si trouvé
        IF v_service_id IS NOT NULL THEN
            NEW.service_assigne_id := v_service_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Créer le trigger (après le trigger de quartier)
DROP TRIGGER IF EXISTS trg_auto_assign_service ON demandes_citoyens;
CREATE TRIGGER trg_auto_assign_service
    BEFORE INSERT ON demandes_citoyens
    FOR EACH ROW
    EXECUTE FUNCTION auto_assign_service_to_demande();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. VUE ENRICHIE AVEC SERVICE
-- ═══════════════════════════════════════════════════════════════════════════════

-- Mettre à jour la vue des demandes complètes
CREATE OR REPLACE VIEW v_demandes_completes AS
SELECT
    d.*,
    c.nom AS categorie_nom,
    c.icone AS categorie_icone,
    c.couleur AS categorie_couleur,
    p.name AS quartier_nom,
    s.nom AS service_nom,
    s.code AS service_code,
    s.couleur AS service_couleur,
    u.email AS agent_email,
    u.name AS agent_nom_complet,
    ST_X(d.geom) AS longitude,
    ST_Y(d.geom) AS latitude,
    EXTRACT(EPOCH FROM (COALESCE(d.date_resolution, CURRENT_TIMESTAMP) - d.created_at))/3600 AS heures_depuis_creation
FROM demandes_citoyens d
LEFT JOIN demandes_categories c ON d.categorie_id = c.id
LEFT JOIN perimetres p ON d.quartier_id = p.id
LEFT JOIN demandes_services s ON d.service_assigne_id = s.id
LEFT JOIN users u ON d.agent_assigne_id = u.id;

-- Vue des statistiques par service
CREATE OR REPLACE VIEW v_stats_par_service AS
SELECT
    s.project_id,
    s.id AS service_id,
    s.nom AS service_nom,
    s.code AS service_code,
    s.couleur AS service_couleur,
    COUNT(d.id) AS total_demandes,
    COUNT(d.id) FILTER (WHERE d.statut = 'nouveau') AS nouvelles,
    COUNT(d.id) FILTER (WHERE d.statut IN ('en_moderation', 'accepte')) AS a_traiter,
    COUNT(d.id) FILTER (WHERE d.statut IN ('en_cours', 'planifie')) AS en_cours,
    COUNT(d.id) FILTER (WHERE d.statut = 'traite') AS traitees,
    COUNT(d.id) FILTER (WHERE d.statut IN ('cloture', 'rejete')) AS cloturees,
    AVG(EXTRACT(EPOCH FROM (COALESCE(d.date_resolution, CURRENT_TIMESTAMP) - d.created_at))/3600)
        FILTER (WHERE d.date_resolution IS NOT NULL) AS temps_moyen_heures
FROM demandes_services s
LEFT JOIN demandes_citoyens d ON d.service_assigne_id = s.id
WHERE s.actif = TRUE
GROUP BY s.project_id, s.id, s.nom, s.code, s.couleur;

COMMENT ON VIEW v_stats_par_service IS 'Statistiques agrégées par service municipal';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 6. FONCTION POUR RÉAFFECTER LES DEMANDES D'UN SERVICE
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION reassign_demandes_to_service(
    p_from_service_id UUID,
    p_to_service_id UUID
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE demandes_citoyens
    SET service_assigne_id = p_to_service_id,
        updated_at = CURRENT_TIMESTAMP
    WHERE service_assigne_id = p_from_service_id
      AND statut NOT IN ('cloture', 'rejete', 'traite');

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION reassign_demandes_to_service IS 'Réaffecte les demandes ouvertes d''un service vers un autre';

-- ═══════════════════════════════════════════════════════════════════════════════
-- FIN DE LA MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════════

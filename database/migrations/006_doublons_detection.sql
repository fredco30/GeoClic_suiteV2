-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 006: Détection des doublons (Phase 2 GeoClic Demandes V2)
-- GéoClic Suite V14
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. COLONNE POUR LIER LES DOUBLONS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Ajouter la colonne pour lier une demande à son doublon potentiel
ALTER TABLE demandes_citoyens ADD COLUMN IF NOT EXISTS doublon_de_id UUID REFERENCES demandes_citoyens(id) ON DELETE SET NULL;
ALTER TABLE demandes_citoyens ADD COLUMN IF NOT EXISTS est_doublon BOOLEAN DEFAULT FALSE;

-- Index pour rechercher les doublons
CREATE INDEX IF NOT EXISTS idx_demandes_citoyens_doublon ON demandes_citoyens(doublon_de_id) WHERE doublon_de_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_demandes_citoyens_est_doublon ON demandes_citoyens(est_doublon) WHERE est_doublon = TRUE;

COMMENT ON COLUMN demandes_citoyens.doublon_de_id IS 'ID de la demande originale si celle-ci est un doublon';
COMMENT ON COLUMN demandes_citoyens.est_doublon IS 'Indique si cette demande a été marquée comme doublon';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. FONCTION DE DÉTECTION DES DOUBLONS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Fonction pour trouver les doublons potentiels
-- Critères: même catégorie, dans un rayon de 50m, créé dans les 30 derniers jours
CREATE OR REPLACE FUNCTION find_duplicate_demandes(
    p_categorie_id UUID,
    p_lat DOUBLE PRECISION,
    p_lng DOUBLE PRECISION,
    p_project_id UUID,
    p_rayon_metres INTEGER DEFAULT 50,
    p_jours INTEGER DEFAULT 30,
    p_exclude_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    numero_suivi VARCHAR(20),
    description TEXT,
    statut VARCHAR(30),
    distance_metres DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE,
    declarant_email VARCHAR(255),
    photos JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.numero_suivi,
        d.description,
        d.statut,
        ST_Distance(
            d.geom::geography,
            ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography
        ) AS distance_metres,
        d.created_at,
        d.declarant_email,
        d.photos
    FROM demandes_citoyens d
    WHERE d.project_id = p_project_id
      AND d.categorie_id = p_categorie_id
      AND d.geom IS NOT NULL
      AND d.created_at >= (CURRENT_TIMESTAMP - (p_jours || ' days')::INTERVAL)
      AND d.statut NOT IN ('rejete', 'cloture')  -- Ignorer les demandes fermées
      AND d.est_doublon = FALSE  -- Ne pas montrer les doublons déjà marqués
      AND (p_exclude_id IS NULL OR d.id != p_exclude_id)  -- Exclure la demande elle-même
      AND ST_DWithin(
          d.geom::geography,
          ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)::geography,
          p_rayon_metres
      )
    ORDER BY distance_metres ASC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_duplicate_demandes IS 'Trouve les demandes similaires à proximité (même catégorie, <50m, <30 jours)';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. FONCTION POUR CALCULER LE SCORE DE SIMILARITÉ
-- ═══════════════════════════════════════════════════════════════════════════════

-- Fonction pour calculer un score de similarité (0-100)
CREATE OR REPLACE FUNCTION calculate_similarity_score(
    p_distance_metres DOUBLE PRECISION,
    p_days_diff INTEGER,
    p_same_email BOOLEAN
)
RETURNS INTEGER AS $$
DECLARE
    score INTEGER := 0;
BEGIN
    -- Score basé sur la distance (max 40 points)
    -- 0m = 40 points, 50m = 0 points
    IF p_distance_metres < 50 THEN
        score := score + GREATEST(0, 40 - (p_distance_metres * 0.8)::INTEGER);
    END IF;

    -- Score basé sur la date (max 30 points)
    -- 0 jours = 30 points, 30 jours = 0 points
    IF p_days_diff < 30 THEN
        score := score + GREATEST(0, 30 - p_days_diff);
    END IF;

    -- Bonus si même email (30 points)
    IF p_same_email THEN
        score := score + 30;
    END IF;

    RETURN LEAST(100, score);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_similarity_score IS 'Calcule un score de similarité entre 0 et 100';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. VUE POUR LES DOUBLONS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Vue des demandes avec leurs doublons liés
CREATE OR REPLACE VIEW v_demandes_avec_doublons AS
SELECT
    d.*,
    c.nom AS categorie_nom,
    original.numero_suivi AS doublon_de_numero,
    (
        SELECT COUNT(*)
        FROM demandes_citoyens sub
        WHERE sub.doublon_de_id = d.id
    ) AS nb_doublons_lies
FROM demandes_citoyens d
LEFT JOIN demandes_categories c ON d.categorie_id = c.id
LEFT JOIN demandes_citoyens original ON d.doublon_de_id = original.id;

COMMENT ON VIEW v_demandes_avec_doublons IS 'Vue enrichie des demandes avec informations sur les doublons';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. TRIGGER POUR DÉTECTER AUTOMATIQUEMENT LES DOUBLONS À LA CRÉATION
-- ═══════════════════════════════════════════════════════════════════════════════

-- Fonction trigger pour suggérer un doublon lors de la création
CREATE OR REPLACE FUNCTION check_potential_duplicate()
RETURNS TRIGGER AS $$
DECLARE
    v_potential_duplicate RECORD;
BEGIN
    -- Ne vérifier que si on a des coordonnées
    IF NEW.geom IS NOT NULL THEN
        SELECT * INTO v_potential_duplicate
        FROM find_duplicate_demandes(
            NEW.categorie_id,
            ST_Y(NEW.geom),  -- latitude
            ST_X(NEW.geom),  -- longitude
            NEW.project_id,
            50,  -- 50 mètres
            30,  -- 30 jours
            NEW.id
        )
        LIMIT 1;

        -- Si on trouve un doublon très proche (< 10m) du même email, marquer automatiquement
        IF v_potential_duplicate.id IS NOT NULL
           AND v_potential_duplicate.distance_metres < 10
           AND v_potential_duplicate.declarant_email = NEW.declarant_email THEN
            NEW.doublon_de_id := v_potential_duplicate.id;
            NEW.est_doublon := TRUE;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: Le trigger est désactivé par défaut car on préfère la détection via API
-- pour permettre au citoyen de confirmer
-- CREATE TRIGGER trg_check_duplicate
--     BEFORE INSERT ON demandes_citoyens
--     FOR EACH ROW
--     EXECUTE FUNCTION check_potential_duplicate();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 6. ACTION POUR MARQUER COMME DOUBLON
-- ═══════════════════════════════════════════════════════════════════════════════

-- Ajouter l'action 'doublon' dans l'historique possible
-- (L'enum n'existe pas en PostgreSQL pour cette table, on utilise VARCHAR)

-- ═══════════════════════════════════════════════════════════════════════════════
-- FIN DE LA MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════════

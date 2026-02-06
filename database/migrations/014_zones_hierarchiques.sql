-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 014: Zones Hiérarchiques (Fusion zones + perimetres)
-- GéoClic Suite V14 - Phase 5 GeoClic Demandes V2
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- OBJECTIF:
-- Fusionner les tables 'zones' et 'perimetres' en une seule table hiérarchique.
-- Structure: Commune (level=1) → Quartier (level=2) → Secteur (level=3)
--
-- CHANGEMENTS:
-- 1. Enrichir 'perimetres' avec parent_id, level, is_global
-- 2. Migrer les données de 'zones' vers 'perimetres'
-- 3. Modifier les triggers et fonctions
-- 4. Supprimer la table 'zones'
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. ENRICHIR LA TABLE PERIMETRES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Colonnes pour la hiérarchie
ALTER TABLE perimetres ADD COLUMN IF NOT EXISTS parent_id UUID REFERENCES perimetres(id) ON DELETE SET NULL;
ALTER TABLE perimetres ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 2;
ALTER TABLE perimetres ADD COLUMN IF NOT EXISTS is_global BOOLEAN DEFAULT FALSE;

-- Rendre project_id nullable pour les zones globales
ALTER TABLE perimetres ALTER COLUMN project_id DROP NOT NULL;

-- Index pour les nouvelles colonnes
CREATE INDEX IF NOT EXISTS idx_perimetres_parent ON perimetres(parent_id);
CREATE INDEX IF NOT EXISTS idx_perimetres_level ON perimetres(level);
CREATE INDEX IF NOT EXISTS idx_perimetres_global ON perimetres(is_global);
CREATE INDEX IF NOT EXISTS idx_perimetres_level_parent ON perimetres(level, parent_id);

-- Commentaires
COMMENT ON COLUMN perimetres.parent_id IS 'Zone parente (NULL pour communes/racines)';
COMMENT ON COLUMN perimetres.level IS 'Niveau hiérarchique: 1=Commune, 2=Quartier, 3=Secteur';
COMMENT ON COLUMN perimetres.is_global IS 'TRUE = zone partagée par tous les projets';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. METTRE À JOUR LES PERIMETRES EXISTANTS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Définir le level en fonction du perimetre_type existant
UPDATE perimetres SET level =
    CASE perimetre_type
        WHEN 'commune' THEN 1
        WHEN 'quartier' THEN 2
        WHEN 'iris' THEN 2
        WHEN 'secteur' THEN 3
        WHEN 'zone_travaux' THEN 3
        ELSE 2  -- Par défaut niveau quartier
    END
WHERE level IS NULL OR level = 2;  -- Ne met à jour que si pas déjà défini

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. MIGRER LES DONNÉES DE 'ZONES' VERS 'PERIMETRES'
-- ═══════════════════════════════════════════════════════════════════════════════

-- Migration seulement si la table zones existe et a des données
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'zones') THEN
        INSERT INTO perimetres (name, code, perimetre_type, geom, metadata, is_global, level, project_id, created_at)
        SELECT
            z.name,
            z.code,
            COALESCE(z.zone_type, 'quartier'),  -- perimetre_type depuis zone_type
            z.geom,
            z.metadata,
            TRUE,  -- Les zones étaient globales (pas de project_id)
            CASE z.zone_type
                WHEN 'commune' THEN 1
                WHEN 'quartier' THEN 2
                WHEN 'iris' THEN 2
                WHEN 'secteur' THEN 3
                ELSE 2
            END,
            NULL,  -- project_id NULL car global
            z.created_at
        FROM zones z
        WHERE NOT EXISTS (
            -- Éviter les doublons par code
            SELECT 1 FROM perimetres p
            WHERE p.code = z.code AND p.code IS NOT NULL
        );

        RAISE NOTICE 'Migration zones → perimetres terminée';
    ELSE
        RAISE NOTICE 'Table zones inexistante, pas de migration nécessaire';
    END IF;
END $$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. CONTRAINTES D'INTÉGRITÉ
-- ═══════════════════════════════════════════════════════════════════════════════

-- Level doit être entre 1 et 3
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_perimetres_level_range'
    ) THEN
        ALTER TABLE perimetres ADD CONSTRAINT chk_perimetres_level_range
            CHECK (level BETWEEN 1 AND 3);
    END IF;
END $$;

-- Fonction de vérification de la hiérarchie parent/enfant
CREATE OR REPLACE FUNCTION check_perimetre_hierarchy()
RETURNS TRIGGER AS $$
DECLARE
    parent_level INTEGER;
    parent_project_id UUID;
    parent_is_global BOOLEAN;
BEGIN
    -- Si pas de parent, doit être level 1 (ou on accepte level 2 pour rétrocompatibilité)
    IF NEW.parent_id IS NULL THEN
        IF NEW.level > 2 THEN
            RAISE EXCEPTION 'Une zone sans parent doit être de niveau 1 (commune) ou 2 (quartier racine)';
        END IF;
        RETURN NEW;
    END IF;

    -- Récupérer les infos du parent
    SELECT level, project_id, is_global
    INTO parent_level, parent_project_id, parent_is_global
    FROM perimetres WHERE id = NEW.parent_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Zone parente non trouvée: %', NEW.parent_id;
    END IF;

    -- Le level de l'enfant doit être > level du parent
    IF NEW.level <= parent_level THEN
        RAISE EXCEPTION 'Le niveau de la zone enfant (%) doit être supérieur au niveau du parent (%)',
            NEW.level, parent_level;
    END IF;

    -- Si le parent est spécifique à un projet, l'enfant doit être du même projet (ou global)
    IF parent_project_id IS NOT NULL AND NOT COALESCE(parent_is_global, FALSE) THEN
        IF NEW.project_id IS NOT NULL AND NEW.project_id != parent_project_id THEN
            RAISE EXCEPTION 'La zone enfant doit appartenir au même projet que son parent ou être globale';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Créer le trigger seulement s'il n'existe pas
DROP TRIGGER IF EXISTS trg_check_perimetre_hierarchy ON perimetres;
CREATE TRIGGER trg_check_perimetre_hierarchy
    BEFORE INSERT OR UPDATE ON perimetres
    FOR EACH ROW
    EXECUTE FUNCTION check_perimetre_hierarchy();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. MODIFIER LA FONCTION GET_ZONE_FOR_POINT
-- ═══════════════════════════════════════════════════════════════════════════════

-- Cette fonction est utilisée par le trigger detect_zone_trigger sur geoclic_staging
-- Elle doit maintenant chercher dans perimetres avec support des zones globales
CREATE OR REPLACE FUNCTION get_zone_for_point(point_geom GEOMETRY)
RETURNS VARCHAR(255) AS $$
    SELECT name FROM perimetres
    WHERE ST_Contains(geom, point_geom)
      AND (is_global = TRUE OR project_id IS NULL)  -- Zones globales seulement pour staging
    ORDER BY level DESC  -- Plus précis d'abord (secteur > quartier > commune)
    LIMIT 1;
$$ LANGUAGE SQL;

COMMENT ON FUNCTION get_zone_for_point IS 'Retourne le nom de la zone la plus précise contenant le point (zones globales uniquement)';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 6. MODIFIER LE TRIGGER D'ASSIGNATION DE QUARTIER
-- ═══════════════════════════════════════════════════════════════════════════════

-- Ce trigger assigne automatiquement un quartier aux demandes citoyennes
-- Il doit maintenant chercher le niveau le plus précis et supporter les zones globales
CREATE OR REPLACE FUNCTION assign_quartier_to_demande()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.geom IS NOT NULL AND NEW.quartier_id IS NULL THEN
        SELECT id INTO NEW.quartier_id
        FROM perimetres
        WHERE ST_Contains(geom, NEW.geom)
          AND (
              project_id = NEW.project_id  -- Zones du projet
              OR is_global = TRUE           -- OU zones globales
              OR project_id IS NULL         -- OU zones sans projet (legacy)
          )
        ORDER BY
            -- Priorité: zones du projet > zones globales
            CASE WHEN project_id = NEW.project_id THEN 0 ELSE 1 END,
            -- Puis par niveau décroissant (plus précis d'abord)
            level DESC
        LIMIT 1;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION assign_quartier_to_demande IS 'Assigne automatiquement la zone la plus précise à une demande citoyenne';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 7. VUE RÉCURSIVE V_ZONES_HIERARCHY
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW v_zones_hierarchy AS
WITH RECURSIVE zone_tree AS (
    -- Base: zones racines (sans parent)
    SELECT
        id,
        name,
        code,
        perimetre_type,
        parent_id,
        level,
        is_global,
        project_id,
        population,
        code_iris,
        code_insee,
        metadata,
        created_at,
        updated_at,
        name::text AS full_path,
        ARRAY[id] AS path_ids,
        0 AS depth
    FROM perimetres
    WHERE parent_id IS NULL

    UNION ALL

    -- Récursion: enfants
    SELECT
        p.id,
        p.name,
        p.code,
        p.perimetre_type,
        p.parent_id,
        p.level,
        p.is_global,
        p.project_id,
        p.population,
        p.code_iris,
        p.code_insee,
        p.metadata,
        p.created_at,
        p.updated_at,
        zt.full_path || ' > ' || p.name,
        zt.path_ids || p.id,
        zt.depth + 1
    FROM perimetres p
    JOIN zone_tree zt ON p.parent_id = zt.id
)
SELECT
    zt.*,
    parent.name AS parent_name
FROM zone_tree zt
LEFT JOIN perimetres parent ON zt.parent_id = parent.id
ORDER BY full_path;

COMMENT ON VIEW v_zones_hierarchy IS 'Vue hiérarchique des zones avec chemin complet et profondeur';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 8. FONCTION GET_ZONE_HIERARCHY_FOR_POINT
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION get_zone_hierarchy_for_point(
    point_geom GEOMETRY,
    p_project_id UUID DEFAULT NULL
)
RETURNS TABLE(
    zone_id UUID,
    zone_name VARCHAR(255),
    zone_level INTEGER,
    zone_type VARCHAR(50),
    zone_parent_id UUID
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE found_zone AS (
        -- Trouver la zone la plus précise contenant le point
        SELECT p.id, p.name, p.level, p.perimetre_type, p.parent_id
        FROM perimetres p
        WHERE ST_Contains(p.geom, point_geom)
          AND (
              p.project_id = p_project_id
              OR p.is_global = TRUE
              OR p.project_id IS NULL
          )
        ORDER BY
            CASE WHEN p.project_id = p_project_id THEN 0 ELSE 1 END,
            p.level DESC
        LIMIT 1
    ),
    hierarchy AS (
        -- Zone trouvée
        SELECT * FROM found_zone
        UNION ALL
        -- Remonter aux parents
        SELECT p.id, p.name, p.level, p.perimetre_type, p.parent_id
        FROM perimetres p
        JOIN hierarchy h ON p.id = h.parent_id
    )
    SELECT
        h.id AS zone_id,
        h.name AS zone_name,
        h.level AS zone_level,
        h.perimetre_type AS zone_type,
        h.parent_id AS zone_parent_id
    FROM hierarchy h
    ORDER BY h.level ASC;  -- Du plus haut (commune) au plus bas (secteur)
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_zone_hierarchy_for_point IS 'Retourne la hiérarchie complète des zones contenant un point';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 9. VUE V_STATS_DEMANDES_PAR_ZONE
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW v_stats_demandes_par_zone AS
SELECT
    p.id AS zone_id,
    p.name AS zone_name,
    p.level,
    p.perimetre_type,
    p.parent_id,
    parent.name AS parent_name,
    p.project_id,
    p.is_global,
    p.population,
    -- Statistiques directes (demandes assignées à cette zone)
    COUNT(d.id) AS total_demandes,
    COUNT(d.id) FILTER (WHERE d.statut = 'nouveau') AS nouvelles,
    COUNT(d.id) FILTER (WHERE d.statut = 'accepte') AS acceptees,
    COUNT(d.id) FILTER (WHERE d.statut IN ('en_cours', 'planifie')) AS en_cours,
    COUNT(d.id) FILTER (WHERE d.statut = 'traite') AS traitees,
    COUNT(d.id) FILTER (WHERE d.statut = 'rejete') AS rejetees,
    -- Temps moyen de résolution (en heures)
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (COALESCE(d.date_resolution, CURRENT_TIMESTAMP) - d.created_at)) / 3600
        ) FILTER (WHERE d.date_resolution IS NOT NULL)::numeric,
        1
    ) AS temps_moyen_heures
FROM perimetres p
LEFT JOIN perimetres parent ON p.parent_id = parent.id
LEFT JOIN demandes_citoyens d ON d.quartier_id = p.id
GROUP BY p.id, p.name, p.level, p.perimetre_type, p.parent_id, parent.name,
         p.project_id, p.is_global, p.population;

COMMENT ON VIEW v_stats_demandes_par_zone IS 'Statistiques des demandes par zone géographique';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 10. FONCTION POUR RÉCUPÉRER LES ENFANTS D'UNE ZONE
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION get_zone_children(
    p_zone_id UUID,
    p_recursive BOOLEAN DEFAULT FALSE
)
RETURNS TABLE(
    zone_id UUID,
    zone_name VARCHAR(255),
    zone_level INTEGER,
    zone_type VARCHAR(50),
    zone_parent_id UUID,
    depth INTEGER
) AS $$
BEGIN
    IF p_recursive THEN
        -- Récupérer tous les descendants
        RETURN QUERY
        WITH RECURSIVE children AS (
            SELECT p.id, p.name, p.level, p.perimetre_type, p.parent_id, 1 AS depth
            FROM perimetres p
            WHERE p.parent_id = p_zone_id

            UNION ALL

            SELECT p.id, p.name, p.level, p.perimetre_type, p.parent_id, c.depth + 1
            FROM perimetres p
            JOIN children c ON p.parent_id = c.id
        )
        SELECT c.id, c.name, c.level, c.perimetre_type, c.parent_id, c.depth
        FROM children c
        ORDER BY c.depth, c.name;
    ELSE
        -- Enfants directs seulement
        RETURN QUERY
        SELECT p.id, p.name, p.level, p.perimetre_type, p.parent_id, 1 AS depth
        FROM perimetres p
        WHERE p.parent_id = p_zone_id
        ORDER BY p.name;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_zone_children IS 'Récupère les zones enfants (directes ou récursives)';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 11. SUPPRIMER LA TABLE ZONES (PLUS UTILISÉE)
-- ═══════════════════════════════════════════════════════════════════════════════

-- Supprimer les objets dépendants d'abord
DROP TRIGGER IF EXISTS staging_detect_zone ON geoclic_staging;

-- Recréer le trigger detect_zone avec la nouvelle fonction (qui utilise perimetres)
-- Note: detect_zone_trigger() utilise get_zone_for_point() qui a été modifiée
CREATE TRIGGER staging_detect_zone
    BEFORE INSERT OR UPDATE ON geoclic_staging
    FOR EACH ROW
    EXECUTE FUNCTION detect_zone_trigger();

-- Supprimer la table zones
DROP TABLE IF EXISTS zones CASCADE;

-- Note: Table zones supprimée - utiliser perimetres à la place

-- ═══════════════════════════════════════════════════════════════════════════════
-- 12. METTRE À JOUR LES COMMENTAIRES
-- ═══════════════════════════════════════════════════════════════════════════════

COMMENT ON TABLE perimetres IS 'Zones géographiques hiérarchiques (Commune > Quartier > Secteur). Remplace l''ancienne table zones.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- RÉSUMÉ DES CHANGEMENTS
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- Nouvelles colonnes sur perimetres:
--   - parent_id: référence vers la zone parente
--   - level: 1=Commune, 2=Quartier, 3=Secteur
--   - is_global: TRUE pour zones partagées par tous les projets
--
-- Nouvelles vues:
--   - v_zones_hierarchy: arbre complet avec chemin
--   - v_stats_demandes_par_zone: statistiques par zone
--
-- Nouvelles fonctions:
--   - get_zone_hierarchy_for_point(): hiérarchie pour un point GPS
--   - get_zone_children(): enfants d'une zone
--
-- Fonctions modifiées:
--   - get_zone_for_point(): utilise perimetres
--   - assign_quartier_to_demande(): supporte is_global et level
--
-- Table supprimée:
--   - zones (remplacée par perimetres)
--
-- ═══════════════════════════════════════════════════════════════════════════════

COMMIT;

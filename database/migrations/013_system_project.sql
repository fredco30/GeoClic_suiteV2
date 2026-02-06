-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 013: Projet Système pour Demandes Citoyens
-- GéoClic Suite - Sécurisation des données
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. AJOUTER LA COLONNE is_system À LA TABLE PROJECTS
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_system BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN projects.is_system IS 'Projet système non modifiable/supprimable';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. CRÉER LE PROJET SYSTÈME POUR LES DEMANDES CITOYENS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Créer le projet système s'il n'existe pas
INSERT INTO projects (
    name,
    description,
    status,
    is_active,
    is_system,
    collectivite_name
)
SELECT
    'Signalements Citoyens',
    'Projet système pour la gestion des demandes citoyennes. Ce projet ne peut pas être supprimé.',
    'En cours',
    TRUE,
    TRUE,
    NULL
WHERE NOT EXISTS (
    SELECT 1 FROM projects WHERE is_system = TRUE
);

-- Si un projet existe déjà avec des catégories de demandes, le marquer comme système
UPDATE projects p
SET is_system = TRUE,
    name = CASE
        WHEN name = 'Projet Démo V12 Pro' THEN 'Signalements Citoyens'
        ELSE name
    END,
    description = COALESCE(description, 'Projet système pour la gestion des demandes citoyennes.')
WHERE p.id IN (
    SELECT DISTINCT project_id FROM demandes_categories
)
AND p.is_system IS NOT TRUE;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. TRIGGER POUR EMPÊCHER LA SUPPRESSION DES PROJETS SYSTÈME
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION prevent_system_project_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_system = TRUE THEN
        RAISE EXCEPTION 'Impossible de supprimer un projet système. Ce projet contient des données critiques.';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_system_project_delete ON projects;
CREATE TRIGGER trg_prevent_system_project_delete
    BEFORE DELETE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION prevent_system_project_delete();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. TRIGGER POUR EMPÊCHER LA MODIFICATION DES CHAMPS CRITIQUES DES PROJETS SYSTÈME
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION prevent_system_project_critical_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_system = TRUE THEN
        -- Empêcher de désactiver un projet système
        IF NEW.is_active = FALSE THEN
            RAISE EXCEPTION 'Impossible de désactiver un projet système.';
        END IF;

        -- Empêcher de retirer le flag is_system
        IF NEW.is_system = FALSE OR NEW.is_system IS NULL THEN
            RAISE EXCEPTION 'Impossible de retirer le statut système d''un projet.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_system_project_critical_update ON projects;
CREATE TRIGGER trg_prevent_system_project_critical_update
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION prevent_system_project_critical_update();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. FONCTION POUR OBTENIR LE PROJET SYSTÈME
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION get_system_project_id()
RETURNS UUID AS $$
DECLARE
    v_project_id UUID;
BEGIN
    SELECT id INTO v_project_id
    FROM projects
    WHERE is_system = TRUE
    LIMIT 1;

    RETURN v_project_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_system_project_id IS 'Retourne l''ID du projet système pour les demandes citoyennes';

-- ═══════════════════════════════════════════════════════════════════════════════
-- FIN DE LA MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════════

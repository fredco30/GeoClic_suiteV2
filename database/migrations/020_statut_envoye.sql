-- Migration 020: Ajout du statut 'envoye' dans le workflow des demandes
-- Quand une demande est assignée à un service (auto ou manuellement),
-- le statut passe à 'envoye' (transmis au service compétent).

-- 1. Modifier le trigger auto-assign pour aussi changer le statut en 'envoye'
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

        -- Assigner si trouvé et passer en 'envoye'
        IF v_service_id IS NOT NULL THEN
            NEW.service_assigne_id := v_service_id;
            NEW.statut := 'envoye';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Mettre à jour la vue stats par service pour inclure 'envoye' dans 'a_traiter'
DROP VIEW IF EXISTS v_stats_par_service;
CREATE VIEW v_stats_par_service AS
SELECT
    s.id AS service_id,
    s.nom AS service_nom,
    COUNT(d.id) AS total,
    COUNT(d.id) FILTER (WHERE d.statut IN ('nouveau', 'en_moderation', 'accepte', 'envoye')) AS a_traiter,
    COUNT(d.id) FILTER (WHERE d.statut IN ('en_cours', 'planifie')) AS en_cours,
    COUNT(d.id) FILTER (WHERE d.statut = 'traite') AS traitees,
    COUNT(d.id) FILTER (WHERE d.statut IN ('cloture', 'rejete')) AS cloturees
FROM demandes_services s
LEFT JOIN demandes_citoyens d ON d.service_assigne_id = s.id
GROUP BY s.id, s.nom;

-- 3. Passer les demandes existantes qui ont un service assigné mais sont encore en 'nouveau' ou 'en_moderation' vers 'envoye'
UPDATE demandes_citoyens
SET statut = 'envoye'
WHERE service_assigne_id IS NOT NULL
  AND statut IN ('nouveau', 'en_moderation')
  AND est_doublon IS NOT TRUE;

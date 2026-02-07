-- ============================================================================
-- GéoClic Suite - Données de démonstration
-- ============================================================================
-- Ce script crée des données fictives réalistes pour démontrer la plateforme.
-- À exécuter APRÈS toutes les migrations.
-- Usage: psql -U geoclic -d geoclic_db < demo_data.sql
-- ============================================================================

-- ============================================================================
-- 1. SUPER ADMIN (compte de démonstration)
-- ============================================================================
-- Mot de passe: demo2026!
INSERT INTO geoclic_users (id, email, nom, prenom, actif, is_super_admin, role_data, role_demandes, role_sig, role_terrain, password_hash)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'admin@demo.geoclic.fr',
    'Martin',
    'Sophie',
    TRUE,
    TRUE,
    'admin',
    'admin',
    'edition',
    'agent',
    '$2b$12$LJ3m5E5JQKyU5U5VXc1Y8OGV9Z5m4dC4n1P2w8vP1cJgF1Xz2zKRe'
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- 2. BRANDING (personnalisation démo)
-- ============================================================================
INSERT INTO system_settings (key, value) VALUES
    ('nom_collectivite', '"Mairie de Démonstration"'),
    ('primary_color', '"#1565C0"'),
    ('secondary_color', '"#37474F"'),
    ('accent_color', '"#FF6F00"'),
    ('contact_email', '"contact@demo.geoclic.fr"'),
    ('contact_telephone', '"01 23 45 67 89"')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- ============================================================================
-- 3. SERVICES MUNICIPAUX
-- ============================================================================
INSERT INTO demandes_services (id, nom, description, couleur, actif) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'Service Voirie', 'Entretien des routes et trottoirs', '#1565C0', TRUE),
    ('b0000000-0000-0000-0000-000000000002', 'Service Espaces Verts', 'Parcs, jardins et arbres', '#2E7D32', TRUE),
    ('b0000000-0000-0000-0000-000000000003', 'Service Propreté', 'Nettoyage et déchets', '#F57C00', TRUE),
    ('b0000000-0000-0000-0000-000000000004', 'Service Éclairage', 'Éclairage public', '#FBC02D', TRUE)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 4. AGENTS TERRAIN
-- ============================================================================
-- Agent 1 - Voirie (mot de passe: agent2026!)
INSERT INTO geoclic_users (id, email, nom, prenom, actif, is_super_admin, role_data, role_demandes, role_sig, role_terrain, service_id, password_hash)
VALUES (
    'a0000000-0000-0000-0000-000000000002',
    'voirie@demo.geoclic.fr',
    'Durand',
    'Pierre',
    TRUE, FALSE, 'aucun', 'agent', 'aucun', 'agent',
    'b0000000-0000-0000-0000-000000000001',
    '$2b$12$LJ3m5E5JQKyU5U5VXc1Y8OGV9Z5m4dC4n1P2w8vP1cJgF1Xz2zKRe'
) ON CONFLICT (email) DO NOTHING;

INSERT INTO demandes_services_agents (id, service_id, nom, prenom, email, telephone, actif)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    'Durand', 'Pierre', 'voirie@demo.geoclic.fr', '06 12 34 56 78', TRUE
) ON CONFLICT (email) DO NOTHING;

-- Agent 2 - Espaces Verts
INSERT INTO geoclic_users (id, email, nom, prenom, actif, is_super_admin, role_data, role_demandes, role_sig, role_terrain, service_id, password_hash)
VALUES (
    'a0000000-0000-0000-0000-000000000003',
    'espacesverts@demo.geoclic.fr',
    'Moreau',
    'Julie',
    TRUE, FALSE, 'aucun', 'agent', 'aucun', 'agent',
    'b0000000-0000-0000-0000-000000000002',
    '$2b$12$LJ3m5E5JQKyU5U5VXc1Y8OGV9Z5m4dC4n1P2w8vP1cJgF1Xz2zKRe'
) ON CONFLICT (email) DO NOTHING;

INSERT INTO demandes_services_agents (id, service_id, nom, prenom, email, telephone, actif)
VALUES (
    'c0000000-0000-0000-0000-000000000002',
    'b0000000-0000-0000-0000-000000000002',
    'Moreau', 'Julie', 'espacesverts@demo.geoclic.fr', '06 23 45 67 89', TRUE
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- 5. CATÉGORIES DE SIGNALEMENTS
-- ============================================================================
-- Récupérer le projet système
DO $$
DECLARE
    sys_project_id UUID;
BEGIN
    SELECT id INTO sys_project_id FROM projects WHERE is_system = TRUE LIMIT 1;
    IF sys_project_id IS NULL THEN
        RAISE NOTICE 'Pas de projet système trouvé, catégories non créées';
        RETURN;
    END IF;

    -- Catégories parentes
    INSERT INTO demandes_categories (id, nom, icone, couleur, parent_id, ordre, actif, project_id)
    VALUES
        ('d0000000-0000-0000-0000-000000000001', 'Voirie', 'road', -12345678, NULL, 1, TRUE, sys_project_id),
        ('d0000000-0000-0000-0000-000000000002', 'Espaces Verts', 'park', -14012437, NULL, 2, TRUE, sys_project_id),
        ('d0000000-0000-0000-0000-000000000003', 'Propreté', 'delete', -1146130, NULL, 3, TRUE, sys_project_id),
        ('d0000000-0000-0000-0000-000000000004', 'Éclairage', 'lightbulb', -27648, NULL, 4, TRUE, sys_project_id)
    ON CONFLICT (id) DO NOTHING;

    -- Sous-catégories Voirie
    INSERT INTO demandes_categories (id, nom, icone, couleur, parent_id, ordre, actif, project_id, service_assigne_id)
    VALUES
        ('d0000000-0000-0000-0000-000000000011', 'Nid-de-poule', 'warning', -12345678, 'd0000000-0000-0000-0000-000000000001', 1, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000001'),
        ('d0000000-0000-0000-0000-000000000012', 'Trottoir dégradé', 'construction', -12345678, 'd0000000-0000-0000-0000-000000000001', 2, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000001'),
        ('d0000000-0000-0000-0000-000000000013', 'Signalisation', 'traffic', -12345678, 'd0000000-0000-0000-0000-000000000001', 3, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000001')
    ON CONFLICT (id) DO NOTHING;

    -- Sous-catégories Espaces Verts
    INSERT INTO demandes_categories (id, nom, icone, couleur, parent_id, ordre, actif, project_id, service_assigne_id)
    VALUES
        ('d0000000-0000-0000-0000-000000000021', 'Arbre dangereux', 'nature', -14012437, 'd0000000-0000-0000-0000-000000000002', 1, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000002'),
        ('d0000000-0000-0000-0000-000000000022', 'Pelouse abîmée', 'grass', -14012437, 'd0000000-0000-0000-0000-000000000002', 2, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000002'),
        ('d0000000-0000-0000-0000-000000000023', 'Jeux enfants', 'child_friendly_zone', -14012437, 'd0000000-0000-0000-0000-000000000002', 3, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000002')
    ON CONFLICT (id) DO NOTHING;

    -- Sous-catégories Propreté
    INSERT INTO demandes_categories (id, nom, icone, couleur, parent_id, ordre, actif, project_id, service_assigne_id)
    VALUES
        ('d0000000-0000-0000-0000-000000000031', 'Dépôt sauvage', 'delete_sweep', -1146130, 'd0000000-0000-0000-0000-000000000003', 1, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000003'),
        ('d0000000-0000-0000-0000-000000000032', 'Poubelle pleine', 'delete', -1146130, 'd0000000-0000-0000-0000-000000000003', 2, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000003'),
        ('d0000000-0000-0000-0000-000000000033', 'Tag / Graffiti', 'format_paint', -1146130, 'd0000000-0000-0000-0000-000000000003', 3, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000003')
    ON CONFLICT (id) DO NOTHING;

    -- Sous-catégories Éclairage
    INSERT INTO demandes_categories (id, nom, icone, couleur, parent_id, ordre, actif, project_id, service_assigne_id)
    VALUES
        ('d0000000-0000-0000-0000-000000000041', 'Lampadaire en panne', 'lightbulb', -27648, 'd0000000-0000-0000-0000-000000000004', 1, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000004'),
        ('d0000000-0000-0000-0000-000000000042', 'Éclairage insuffisant', 'brightness_low', -27648, 'd0000000-0000-0000-0000-000000000004', 2, TRUE, sys_project_id, 'b0000000-0000-0000-0000-000000000004')
    ON CONFLICT (id) DO NOTHING;
END $$;

-- ============================================================================
-- 6. DEMANDES CITOYENS (signalements de démonstration)
-- ============================================================================
-- Coordonnées GPS autour de Montpellier (exemple)

INSERT INTO demandes_citoyens (id, numero_suivi, description, latitude, longitude, adresse, statut, priorite, categorie_id, service_assigne_id, email_citoyen, created_at)
VALUES
    ('e0000000-0000-0000-0000-000000000001', 'SIG-2026-0001', 'Grand nid-de-poule boulevard Gambetta, dangereux pour les vélos', 43.6108, 3.8767, '45 Boulevard Gambetta', 'nouveau', 'urgente', 'd0000000-0000-0000-0000-000000000011', 'b0000000-0000-0000-0000-000000000001', 'citoyen1@example.fr', NOW() - INTERVAL '3 days'),
    ('e0000000-0000-0000-0000-000000000002', 'SIG-2026-0002', 'Trottoir cassé devant l''école Jules Ferry, chute d''un enfant la semaine dernière', 43.6045, 3.8820, '12 Rue de l''École', 'en_cours', 'urgente', 'd0000000-0000-0000-0000-000000000012', 'b0000000-0000-0000-0000-000000000001', 'citoyen2@example.fr', NOW() - INTERVAL '7 days'),
    ('e0000000-0000-0000-0000-000000000003', 'SIG-2026-0003', 'Arbre penché au parc Méric, risque de chute avec le prochain épisode de vent', 43.6320, 3.8650, 'Parc de Méric', 'planifie', 'haute', 'd0000000-0000-0000-0000-000000000021', 'b0000000-0000-0000-0000-000000000002', 'citoyen3@example.fr', NOW() - INTERVAL '10 days'),
    ('e0000000-0000-0000-0000-000000000004', 'SIG-2026-0004', 'Dépôt sauvage de gravats et meubles au bout de la rue des Lilas', 43.6200, 3.8550, '89 Rue des Lilas', 'envoye', 'normale', 'd0000000-0000-0000-0000-000000000031', 'b0000000-0000-0000-0000-000000000003', 'citoyen4@example.fr', NOW() - INTERVAL '2 days'),
    ('e0000000-0000-0000-0000-000000000005', 'SIG-2026-0005', 'Lampadaire éteint depuis 2 semaines, zone très sombre le soir', 43.6150, 3.8900, '7 Avenue de Toulouse', 'nouveau', 'haute', 'd0000000-0000-0000-0000-000000000041', 'b0000000-0000-0000-0000-000000000004', NULL, NOW() - INTERVAL '1 day'),
    ('e0000000-0000-0000-0000-000000000006', 'SIG-2026-0006', 'Tag obscène sur le mur de la médiathèque', 43.6080, 3.8780, '3 Place de la Comédie', 'en_cours', 'normale', 'd0000000-0000-0000-0000-000000000033', 'b0000000-0000-0000-0000-000000000003', 'citoyen6@example.fr', NOW() - INTERVAL '5 days'),
    ('e0000000-0000-0000-0000-000000000007', 'SIG-2026-0007', 'Panneau stop arraché au carrefour, très dangereux', 43.6095, 3.8830, 'Carrefour Rue de la Loge', 'traite', 'urgente', 'd0000000-0000-0000-0000-000000000013', 'b0000000-0000-0000-0000-000000000001', 'citoyen7@example.fr', NOW() - INTERVAL '15 days'),
    ('e0000000-0000-0000-0000-000000000008', 'SIG-2026-0008', 'Pelouse du square complètement piétinée après la foire', 43.6180, 3.8700, 'Square Planchon', 'nouveau', 'basse', 'd0000000-0000-0000-0000-000000000022', 'b0000000-0000-0000-0000-000000000002', NULL, NOW() - INTERVAL '12 hours'),
    ('e0000000-0000-0000-0000-000000000009', 'SIG-2026-0009', 'Poubelles débordent tous les vendredis soir place Jean Jaurès', 43.6070, 3.8810, 'Place Jean Jaurès', 'envoye', 'normale', 'd0000000-0000-0000-0000-000000000032', 'b0000000-0000-0000-0000-000000000003', 'citoyen9@example.fr', NOW() - INTERVAL '4 days'),
    ('e0000000-0000-0000-0000-000000000010', 'SIG-2026-0010', 'Jeu pour enfants cassé (toboggan fendu), risque de blessure', 43.6250, 3.8680, 'Parc Montcalm', 'en_cours', 'urgente', 'd0000000-0000-0000-0000-000000000023', 'b0000000-0000-0000-0000-000000000002', 'citoyen10@example.fr', NOW() - INTERVAL '6 days'),
    ('e0000000-0000-0000-0000-000000000011', 'SIG-2026-0011', 'Nid-de-poule rue Foch, creusé par les travaux récents', 43.6100, 3.8750, '22 Rue Foch', 'nouveau', 'normale', 'd0000000-0000-0000-0000-000000000011', 'b0000000-0000-0000-0000-000000000001', 'citoyen11@example.fr', NOW() - INTERVAL '6 hours'),
    ('e0000000-0000-0000-0000-000000000012', 'SIG-2026-0012', 'Éclairage clignotant en permanence avenue de la Mer', 43.6130, 3.8850, '15 Avenue de la Mer', 'nouveau', 'basse', 'd0000000-0000-0000-0000-000000000042', 'b0000000-0000-0000-0000-000000000004', NULL, NOW() - INTERVAL '2 hours')
ON CONFLICT (id) DO NOTHING;

-- Assigner quelques demandes à des agents
UPDATE demandes_citoyens SET agent_service_id = 'c0000000-0000-0000-0000-000000000001'
WHERE id IN ('e0000000-0000-0000-0000-000000000002', 'e0000000-0000-0000-0000-000000000007');

UPDATE demandes_citoyens SET agent_service_id = 'c0000000-0000-0000-0000-000000000002'
WHERE id IN ('e0000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000010');

-- Ajouter les dates de traitement pour les demandes traitées
UPDATE demandes_citoyens SET
    date_prise_en_charge = created_at + INTERVAL '1 day',
    date_resolution = created_at + INTERVAL '3 days'
WHERE statut = 'traite';

UPDATE demandes_citoyens SET
    date_prise_en_charge = created_at + INTERVAL '1 day'
WHERE statut IN ('en_cours', 'planifie');

UPDATE demandes_citoyens SET
    date_planification = NOW() + INTERVAL '2 days'
WHERE statut = 'planifie';

-- ============================================================================
-- RÉSUMÉ
-- ============================================================================
-- Comptes de démonstration:
--   Admin:  admin@demo.geoclic.fr / demo2026!
--   Agent:  voirie@demo.geoclic.fr / demo2026!
--   Agent:  espacesverts@demo.geoclic.fr / demo2026!
--
-- Données créées:
--   4 services municipaux
--   4 catégories + 11 sous-catégories
--   12 signalements citoyens (répartis sur différents statuts et priorités)
--   Coordonnées GPS autour de Montpellier
-- ============================================================================

SELECT 'Données de démonstration chargées avec succès !' AS resultat;
SELECT COUNT(*) || ' demandes de démo créées' AS demandes FROM demandes_citoyens WHERE numero_suivi LIKE 'SIG-2026-%';
SELECT COUNT(*) || ' services créés' AS services FROM demandes_services;
SELECT COUNT(*) || ' agents terrain créés' AS agents FROM demandes_services_agents;

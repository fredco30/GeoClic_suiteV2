-- Migration 017: Synchroniser les agents de demandes_services_agents vers geoclic_users
-- Cela permet aux agents créés dans geoclic_demandes d'accéder à geoclic_services

-- Insérer les agents existants dans geoclic_users s'ils n'existent pas déjà
INSERT INTO geoclic_users (
    email, password_hash, nom, prenom, actif,
    is_super_admin, role_data, role_demandes, role_sig, role_terrain,
    service_id
)
SELECT
    a.email,
    a.password_hash,
    a.nom,
    a.prenom,
    a.actif,
    FALSE,  -- is_super_admin
    'aucun',  -- role_data
    CASE WHEN a.role = 'responsable' THEN 'admin' ELSE 'agent' END,  -- role_demandes
    'aucun',  -- role_sig
    'agent',  -- role_terrain - tous les agents services ont accès terrain
    a.service_id
FROM demandes_services_agents a
WHERE NOT EXISTS (
    SELECT 1 FROM geoclic_users u WHERE u.email = a.email
);

-- Afficher les résultats
DO $$
DECLARE
    inserted_count INT;
BEGIN
    GET DIAGNOSTICS inserted_count = ROW_COUNT;
    RAISE NOTICE 'Agents migrés vers geoclic_users: %', inserted_count;
END $$;

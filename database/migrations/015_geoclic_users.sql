-- Migration 015: Système d'authentification unifié
-- Crée la table geoclic_users pour gérer tous les utilisateurs de la suite GéoClic

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLE PRINCIPALE
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS geoclic_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    actif BOOLEAN DEFAULT TRUE,

    -- Super admin (peut tout faire, peut créer d'autres admins)
    is_super_admin BOOLEAN DEFAULT FALSE,

    -- Rôles par application
    -- role_data: accès à GéoClic Data (admin backoffice)
    role_data VARCHAR(20) DEFAULT 'aucun' CHECK (role_data IN ('aucun', 'admin')),

    -- role_demandes: accès à GéoClic Demandes (gestion signalements)
    role_demandes VARCHAR(20) DEFAULT 'aucun' CHECK (role_demandes IN ('aucun', 'agent', 'admin')),

    -- role_sig: accès à GéoClic SIG (cartographie)
    role_sig VARCHAR(20) DEFAULT 'aucun' CHECK (role_sig IN ('aucun', 'lecture', 'edition')),

    -- role_terrain: accès à GéoClic Terrain (app mobile agents)
    role_terrain VARCHAR(20) DEFAULT 'aucun' CHECK (role_terrain IN ('aucun', 'agent')),

    -- Pour agents terrain: service assigné
    service_id UUID REFERENCES demandes_services(id) ON DELETE SET NULL,

    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Index pour les recherches fréquentes
CREATE INDEX IF NOT EXISTS idx_geoclic_users_email ON geoclic_users(email);
CREATE INDEX IF NOT EXISTS idx_geoclic_users_service ON geoclic_users(service_id) WHERE service_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_geoclic_users_actif ON geoclic_users(actif) WHERE actif = TRUE;

-- ═══════════════════════════════════════════════════════════════════════════════
-- MIGRATION DES AGENTS TERRAIN EXISTANTS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Migrer les agents existants vers la nouvelle table
INSERT INTO geoclic_users (
    email,
    password_hash,
    nom,
    prenom,
    actif,
    role_terrain,
    service_id,
    created_at
)
SELECT
    email,
    password_hash,
    nom,
    prenom,
    actif,
    'agent',
    service_id,
    COALESCE(created_at, CURRENT_TIMESTAMP)
FROM demandes_services_agents
WHERE email IS NOT NULL
  AND password_hash IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM geoclic_users WHERE geoclic_users.email = demandes_services_agents.email
  );

-- ═══════════════════════════════════════════════════════════════════════════════
-- SUPER ADMIN INITIAL
-- ═══════════════════════════════════════════════════════════════════════════════

-- Hash bcrypt pour 'admin123' (coût 12)
-- IMPORTANT: Changer ce mot de passe en production avec la fonction update_user_password()
INSERT INTO geoclic_users (
    email,
    password_hash,
    nom,
    prenom,
    is_super_admin,
    role_data,
    role_demandes,
    role_sig,
    role_terrain
)
VALUES (
    'admin@geoclic.local',
    '$2b$12$rNCLYdLTTdlEzZOyqMKLaeHGWqCDRzWqfWzpXd.YyZnTq9B0qHXPK',
    'Administrateur',
    'GéoClic',
    TRUE,
    'admin',
    'admin',
    'edition',
    'agent'
)
ON CONFLICT (email) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════════════
-- FONCTIONS UTILITAIRES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Fonction pour mettre à jour le mot de passe d'un utilisateur
-- Usage: SELECT update_user_password('admin@geoclic.local', 'nouveau_hash_bcrypt');
CREATE OR REPLACE FUNCTION update_user_password(user_email VARCHAR, new_password_hash VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE geoclic_users
    SET password_hash = new_password_hash,
        updated_at = CURRENT_TIMESTAMP
    WHERE email = user_email;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour créer un nouveau super admin (remplace l'existant)
-- Usage: SELECT create_super_admin('nouveau@email.fr', 'hash_bcrypt', 'Nom', 'Prénom');
CREATE OR REPLACE FUNCTION create_super_admin(
    admin_email VARCHAR,
    admin_password_hash VARCHAR,
    admin_nom VARCHAR,
    admin_prenom VARCHAR
)
RETURNS UUID AS $$
DECLARE
    new_id UUID;
BEGIN
    -- Retirer le statut super_admin des autres utilisateurs
    UPDATE geoclic_users SET is_super_admin = FALSE WHERE is_super_admin = TRUE;

    -- Créer ou mettre à jour le super admin
    INSERT INTO geoclic_users (
        email, password_hash, nom, prenom,
        is_super_admin, role_data, role_demandes, role_sig, role_terrain
    )
    VALUES (
        admin_email, admin_password_hash, admin_nom, admin_prenom,
        TRUE, 'admin', 'admin', 'edition', 'agent'
    )
    ON CONFLICT (email) DO UPDATE SET
        password_hash = EXCLUDED.password_hash,
        nom = EXCLUDED.nom,
        prenom = EXCLUDED.prenom,
        is_super_admin = TRUE,
        role_data = 'admin',
        role_demandes = 'admin',
        role_sig = 'edition',
        role_terrain = 'agent',
        updated_at = CURRENT_TIMESTAMP
    RETURNING id INTO new_id;

    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════════
-- TRIGGER UPDATED_AT
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION update_geoclic_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_geoclic_users_updated_at ON geoclic_users;
CREATE TRIGGER trg_geoclic_users_updated_at
    BEFORE UPDATE ON geoclic_users
    FOR EACH ROW
    EXECUTE FUNCTION update_geoclic_users_updated_at();

-- ═══════════════════════════════════════════════════════════════════════════════
-- VUE POUR LISTER LES UTILISATEURS AVEC LEURS ACCÈS
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW v_users_summary AS
SELECT
    u.id,
    u.email,
    u.nom,
    u.prenom,
    u.actif,
    u.is_super_admin,
    u.role_data,
    u.role_demandes,
    u.role_sig,
    u.role_terrain,
    s.nom AS service_nom,
    u.last_login,
    u.created_at,
    -- Résumé des accès
    ARRAY_REMOVE(ARRAY[
        CASE WHEN u.role_data != 'aucun' THEN 'Data' END,
        CASE WHEN u.role_demandes != 'aucun' THEN 'Demandes' END,
        CASE WHEN u.role_sig != 'aucun' THEN 'SIG' END,
        CASE WHEN u.role_terrain != 'aucun' THEN 'Terrain' END
    ], NULL) AS apps_accessibles
FROM geoclic_users u
LEFT JOIN demandes_services s ON u.service_id = s.id
ORDER BY u.is_super_admin DESC, u.nom, u.prenom;

-- ═══════════════════════════════════════════════════════════════════════════════
-- COMMENTAIRES
-- ═══════════════════════════════════════════════════════════════════════════════

COMMENT ON TABLE geoclic_users IS 'Table unifiée des utilisateurs GéoClic Suite';
COMMENT ON COLUMN geoclic_users.is_super_admin IS 'Super administrateur avec tous les droits';
COMMENT ON COLUMN geoclic_users.role_data IS 'Accès GéoClic Data: aucun, admin';
COMMENT ON COLUMN geoclic_users.role_demandes IS 'Accès GéoClic Demandes: aucun, agent, admin';
COMMENT ON COLUMN geoclic_users.role_sig IS 'Accès GéoClic SIG: aucun, lecture, edition';
COMMENT ON COLUMN geoclic_users.role_terrain IS 'Accès GéoClic Terrain: aucun, agent';
COMMENT ON FUNCTION update_user_password IS 'Met à jour le mot de passe (hash bcrypt)';
COMMENT ON FUNCTION create_super_admin IS 'Crée un nouveau super admin (remplace existant)';

-- ═══════════════════════════════════════════════════════════════════════════════
-- NOTE: Pour remplacer le super admin en production:
--
-- 1. Générer un hash bcrypt pour le nouveau mot de passe:
--    python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('MOT_DE_PASSE'))"
--
-- 2. Appeler la fonction:
--    SELECT create_super_admin('email@collectivite.fr', '$2b$12$...hash...', 'Nom', 'Prénom');
-- ═══════════════════════════════════════════════════════════════════════════════

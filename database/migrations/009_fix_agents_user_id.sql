-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 009: Fix agents table for GeoClic Services authentication
-- Permet aux agents d'avoir leur propre authentification sans user_id obligatoire
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1. Rendre user_id nullable (pour les agents avec auth propre)
ALTER TABLE demandes_services_agents
ALTER COLUMN user_id DROP NOT NULL;

-- 2. Renommer la colonne avec cédille pour éviter les problèmes d'encodage
-- D'abord vérifier si la colonne existe avec cédille
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'demandes_services_agents'
        AND column_name = 'reçoit_notifications'
    ) THEN
        ALTER TABLE demandes_services_agents
        RENAME COLUMN "reçoit_notifications" TO recoit_notifications;
    END IF;
END $$;

-- 3. S'assurer que la colonne existe (sans cédille)
ALTER TABLE demandes_services_agents
ADD COLUMN IF NOT EXISTS recoit_notifications BOOLEAN DEFAULT TRUE;

-- 4. Supprimer la contrainte UNIQUE sur service_id, user_id (car user_id peut être null)
ALTER TABLE demandes_services_agents
DROP CONSTRAINT IF EXISTS demandes_services_agents_service_id_user_id_key;

-- 5. Ajouter contrainte UNIQUE sur service_id, email à la place
-- (un agent ne peut avoir qu'un compte par service)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'demandes_services_agents_service_email_key'
    ) THEN
        ALTER TABLE demandes_services_agents
        ADD CONSTRAINT demandes_services_agents_service_email_key
        UNIQUE (service_id, email);
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- Ignore si la contrainte existe déjà sous un autre nom
    NULL;
END $$;

COMMENT ON COLUMN demandes_services_agents.user_id IS 'Lien optionnel vers users (NULL pour auth autonome GeoClic Services)';
COMMENT ON COLUMN demandes_services_agents.email IS 'Email de connexion GeoClic Services (unique par service)';

-- Migration 016: Fix demandes_historique foreign key constraint
-- Le champ agent_id référençait l'ancienne table "users" mais les utilisateurs sont maintenant dans "geoclic_users"

-- Supprimer l'ancienne contrainte FK si elle existe
ALTER TABLE demandes_historique DROP CONSTRAINT IF EXISTS demandes_historique_agent_id_fkey;

-- Ajouter la nouvelle contrainte FK vers geoclic_users
-- On utilise ON DELETE SET NULL pour ne pas perdre l'historique si un utilisateur est supprimé
ALTER TABLE demandes_historique
ADD CONSTRAINT demandes_historique_agent_id_fkey
FOREIGN KEY (agent_id) REFERENCES geoclic_users(id) ON DELETE SET NULL;

-- Mettre à jour les agent_id existants qui ne sont pas dans geoclic_users (les mettre à NULL)
UPDATE demandes_historique h
SET agent_id = NULL
WHERE agent_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM geoclic_users u WHERE u.id = h.agent_id);

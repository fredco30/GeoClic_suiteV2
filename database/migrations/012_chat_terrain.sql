-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 012: Chat terrain séparé
-- Ajoute un canal pour distinguer les messages back-office des messages terrain
-- ═══════════════════════════════════════════════════════════════════════════════

-- Ajouter la colonne canal aux messages existants
ALTER TABLE demandes_messages
ADD COLUMN IF NOT EXISTS canal VARCHAR(20) DEFAULT 'backoffice';

-- Mettre à jour les messages existants (tous sont backoffice par défaut)
UPDATE demandes_messages SET canal = 'backoffice' WHERE canal IS NULL;

-- Ajouter une contrainte pour valider les valeurs
ALTER TABLE demandes_messages
ADD CONSTRAINT check_canal CHECK (canal IN ('backoffice', 'terrain'));

-- Créer un index pour les requêtes par canal
CREATE INDEX IF NOT EXISTS idx_demandes_messages_canal
ON demandes_messages(demande_id, canal);

-- Commentaire
COMMENT ON COLUMN demandes_messages.canal IS 'Canal du message: backoffice (demandes↔services) ou terrain (services↔terrain PWA)';

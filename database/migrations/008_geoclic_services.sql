-- ═══════════════════════════════════════════════════════════════════════════════
-- Migration 008: GeoClic Services - Authentification et Tchat
-- GéoClic Suite V14 - Module Services Terrain
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. EXTENSION TABLE AGENTS AVEC AUTHENTIFICATION
-- ═══════════════════════════════════════════════════════════════════════════════

-- Ajouter colonnes pour authentification autonome des agents service
ALTER TABLE demandes_services_agents
ADD COLUMN IF NOT EXISTS email VARCHAR(255),
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS nom VARCHAR(100),
ADD COLUMN IF NOT EXISTS prenom VARCHAR(100),
ADD COLUMN IF NOT EXISTS telephone VARCHAR(20),
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS actif BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Index pour login (unique sur email non null)
CREATE UNIQUE INDEX IF NOT EXISTS idx_agents_email
ON demandes_services_agents(email)
WHERE email IS NOT NULL;

-- Index pour recherche agents actifs
CREATE INDEX IF NOT EXISTS idx_agents_actif
ON demandes_services_agents(actif);

COMMENT ON COLUMN demandes_services_agents.email IS 'Email de connexion pour GeoClic Services';
COMMENT ON COLUMN demandes_services_agents.password_hash IS 'Hash bcrypt du mot de passe';
COMMENT ON COLUMN demandes_services_agents.role IS 'responsable = gère les agents, agent = terrain';
COMMENT ON COLUMN demandes_services_agents.actif IS 'FALSE = compte désactivé';

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_agents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_agents_updated_at ON demandes_services_agents;
CREATE TRIGGER trg_agents_updated_at
    BEFORE UPDATE ON demandes_services_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_agents_updated_at();

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. TABLE MESSAGES TCHAT
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS demandes_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demande_id UUID NOT NULL REFERENCES demandes_citoyens(id) ON DELETE CASCADE,

    -- Expéditeur
    sender_type VARCHAR(20) NOT NULL,  -- 'service' ou 'demandes'
    sender_id UUID,                     -- agent service (demandes_services_agents.id) ou user demandes (users.id)
    sender_nom VARCHAR(100),            -- Nom affiché (dénormalisé pour perf)

    -- Contenu
    message TEXT NOT NULL,

    -- Suivi lecture
    lu_par_service BOOLEAN DEFAULT FALSE,
    lu_par_demandes BOOLEAN DEFAULT FALSE,

    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Contrainte sur sender_type
    CONSTRAINT chk_sender_type CHECK (sender_type IN ('service', 'demandes'))
);

CREATE INDEX idx_messages_demande ON demandes_messages(demande_id);
CREATE INDEX idx_messages_created ON demandes_messages(created_at DESC);
CREATE INDEX idx_messages_unread_service ON demandes_messages(demande_id) WHERE lu_par_service = FALSE;
CREATE INDEX idx_messages_unread_demandes ON demandes_messages(demande_id) WHERE lu_par_demandes = FALSE;

COMMENT ON TABLE demandes_messages IS 'Messages tchat entre service terrain et back-office demandes';
COMMENT ON COLUMN demandes_messages.sender_type IS 'service = agent terrain, demandes = agent back-office';
COMMENT ON COLUMN demandes_messages.lu_par_service IS 'TRUE si lu par un agent du service terrain';
COMMENT ON COLUMN demandes_messages.lu_par_demandes IS 'TRUE si lu par un agent du back-office demandes';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. FONCTIONS UTILITAIRES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Fonction pour compter les messages non lus par demande (côté service)
CREATE OR REPLACE FUNCTION get_unread_messages_count_service(p_service_id UUID)
RETURNS TABLE(demande_id UUID, unread_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT m.demande_id, COUNT(*) AS unread_count
    FROM demandes_messages m
    JOIN demandes_citoyens d ON d.id = m.demande_id
    WHERE d.service_assigne_id = p_service_id
      AND m.lu_par_service = FALSE
      AND m.sender_type = 'demandes'  -- Messages envoyés par demandes, non lus par service
    GROUP BY m.demande_id;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour compter les messages non lus par demande (côté demandes)
CREATE OR REPLACE FUNCTION get_unread_messages_count_demandes(p_project_id UUID)
RETURNS TABLE(demande_id UUID, unread_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT m.demande_id, COUNT(*) AS unread_count
    FROM demandes_messages m
    JOIN demandes_citoyens d ON d.id = m.demande_id
    WHERE d.project_id = p_project_id
      AND m.lu_par_demandes = FALSE
      AND m.sender_type = 'service'  -- Messages envoyés par service, non lus par demandes
    GROUP BY m.demande_id;
END;
$$ LANGUAGE plpgsql;

-- Marquer les messages comme lus (côté service)
CREATE OR REPLACE FUNCTION mark_messages_read_service(p_demande_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE demandes_messages
    SET lu_par_service = TRUE
    WHERE demande_id = p_demande_id
      AND lu_par_service = FALSE
      AND sender_type = 'demandes';

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Marquer les messages comme lus (côté demandes)
CREATE OR REPLACE FUNCTION mark_messages_read_demandes(p_demande_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE demandes_messages
    SET lu_par_demandes = TRUE
    WHERE demande_id = p_demande_id
      AND lu_par_demandes = FALSE
      AND sender_type = 'service';

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. VUE AGENTS AVEC INFORMATIONS SERVICE
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW v_agents_services AS
SELECT
    a.id,
    a.service_id,
    a.user_id,
    a.email,
    a.nom,
    a.prenom,
    COALESCE(a.nom || ' ' || a.prenom, u.name, a.email) AS nom_complet,
    a.telephone,
    a.role,
    a.peut_assigner,
    a.reçoit_notifications,
    a.actif,
    a.last_login,
    a.created_at,
    s.nom AS service_nom,
    s.code AS service_code,
    s.couleur AS service_couleur,
    s.project_id
FROM demandes_services_agents a
JOIN demandes_services s ON a.service_id = s.id
LEFT JOIN users u ON a.user_id = u.id;

COMMENT ON VIEW v_agents_services IS 'Vue enrichie des agents avec infos service';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. AJOUTER COLONNE AGENT TERRAIN SUR DEMANDES
-- ═══════════════════════════════════════════════════════════════════════════════

-- L'agent terrain (du service) qui traite la demande
ALTER TABLE demandes_citoyens
ADD COLUMN IF NOT EXISTS agent_service_id UUID REFERENCES demandes_services_agents(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_demandes_agent_service ON demandes_citoyens(agent_service_id);

COMMENT ON COLUMN demandes_citoyens.agent_service_id IS 'Agent du service terrain assigné à cette demande';

-- ═══════════════════════════════════════════════════════════════════════════════
-- FIN DE LA MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════════

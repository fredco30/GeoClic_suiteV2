-- Migration 011: Email notifications enhancement
-- Phase 3: Notifications par email

-- Table de log des emails envoyés (pour historique et debug)
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Destinataire
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),

    -- Contenu
    subject VARCHAR(500) NOT NULL,
    template_type VARCHAR(50) NOT NULL, -- 'creation', 'status_change', 'assignment', 'message', 'reminder'

    -- Référence
    demande_id UUID REFERENCES demandes_citoyens(id) ON DELETE SET NULL,

    -- Statut
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'sent', 'failed'
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,

    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les logs
CREATE INDEX IF NOT EXISTS idx_email_logs_demande ON email_logs(demande_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);
CREATE INDEX IF NOT EXISTS idx_email_logs_created ON email_logs(created_at DESC);

-- Ajouter colonne email aux agents si pas présente
ALTER TABLE demandes_services_agents
ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Table pour stocker les rappels planifiés
CREATE TABLE IF NOT EXISTS email_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demande_id UUID NOT NULL REFERENCES demandes_citoyens(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES demandes_services_agents(id) ON DELETE SET NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sent BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_email_reminders_scheduled ON email_reminders(scheduled_at) WHERE NOT sent;

COMMENT ON TABLE email_logs IS 'Historique des emails envoyés';
COMMENT ON TABLE email_reminders IS 'Rappels email planifiés pour interventions';

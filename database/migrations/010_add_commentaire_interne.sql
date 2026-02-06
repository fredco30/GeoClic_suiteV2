-- Migration 010: Ajouter colonne commentaire_interne pour GeoClic Services
-- Date: 2026-02-01

-- Colonne pour stocker les commentaires internes des agents terrain
ALTER TABLE demandes_citoyens
ADD COLUMN IF NOT EXISTS commentaire_interne TEXT;

COMMENT ON COLUMN demandes_citoyens.commentaire_interne IS 'Commentaires internes des agents terrain (non visibles par le citoyen)';

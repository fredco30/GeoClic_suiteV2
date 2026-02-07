#!/bin/bash
# ============================================================================
# GéoClic Suite - Reset des données de démonstration
# ============================================================================
# Ce script nettoie et recharge les données de démonstration.
# Usage: sudo /opt/geoclic/scripts/reset_demo.sh
# ============================================================================

set -e

DB_CONTAINER="geoclic_db"
DB_NAME="geoclic_db"
DB_USER="geoclic"
DEMO_SQL="/opt/geoclic/database/demo_data.sql"

echo "=== GéoClic - Reset données de démonstration ==="
echo ""

# Vérifier que le fichier SQL existe
if [ ! -f "$DEMO_SQL" ]; then
    echo "ERREUR: Fichier $DEMO_SQL non trouvé"
    exit 1
fi

# Vérifier que le conteneur DB tourne
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    echo "ERREUR: Le conteneur $DB_CONTAINER n'est pas en cours d'exécution"
    exit 1
fi

echo "1. Nettoyage des anciennes données de démonstration..."
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<'SQL'
-- Supprimer les demandes de démo
DELETE FROM demandes_citoyens WHERE id LIKE 'e0000000-0000-0000-0000-%';
-- Supprimer les catégories de démo
DELETE FROM demandes_categories WHERE id LIKE 'd0000000-0000-0000-0000-%';
-- Supprimer les agents de démo
DELETE FROM demandes_services_agents WHERE id LIKE 'c0000000-0000-0000-0000-%';
-- Supprimer les services de démo
DELETE FROM demandes_services WHERE id LIKE 'b0000000-0000-0000-0000-%';
-- Supprimer les utilisateurs de démo
DELETE FROM geoclic_users WHERE id LIKE 'a0000000-0000-0000-0000-%';
-- Supprimer les messages de contact de démo
DELETE FROM contact_messages WHERE email LIKE '%@demo.geoclic.fr';
SQL

echo "2. Chargement des données de démonstration..."
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$DEMO_SQL"

echo ""
echo "=== Données de démonstration rechargées avec succès ! ==="
echo ""
echo "Comptes de démonstration :"
echo "  Admin:  admin@demo.geoclic.fr / demo2026!"
echo "  Agent:  voirie@demo.geoclic.fr / demo2026!"
echo "  Agent:  espacesverts@demo.geoclic.fr / demo2026!"

#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# GéoClic Suite - Script de restauration de la base de données
# ═══════════════════════════════════════════════════════════════════════════════
# Usage: sudo /opt/geoclic/scripts/restore_db.sh [fichier_backup.sql.gz]
#
# ATTENTION: Ce script écrase toutes les données actuelles!
# Utilisez-le uniquement en cas de problème grave.

# Configuration
BACKUP_DIR="/opt/geoclic/backups"
DB_CONTAINER="geoclic_db"
DB_NAME="geoclic_db"
DB_USER="geoclic"

# Vérifier les arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <fichier_backup.sql.gz>"
    echo ""
    echo "Sauvegardes disponibles:"
    ls -lh "$BACKUP_DIR"/geoclic_backup_*.sql.gz 2>/dev/null
    exit 1
fi

BACKUP_FILE="$1"

# Si le chemin n'est pas absolu, chercher dans BACKUP_DIR
if [[ "$BACKUP_FILE" != /* ]]; then
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    fi
fi

# Vérifier que le fichier existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERREUR: Fichier non trouvé: $BACKUP_FILE"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════════════"
echo "  ATTENTION: RESTAURATION DE LA BASE DE DONNÉES"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Fichier de sauvegarde: $BACKUP_FILE"
echo "Base de données cible: $DB_NAME"
echo ""
echo "CETTE OPÉRATION VA ÉCRASER TOUTES LES DONNÉES ACTUELLES!"
echo ""
read -p "Êtes-vous sûr de vouloir continuer? (oui/non): " CONFIRM

if [ "$CONFIRM" != "oui" ]; then
    echo "Restauration annulée."
    exit 0
fi

echo ""
echo "Restauration en cours..."

# Arrêter les connexions à la base
echo "1/4 - Fermeture des connexions actives..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" > /dev/null 2>&1

# Supprimer et recréer la base
echo "2/4 - Recréation de la base de données..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Activer PostGIS
echo "3/4 - Activation des extensions..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Restaurer les données
echo "4/4 - Restauration des données..."
if gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  RESTAURATION TERMINÉE AVEC SUCCÈS"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "Redémarrez l'API pour appliquer les changements:"
    echo "  cd /opt/geoclic/deploy && sudo docker-compose restart api"
else
    echo ""
    echo "ERREUR: La restauration a échoué!"
    exit 1
fi

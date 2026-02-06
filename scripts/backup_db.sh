#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# GéoClic Suite - Script de sauvegarde automatique (DB + Photos)
# ═══════════════════════════════════════════════════════════════════════════════
# Usage: sudo /opt/geoclic/scripts/backup_db.sh
# Recommandé: Exécuter via cron tous les jours à 2h du matin
#
# Ce script:
# - Crée un dump complet de la base PostgreSQL (format custom + SQL compressé)
# - Sauvegarde le volume photos (tar.gz)
# - Vérifie l'intégrité des sauvegardes
# - Conserve les 7 derniers jours + 4 dernières semaines
# - Log toutes les opérations

# Configuration
BACKUP_DIR="/opt/geoclic/backups"
DB_CONTAINER="geoclic_db"
DB_NAME="geoclic_db"
DB_USER="geoclic"
PHOTOS_CONTAINER="geoclic_api"
PHOTOS_PATH="/app/photos"
RETENTION_DAILY=7
RETENTION_WEEKLY=28
DATE=$(date +%Y%m%d_%H%M%S)
DAY_OF_WEEK=$(date +%u)
BACKUP_FILE_SQL="geoclic_backup_${DATE}.sql.gz"
BACKUP_FILE_CUSTOM="geoclic_backup_${DATE}.dump"
BACKUP_FILE_PHOTOS="geoclic_photos_${DATE}.tar.gz"
LOG_FILE="/var/log/geoclic_backup.log"
EXIT_CODE=0

# Créer le répertoire de backup s'il n'existe pas
mkdir -p "$BACKUP_DIR"

# Fonction de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Début de la sauvegarde ==="

# Vérifier que le conteneur DB est en cours d'exécution
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    log "ERREUR: Le conteneur $DB_CONTAINER n'est pas en cours d'exécution!"
    exit 1
fi

# ─── SAUVEGARDE BASE DE DONNÉES (format SQL compressé) ───────────────────────
log "Création du dump SQL de la base de données..."
if docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE_SQL"; then
    if [ -s "$BACKUP_DIR/$BACKUP_FILE_SQL" ]; then
        SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE_SQL" | cut -f1)
        log "OK: Dump SQL créé: $BACKUP_FILE_SQL ($SIZE)"
    else
        log "ERREUR: Le fichier SQL est vide!"
        rm -f "$BACKUP_DIR/$BACKUP_FILE_SQL"
        EXIT_CODE=1
    fi
else
    log "ERREUR: Échec du dump SQL!"
    EXIT_CODE=1
fi

# ─── SAUVEGARDE BASE DE DONNÉES (format custom - restauration sélective) ─────
log "Création du dump format custom (restauration sélective)..."
if docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_DIR/$BACKUP_FILE_CUSTOM"; then
    if [ -s "$BACKUP_DIR/$BACKUP_FILE_CUSTOM" ]; then
        SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE_CUSTOM" | cut -f1)
        log "OK: Dump custom créé: $BACKUP_FILE_CUSTOM ($SIZE)"

        # Vérification d'intégrité du dump custom
        log "Vérification d'intégrité..."
        if docker exec -i "$DB_CONTAINER" pg_restore --list < "$BACKUP_DIR/$BACKUP_FILE_CUSTOM" > /dev/null 2>&1; then
            TABLE_COUNT=$(docker exec -i "$DB_CONTAINER" pg_restore --list < "$BACKUP_DIR/$BACKUP_FILE_CUSTOM" 2>/dev/null | grep -c "TABLE DATA")
            log "OK: Intégrité vérifiée ($TABLE_COUNT tables avec données)"
        else
            log "ATTENTION: Vérification d'intégrité échouée (le dump peut être corrompu)"
            EXIT_CODE=1
        fi
    else
        log "ERREUR: Le fichier custom est vide!"
        rm -f "$BACKUP_DIR/$BACKUP_FILE_CUSTOM"
        EXIT_CODE=1
    fi
else
    log "ERREUR: Échec du dump custom!"
    EXIT_CODE=1
fi

# ─── SAUVEGARDE DES PHOTOS ───────────────────────────────────────────────────
if docker ps --format '{{.Names}}' | grep -q "^${PHOTOS_CONTAINER}$"; then
    log "Sauvegarde des photos..."
    if docker exec "$PHOTOS_CONTAINER" tar czf - -C "$PHOTOS_PATH" . > "$BACKUP_DIR/$BACKUP_FILE_PHOTOS" 2>/dev/null; then
        if [ -s "$BACKUP_DIR/$BACKUP_FILE_PHOTOS" ]; then
            SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE_PHOTOS" | cut -f1)
            PHOTO_COUNT=$(docker exec "$PHOTOS_CONTAINER" find "$PHOTOS_PATH" -type f \( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' \) 2>/dev/null | wc -l)
            log "OK: Photos sauvegardées: $BACKUP_FILE_PHOTOS ($SIZE, ~$PHOTO_COUNT fichiers)"
        else
            log "ATTENTION: Le fichier photos est vide (aucune photo à sauvegarder?)"
            rm -f "$BACKUP_DIR/$BACKUP_FILE_PHOTOS"
        fi
    else
        log "ATTENTION: Échec de la sauvegarde des photos"
    fi
else
    log "ATTENTION: Conteneur $PHOTOS_CONTAINER non trouvé, photos non sauvegardées"
fi

# ─── ROTATION DES SAUVEGARDES ────────────────────────────────────────────────
# Garder les sauvegardes quotidiennes pendant RETENTION_DAILY jours
log "Nettoyage des sauvegardes quotidiennes (> $RETENTION_DAILY jours)..."
DELETED_SQL=$(find "$BACKUP_DIR" -name "geoclic_backup_*.sql.gz" -type f -mtime +$RETENTION_DAILY -delete -print 2>/dev/null | wc -l)
DELETED_CUSTOM=$(find "$BACKUP_DIR" -name "geoclic_backup_*.dump" -type f -mtime +$RETENTION_DAILY -delete -print 2>/dev/null | wc -l)
DELETED_PHOTOS=$(find "$BACKUP_DIR" -name "geoclic_photos_*.tar.gz" -type f -mtime +$RETENTION_DAILY -delete -print 2>/dev/null | wc -l)
log "Supprimés: $DELETED_SQL SQL + $DELETED_CUSTOM dumps + $DELETED_PHOTOS photos"

# Garder une sauvegarde hebdomadaire pendant RETENTION_WEEKLY jours
# (le dimanche = jour 7, on garde ces sauvegardes plus longtemps)
if [ "$DAY_OF_WEEK" != "7" ]; then
    DELETED_OLD=$(find "$BACKUP_DIR" -name "geoclic_*" -type f -mtime +$RETENTION_WEEKLY -delete -print 2>/dev/null | wc -l)
    if [ "$DELETED_OLD" -gt 0 ]; then
        log "Supprimées $DELETED_OLD anciennes sauvegardes hebdomadaires"
    fi
fi

# ─── RÉSUMÉ ──────────────────────────────────────────────────────────────────
log "Sauvegardes disponibles:"
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
TOTAL_FILES=$(ls "$BACKUP_DIR"/geoclic_* 2>/dev/null | wc -l)
log "  Total: $TOTAL_FILES fichiers, $TOTAL_SIZE"

if [ "$EXIT_CODE" -eq 0 ]; then
    log "=== Sauvegarde terminée avec succès ==="
else
    log "=== Sauvegarde terminée avec des erreurs (code: $EXIT_CODE) ==="
fi

exit $EXIT_CODE

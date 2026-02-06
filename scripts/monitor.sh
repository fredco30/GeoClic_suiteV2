#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# GéoClic Suite - Script de monitoring
# ═══════════════════════════════════════════════════════════════════════════════
# Usage: sudo /opt/geoclic/scripts/monitor.sh
# Recommandé: Exécuter via cron toutes les 5 minutes
#
# Ce script vérifie:
# - Que l'API répond (HTTP 200)
# - Que tous les conteneurs Docker sont en cours d'exécution
# - L'espace disque disponible

# Configuration
API_URL="https://geoclic.fr/api/health"
LOG_FILE="/var/log/geoclic_monitor.log"
ALERT_FILE="/tmp/geoclic_alert_sent"
DISK_THRESHOLD=90  # Alerte si disque > 90%

# Conteneurs à surveiller (les principaux)
CONTAINERS=("geoclic_db" "geoclic_api" "geoclic_nginx" "geoclic_portail" "geoclic_demandes")

# Couleurs pour le terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Fonction d'affichage
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}[OK]${NC} $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}[WARN]${NC} $message"
    else
        echo -e "${RED}[ERREUR]${NC} $message"
    fi
}

# Variable pour suivre les erreurs
ERRORS=0

echo "═══════════════════════════════════════════════════════════════════"
echo "  GéoClic Suite - Monitoring"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 1. Vérification de l'API
# ─────────────────────────────────────────────────────────────────────────────
echo "1. API Health Check"
echo "   URL: $API_URL"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$API_URL" 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    print_status "OK" "API répond correctement (HTTP $HTTP_CODE)"
else
    print_status "ERREUR" "API ne répond pas! (HTTP $HTTP_CODE)"
    log "ERREUR: API ne répond pas (HTTP $HTTP_CODE)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 2. Vérification des conteneurs Docker
# ─────────────────────────────────────────────────────────────────────────────
echo "2. Conteneurs Docker"

for container in "${CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        # Récupérer le statut et l'uptime
        STATUS=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
        UPTIME=$(docker inspect --format='{{.State.StartedAt}}' "$container" 2>/dev/null | cut -d'T' -f1)
        print_status "OK" "$container (running depuis $UPTIME)"
    else
        print_status "ERREUR" "$container n'est pas en cours d'exécution!"
        log "ERREUR: Conteneur $container arrêté"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 3. Vérification de l'espace disque
# ─────────────────────────────────────────────────────────────────────────────
echo "3. Espace disque"

DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_AVAIL=$(df -h / | tail -1 | awk '{print $4}')

if [ "$DISK_USAGE" -lt "$DISK_THRESHOLD" ]; then
    print_status "OK" "Utilisation: ${DISK_USAGE}% (${DISK_AVAIL} disponible)"
else
    print_status "WARN" "Utilisation: ${DISK_USAGE}% - ATTENTION disque presque plein!"
    log "WARN: Disque à ${DISK_USAGE}%"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 4. Vérification de la mémoire
# ─────────────────────────────────────────────────────────────────────────────
echo "4. Mémoire"

MEM_TOTAL=$(free -h | grep Mem | awk '{print $2}')
MEM_USED=$(free -h | grep Mem | awk '{print $3}')
MEM_PERCENT=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100)}')

if [ "$MEM_PERCENT" -lt 90 ]; then
    print_status "OK" "Utilisation: ${MEM_PERCENT}% (${MEM_USED} / ${MEM_TOTAL})"
else
    print_status "WARN" "Utilisation: ${MEM_PERCENT}% - ATTENTION mémoire presque pleine!"
    log "WARN: Mémoire à ${MEM_PERCENT}%"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 5. Dernière sauvegarde
# ─────────────────────────────────────────────────────────────────────────────
echo "5. Dernière sauvegarde"

BACKUP_DIR="/opt/geoclic/backups"
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/geoclic_backup_*.sql.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_DATE=$(stat -c %y "$LATEST_BACKUP" | cut -d'.' -f1)
        BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
        BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 86400 ))

        if [ "$BACKUP_AGE" -le 1 ]; then
            print_status "OK" "Dernière: $BACKUP_DATE ($BACKUP_SIZE)"
        else
            print_status "WARN" "Dernière: $BACKUP_DATE (il y a ${BACKUP_AGE} jours!)"
            log "WARN: Backup vieux de ${BACKUP_AGE} jours"
        fi
    else
        print_status "WARN" "Aucune sauvegarde trouvée!"
        log "WARN: Aucune sauvegarde"
    fi
else
    print_status "WARN" "Dossier de backup non créé"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Résumé
# ─────────────────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════════"
if [ "$ERRORS" -eq 0 ]; then
    echo -e "  ${GREEN}Tout est OK${NC}"
    # Supprimer le fichier d'alerte si tout va bien
    rm -f "$ALERT_FILE"
else
    echo -e "  ${RED}$ERRORS erreur(s) détectée(s)!${NC}"
    log "RÉSUMÉ: $ERRORS erreur(s)"

    # Créer un fichier d'alerte (pour éviter le spam)
    if [ ! -f "$ALERT_FILE" ]; then
        touch "$ALERT_FILE"
        echo ""
        echo "  Pour plus de détails: tail -50 $LOG_FILE"
    fi
fi
echo "═══════════════════════════════════════════════════════════════════"

exit $ERRORS

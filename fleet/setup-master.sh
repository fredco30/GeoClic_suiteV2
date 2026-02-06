#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# GéoClic Fleet Manager - Setup du serveur maître
#
# Ce script configure geoclic.fr comme serveur maître pour la gestion de flotte.
# À exécuter UNE SEULE FOIS sur le serveur maître.
#
# Usage: sudo bash /opt/geoclic/fleet/setup-master.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${BOLD}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   GéoClic Fleet Manager - Configuration   ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════╝${NC}"
echo ""

GEOCLIC_DIR="/opt/geoclic"
FLEET_DIR="$GEOCLIC_DIR/fleet"
DEPLOY_DIR="$GEOCLIC_DIR/deploy"
SSH_USER="${SUDO_USER:-ubuntu}"
SSH_DIR="/home/$SSH_USER/.ssh"
SSH_KEY="$SSH_DIR/geoclic_fleet_key"

# Vérifier qu'on est root ou sudo
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Ce script doit être exécuté avec sudo${NC}"
    exit 1
fi

# Vérifier qu'on est sur le bon serveur
if [[ ! -d "$GEOCLIC_DIR/deploy" ]]; then
    echo -e "${RED}GéoClic non trouvé dans $GEOCLIC_DIR${NC}"
    exit 1
fi

# ─── Étape 1: Générer la clé SSH fleet ────────────────────────────────────────
echo -e "${CYAN}[1/5]${NC} Génération de la clé SSH fleet..."

if [[ -f "$SSH_KEY" ]]; then
    echo -e "${YELLOW}  La clé SSH existe déjà : $SSH_KEY${NC}"
else
    sudo -u "$SSH_USER" ssh-keygen -t ed25519 -f "$SSH_KEY" -N "" -C "geoclic-fleet@$(hostname)"
    echo -e "${GREEN}  Clé SSH générée${NC}"
fi

echo -e "${BOLD}  Clé publique :${NC}"
echo -e "${BLUE}  $(cat ${SSH_KEY}.pub)${NC}"
echo ""

# ─── Étape 2: Créer les dossiers nécessaires ────────────────────────────────
echo -e "${CYAN}[2/5]${NC} Création des dossiers..."

mkdir -p "$FLEET_DIR/logs" "$FLEET_DIR/tasks"
chmod +x "$FLEET_DIR/geoclic-fleet.sh" 2>/dev/null || true

# Créer clients.conf s'il n'existe pas
if [[ ! -f "$FLEET_DIR/clients.conf" ]]; then
    cat > "$FLEET_DIR/clients.conf" <<'EOF'
# GéoClic Fleet - Registre des serveurs clients
# ──────────────────────────────────────────────
# Format: NOM|DOMAINE|IP|SSH_USER|SSH_PORT|METHOD|DATE_AJOUT
#
# Ce fichier est géré par geoclic-fleet.sh
# Vous pouvez aussi l'éditer à la main.
# ──────────────────────────────────────────────
EOF
    echo -e "${GREEN}  clients.conf créé${NC}"
fi

# ─── Étape 3: Copier la config nginx fleet ───────────────────────────────────
echo -e "${CYAN}[3/5]${NC} Configuration Nginx pour /fleet/..."

cp "$FLEET_DIR/nginx-fleet.conf" "$DEPLOY_DIR/nginx/conf.d/fleet-routes.conf"
echo -e "${GREEN}  Route /fleet/ ajoutée à nginx${NC}"

# ─── Étape 4: Créer le docker-compose.override.yml ──────────────────────────
echo -e "${CYAN}[4/5]${NC} Configuration Docker du service Fleet..."

cat > "$DEPLOY_DIR/docker-compose.override.yml" <<OVERRIDE
# ═══════════════════════════════════════════════════════════════════════════════
# Docker Compose Override - GéoClic Fleet Manager
# Généré automatiquement par setup-master.sh
# ═══════════════════════════════════════════════════════════════════════════════

version: "3.9"

services:
  fleet:
    build:
      context: ..
      dockerfile: fleet/Dockerfile
    container_name: geoclic_fleet
    restart: unless-stopped
    environment:
      JWT_SECRET_KEY: "\${JWT_SECRET_KEY}"
    volumes:
      - $SSH_DIR:/root/.ssh:ro
      - $FLEET_DIR/clients.conf:/opt/geoclic/fleet/clients.conf
      - fleet_logs:/opt/geoclic/fleet/logs
      - fleet_tasks:/opt/geoclic/fleet/tasks
      - $GEOCLIC_DIR:/opt/geoclic:ro
    networks:
      - geoclic_network

volumes:
  fleet_logs:
    name: geoclic_fleet_logs
  fleet_tasks:
    name: geoclic_fleet_tasks
OVERRIDE

echo -e "${GREEN}  docker-compose.override.yml créé${NC}"

# ─── Étape 5: Build et démarrage ────────────────────────────────────────────
echo -e "${CYAN}[5/5]${NC} Construction et démarrage du service Fleet..."

cd "$DEPLOY_DIR"

# Rebuild fleet + nginx
docker compose build fleet 2>&1 || docker-compose build fleet 2>&1
docker compose up -d fleet nginx 2>&1 || docker-compose up -d fleet nginx 2>&1

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Fleet Manager installé avec succès !${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Dashboard : ${BOLD}https://$(hostname -f)/fleet/${NC}"
echo -e "  Connectez-vous avec votre compte super admin GéoClic."
echo ""
echo -e "  ${YELLOW}Clé SSH à copier sur les nouveaux VPS :${NC}"
echo -e "  ${BLUE}$(cat ${SSH_KEY}.pub)${NC}"
echo ""
echo -e "  ${BOLD}Prochaine étape :${NC}"
echo -e "  Ajoutez un VPS depuis le dashboard ou avec la commande :"
echo -e "  ${CYAN}sudo bash $FLEET_DIR/geoclic-fleet.sh add --name mon-client --domain client.geoclic.fr --ip 1.2.3.4${NC}"
echo ""

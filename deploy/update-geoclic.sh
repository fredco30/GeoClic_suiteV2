#!/bin/bash
# Script de mise à jour GéoClic Suite
# Usage: sudo ./update-geoclic.sh [branche]

set -e

# Configuration
REPO_URL="https://github.com/fredco30/GeoClic_Suite.git"
BRANCH="${1:-main}"
DEPLOY_DIR="/opt/geoclic"
TEMP_DIR="/tmp/geoclic-update-$$"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   GéoClic Suite - Mise à jour${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Vérifier les droits root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Ce script doit être exécuté en tant que root (sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}[1/5]${NC} Téléchargement de la branche '${BRANCH}'..."
rm -rf "$TEMP_DIR"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TEMP_DIR"

echo -e "${GREEN}[2/5]${NC} Sauvegarde de la configuration actuelle..."
if [ -f "$DEPLOY_DIR/deploy/.env" ]; then
    cp "$DEPLOY_DIR/deploy/.env" "/tmp/geoclic-env-backup"
fi

echo -e "${GREEN}[3/5]${NC} Mise à jour des fichiers..."
# Copier les fichiers mis à jour (sauf .env et données)
rsync -av --exclude='.env' --exclude='*.sqlite' --exclude='uploads/' \
    "$TEMP_DIR/" "$DEPLOY_DIR/"

# Restaurer .env si existant
if [ -f "/tmp/geoclic-env-backup" ]; then
    cp "/tmp/geoclic-env-backup" "$DEPLOY_DIR/deploy/.env"
fi

echo -e "${GREEN}[4/5]${NC} Reconstruction des conteneurs..."
cd "$DEPLOY_DIR/deploy"

# Demander quels services reconstruire
echo ""
echo "Quels services voulez-vous reconstruire ?"
echo "  1) sig      - SIG Web uniquement (rapide)"
echo "  2) all      - Tous les services (plus long)"
echo "  3) none     - Aucun (juste copier les fichiers)"
echo ""
read -p "Choix [1/2/3]: " choice

case $choice in
    1)
        docker compose up -d --build sig
        ;;
    2)
        docker compose up -d --build
        ;;
    3)
        echo "Fichiers copiés, pas de reconstruction."
        ;;
    *)
        docker compose up -d --build sig
        ;;
esac

echo -e "${GREEN}[5/5]${NC} Nettoyage..."
rm -rf "$TEMP_DIR"
rm -f "/tmp/geoclic-env-backup"

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}   Mise à jour terminée !${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
docker compose ps

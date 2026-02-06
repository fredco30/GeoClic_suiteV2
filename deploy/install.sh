#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Script d'installation GéoClic Suite V14.3 (Phase 3)
# Installation automatique sur VPS (Ubuntu/Debian)
# Inclut: Portail Citoyen, Gestion Demandes, Microsoft Graph Email
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/votre-repo/geoclic/main/deploy/install.sh | bash
#   ou
#   ./install.sh [options]
#
# Options:
#   --domain    Nom de domaine (ex: geoclic.maville.fr)
#   --email     Email pour Let's Encrypt
#   --dev       Mode développement (pas de SSL)
#   --help      Afficher l'aide
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
GEOCLIC_VERSION="14.3"  # Phase 3 - Portail Citoyen
GEOCLIC_DIR="/opt/geoclic"
GEOCLIC_USER="geoclic"
DOMAIN=""
EMAIL=""
DEV_MODE=false

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}   ___         ___  _ _       ___       _ _         ${NC}"
    echo -e "${GREEN}  / __|___ ___/ __|| (_) ___ / __| _  _(_) |_ ___   ${NC}"
    echo -e "${GREEN} | (_ / -_) _ \\    | | |/ __| \\__ \\| || | |  _/ -_)  ${NC}"
    echo -e "${GREEN}  \\___\\___\\___/\\___|_|_|\\___| |___/ \\_,_|_|\\__\\___|  ${NC}"
    echo -e "${GREEN}                                                     ${NC}"
    echo -e "${GREEN}   Version ${GEOCLIC_VERSION} - Installation automatique          ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --domain DOMAIN   Nom de domaine (ex: geoclic.maville.fr)"
    echo "  --email EMAIL     Email pour Let's Encrypt"
    echo "  --dev             Mode développement (pas de SSL)"
    echo "  --help            Afficher cette aide"
    echo ""
    echo "Exemple:"
    echo "  $0 --domain geoclic.maville.fr --email admin@maville.fr"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# PARSING DES ARGUMENTS
# ═══════════════════════════════════════════════════════════════════════════════
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# ═══════════════════════════════════════════════════════════════════════════════
# VÉRIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════
print_banner

log_info "Vérification des prérequis..."

# Vérifier qu'on est root
if [[ $EUID -ne 0 ]]; then
    log_error "Ce script doit être exécuté en tant que root (sudo)"
    exit 1
fi

# Vérifier le système
if ! command -v apt-get &> /dev/null; then
    log_error "Ce script nécessite un système Debian/Ubuntu"
    exit 1
fi

log_success "Système compatible détecté"

# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLATION DES DÉPENDANCES
# ═══════════════════════════════════════════════════════════════════════════════
log_info "Mise à jour du système..."
apt-get update -qq
apt-get upgrade -y -qq

log_info "Installation des dépendances..."
apt-get install -y -qq \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw

log_success "Dépendances installées"

# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLATION DE DOCKER
# ═══════════════════════════════════════════════════════════════════════════════
if ! command -v docker &> /dev/null; then
    log_info "Installation de Docker..."

    # Ajouter la clé GPG Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Ajouter le repo Docker
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Démarrer Docker
    systemctl start docker
    systemctl enable docker

    log_success "Docker installé"
else
    log_success "Docker déjà installé"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# CRÉATION DE L'UTILISATEUR
# ═══════════════════════════════════════════════════════════════════════════════
if ! id "$GEOCLIC_USER" &>/dev/null; then
    log_info "Création de l'utilisateur $GEOCLIC_USER..."
    useradd -r -m -d "$GEOCLIC_DIR" -s /bin/bash "$GEOCLIC_USER"
    usermod -aG docker "$GEOCLIC_USER"
    log_success "Utilisateur créé"
else
    log_success "Utilisateur $GEOCLIC_USER existe déjà"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# CLONAGE DU PROJET
# ═══════════════════════════════════════════════════════════════════════════════
log_info "Téléchargement de GéoClic Suite..."

if [[ -d "$GEOCLIC_DIR/GeoClic_Suite" ]]; then
    log_warn "Installation existante détectée, mise à jour..."
    cd "$GEOCLIC_DIR/GeoClic_Suite"
    git pull origin main
else
    mkdir -p "$GEOCLIC_DIR"
    cd "$GEOCLIC_DIR"
    # NOTE: Remplacez par votre URL de dépôt
    git clone https://github.com/votre-repo/GeoClic_Suite.git
fi

cd "$GEOCLIC_DIR/GeoClic_Suite"
log_success "Code source téléchargé"

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
log_info "Configuration de l'environnement..."

# Créer le fichier .env
ENV_FILE="$GEOCLIC_DIR/GeoClic_Suite/deploy/.env"

# Générer des mots de passe sécurisés
DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
JWT_SECRET=$(openssl rand -base64 64 | tr -dc 'a-zA-Z0-9' | head -c 48)

cat > "$ENV_FILE" << EOF
# ═══════════════════════════════════════════════════════════════════════════════
# Configuration GéoClic Suite V14.3 (Phase 3)
# Généré automatiquement le $(date)
# ═══════════════════════════════════════════════════════════════════════════════

# Base de données
DB_USER=admin_geoclic
DB_PASSWORD=$DB_PASSWORD
DB_NAME=geoclic_db
DB_PORT=5432

# API
JWT_SECRET_KEY=$JWT_SECRET
JWT_EXPIRE_MINUTES=60
API_PORT=8000
APP_ENV=production
DEBUG=false

# Admin (Gestion patrimoine)
ADMIN_PORT=3000
API_PUBLIC_URL=${DOMAIN:+https://$DOMAIN}${DOMAIN:-http://localhost:8000}

# Portail Citoyen (signalements publics)
PORTAIL_PORT=5174

# Back-office Demandes (gestion des signalements)
DEMANDES_PORT=5175

# Mobile PWA (relevé terrain)
MOBILE_PORT=5176

# Nginx
HTTP_PORT=80
HTTPS_PORT=443

# Photos
PHOTO_MAX_SIZE=10

# CORS (ajouter vos domaines)
CORS_ORIGINS=${DOMAIN:-*}

# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL - Choisir UNE des deux options ci-dessous
# ═══════════════════════════════════════════════════════════════════════════════

# Option 1: SMTP classique (Gmail, OVH, etc.)
# EMAIL_PROVIDER=smtp
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=noreply@mairie.fr
# SMTP_PASSWORD=votre_mot_de_passe
# EMAIL_FROM=noreply@mairie.fr
# EMAIL_FROM_NAME=Mairie de VotreVille

# Option 2: Microsoft 365 / Outlook (RECOMMANDÉ pour mairies)
# Créez une App Registration sur https://portal.azure.com
# EMAIL_PROVIDER=microsoft
# MS_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# MS_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# MS_CLIENT_SECRET=votre_client_secret
# EMAIL_FROM=noreply@mairie.fr
# EMAIL_FROM_NAME=Mairie de VotreVille
EOF

chmod 600 "$ENV_FILE"
log_success "Configuration créée"

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION SSL (si domaine spécifié)
# ═══════════════════════════════════════════════════════════════════════════════
if [[ -n "$DOMAIN" ]] && [[ "$DEV_MODE" == "false" ]]; then
    log_info "Configuration SSL avec Let's Encrypt..."

    # Installer certbot
    apt-get install -y -qq certbot

    # Obtenir le certificat
    if [[ -n "$EMAIL" ]]; then
        certbot certonly --standalone --non-interactive --agree-tos \
            --email "$EMAIL" -d "$DOMAIN"
    else
        certbot certonly --standalone --non-interactive --agree-tos \
            --register-unsafely-without-email -d "$DOMAIN"
    fi

    # Copier les certificats
    mkdir -p "$GEOCLIC_DIR/GeoClic_Suite/deploy/nginx/ssl"
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem "$GEOCLIC_DIR/GeoClic_Suite/deploy/nginx/ssl/"
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem "$GEOCLIC_DIR/GeoClic_Suite/deploy/nginx/ssl/"

    # Activer HTTPS dans nginx.conf
    # (TODO: script de modification du nginx.conf)

    log_success "Certificat SSL obtenu"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION FIREWALL
# ═══════════════════════════════════════════════════════════════════════════════
log_info "Configuration du firewall..."

ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

log_success "Firewall configuré"

# ═══════════════════════════════════════════════════════════════════════════════
# DÉMARRAGE DES SERVICES
# ═══════════════════════════════════════════════════════════════════════════════
log_info "Démarrage des services Docker..."

cd "$GEOCLIC_DIR/GeoClic_Suite/deploy"

# Build et démarrage
docker compose build
docker compose up -d

# Attendre que les services soient prêts
log_info "Attente du démarrage des services..."
sleep 30

# Vérifier la santé
if docker compose ps | grep -q "healthy"; then
    log_success "Services démarrés avec succès"
else
    log_warn "Certains services peuvent nécessiter plus de temps pour démarrer"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# CRÉATION DU SERVICE SYSTEMD
# ═══════════════════════════════════════════════════════════════════════════════
log_info "Création du service systemd..."

cat > /etc/systemd/system/geoclic.service << EOF
[Unit]
Description=GéoClic Suite V14
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$GEOCLIC_DIR/GeoClic_Suite/deploy
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable geoclic.service

log_success "Service systemd créé"

# ═══════════════════════════════════════════════════════════════════════════════
# SCRIPTS DE MAINTENANCE
# ═══════════════════════════════════════════════════════════════════════════════
log_info "Création des scripts de maintenance..."

# Script de sauvegarde
cat > "$GEOCLIC_DIR/backup.sh" << 'EOF'
#!/bin/bash
# Sauvegarde GéoClic
BACKUP_DIR="/var/backups/geoclic"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Sauvegarde PostgreSQL
docker exec geoclic_db pg_dump -U admin_geoclic geoclic_db > "$BACKUP_DIR/geoclic_db_$DATE.sql"

# Sauvegarde photos
tar -czf "$BACKUP_DIR/photos_$DATE.tar.gz" /opt/geoclic/GeoClic_Suite/deploy/photos 2>/dev/null || true

# Nettoyage des vieilles sauvegardes (garder 7 jours)
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Sauvegarde terminée: $BACKUP_DIR"
EOF

chmod +x "$GEOCLIC_DIR/backup.sh"

# Ajouter au cron (sauvegarde quotidienne à 2h)
(crontab -l 2>/dev/null; echo "0 2 * * * $GEOCLIC_DIR/backup.sh") | crontab -

log_success "Scripts de maintenance créés"

# ═══════════════════════════════════════════════════════════════════════════════
# FIN DE L'INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════════

# Obtenir l'IP du serveur
SERVER_IP=$(curl -s ifconfig.me || echo "votre-ip")

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Installation terminée avec succès !                                        ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Informations de connexion :${NC}"
echo ""
if [[ -n "$DOMAIN" ]]; then
    echo -e "  Admin Patrimoine :   ${GREEN}https://$DOMAIN/admin${NC}"
    echo -e "  Portail Citoyen :    ${GREEN}https://$DOMAIN${NC}"
    echo -e "  Gestion Demandes :   ${GREEN}https://$DOMAIN/demandes${NC}"
    echo -e "  Mobile PWA :         ${GREEN}https://$DOMAIN/mobile${NC}"
    echo -e "  API :                ${GREEN}https://$DOMAIN/api${NC}"
else
    echo -e "  Admin Patrimoine :   ${GREEN}http://$SERVER_IP:3000${NC}"
    echo -e "  Portail Citoyen :    ${GREEN}http://$SERVER_IP:5174${NC}"
    echo -e "  Gestion Demandes :   ${GREEN}http://$SERVER_IP:5175${NC}"
    echo -e "  Mobile PWA :         ${GREEN}http://$SERVER_IP:5176${NC}"
    echo -e "  API :                ${GREEN}http://$SERVER_IP:8000${NC}"
fi
echo ""
echo -e "${BLUE}Base de données :${NC}"
echo -e "  Hôte :               localhost"
echo -e "  Port :               5432"
echo -e "  Base :               geoclic_db"
echo -e "  Utilisateur :        admin_geoclic"
echo -e "  Mot de passe :       ${YELLOW}(voir $ENV_FILE)${NC}"
echo ""
echo -e "${BLUE}Commandes utiles :${NC}"
echo -e "  Voir les logs :      ${YELLOW}cd $GEOCLIC_DIR/GeoClic_Suite/deploy && docker compose logs -f${NC}"
echo -e "  Redémarrer :         ${YELLOW}systemctl restart geoclic${NC}"
echo -e "  Sauvegarde :         ${YELLOW}$GEOCLIC_DIR/backup.sh${NC}"
echo ""
echo -e "${BLUE}Documentation :${NC}"
echo -e "  Guide installation : ${GREEN}$GEOCLIC_DIR/GeoClic_Suite/docs/GUIDE_INSTALLATION_OVH.md${NC}"
echo -e "  Guide interactif :   ${GREEN}$GEOCLIC_DIR/GeoClic_Suite/docs/guide-installation-ovh.html${NC}"
echo ""
echo -e "${BLUE}Prochaines étapes :${NC}"
echo -e "  1. Configurez les emails dans ${YELLOW}$ENV_FILE${NC}"
echo -e "  2. (Optionnel) Configurez Microsoft Graph pour Office 365"
echo -e "  3. Configurez les catégories de signalement dans l'admin"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"

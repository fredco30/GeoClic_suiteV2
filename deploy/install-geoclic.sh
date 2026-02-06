#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Script d'installation SIMPLE de GéoClic Suite
#
# Pour les débutants : UNE SEULE COMMANDE à copier-coller !
#
# curl -sSL https://raw.githubusercontent.com/fredco30/GeoClic_Suite/main/deploy/install-geoclic.sh | sudo bash -s -- --domain geoclic.fr --email votre@email.fr
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
GEOCLIC_VERSION="14.3"
GEOCLIC_DIR="/opt/geoclic"
DOMAIN=""
EMAIL=""
REPO_URL="https://github.com/fredco30/GeoClic_Suite.git"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
print_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}   $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

log_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Fonction pour détecter la commande docker compose
get_docker_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    elif docker-compose version &> /dev/null; then
        echo "docker-compose"
    else
        echo ""
    fi
}

DOCKER_COMPOSE=""

print_banner() {
    clear
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                                                                               ${NC}"
    echo -e "${GREEN}     ██████╗ ███████╗ ██████╗  ██████╗██╗     ██╗ ██████╗                      ${NC}"
    echo -e "${GREEN}    ██╔════╝ ██╔════╝██╔═══██╗██╔════╝██║     ██║██╔════╝                      ${NC}"
    echo -e "${GREEN}    ██║  ███╗█████╗  ██║   ██║██║     ██║     ██║██║                           ${NC}"
    echo -e "${GREEN}    ██║   ██║██╔══╝  ██║   ██║██║     ██║     ██║██║                           ${NC}"
    echo -e "${GREEN}    ╚██████╔╝███████╗╚██████╔╝╚██████╗███████╗██║╚██████╗                      ${NC}"
    echo -e "${GREEN}     ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚══════╝╚═╝ ╚═════╝                      ${NC}"
    echo -e "${GREEN}                                                                               ${NC}"
    echo -e "${GREEN}                    Installation Automatique v${GEOCLIC_VERSION}                          ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
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
        --help)
            echo "Usage: $0 --domain votre-domaine.fr --email votre@email.fr"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# ═══════════════════════════════════════════════════════════════════════════════
# VÉRIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════
print_banner

if [[ $EUID -ne 0 ]]; then
    log_error "Ce script doit être exécuté en tant que root (avec sudo)"
    echo ""
    echo "Relancez avec : sudo $0 $@"
    exit 1
fi

if [[ -z "$DOMAIN" ]]; then
    log_error "Le domaine est requis !"
    echo ""
    echo "Usage: $0 --domain geoclic.fr --email admin@geoclic.fr"
    exit 1
fi

if [[ -z "$EMAIL" ]]; then
    log_error "L'email est requis pour Let's Encrypt !"
    echo ""
    echo "Usage: $0 --domain geoclic.fr --email admin@geoclic.fr"
    exit 1
fi

log_ok "Vérifications passées"
log_info "Domaine : $DOMAIN"
log_info "Email : $EMAIL"

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : MISE À JOUR DU SYSTÈME
# ═══════════════════════════════════════════════════════════════════════════════
print_step "ÉTAPE 1/6 : Mise à jour du système"

apt-get update -qq
apt-get upgrade -y -qq
log_ok "Système mis à jour"

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : INSTALLATION DE DOCKER
# ═══════════════════════════════════════════════════════════════════════════════
print_step "ÉTAPE 2/6 : Installation de Docker"

if command -v docker &> /dev/null; then
    log_ok "Docker déjà installé"
else
    log_info "Installation de Docker en cours..."

    # Installer les dépendances
    apt-get install -y -qq ca-certificates curl gnupg lsb-release

    # Ajouter la clé GPG Docker
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Ajouter le repo Docker
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Démarrer Docker
    systemctl start docker
    systemctl enable docker

    log_ok "Docker installé avec succès"
fi

# Détecter la commande docker compose disponible
DOCKER_COMPOSE=$(get_docker_compose_cmd)
if [[ -z "$DOCKER_COMPOSE" ]]; then
    log_error "Ni 'docker compose' ni 'docker-compose' n'est disponible"
    exit 1
fi
log_ok "Utilisation de : $DOCKER_COMPOSE"

# Si l'ancienne version docker-compose v1 est installée, recommander de la supprimer
if command -v docker-compose &> /dev/null && docker compose version &> /dev/null; then
    log_warn "L'ancienne version docker-compose (v1) est installée en plus de docker compose (v2)"
    log_info "Pour éviter les bugs de compatibilité, vous pouvez la désinstaller :"
    log_info "   sudo apt remove docker-compose"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 3 : TÉLÉCHARGEMENT DE GÉOCLIC
# ═══════════════════════════════════════════════════════════════════════════════
print_step "ÉTAPE 3/6 : Téléchargement de GéoClic"

# Installer git si nécessaire
apt-get install -y -qq git

# Créer le répertoire
mkdir -p "$GEOCLIC_DIR"
cd "$GEOCLIC_DIR"

if [[ -d "GeoClic_Suite" ]]; then
    log_info "Mise à jour du code existant..."
    cd GeoClic_Suite
    git pull origin main || git pull origin master || true
else
    log_info "Téléchargement du code..."
    git clone "$REPO_URL" || {
        log_error "Impossible de cloner le dépôt. Vérifiez l'URL du repo."
        exit 1
    }
    cd GeoClic_Suite
fi

log_ok "Code source téléchargé"

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 4 : CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
print_step "ÉTAPE 4/6 : Configuration de GéoClic"

cd "$GEOCLIC_DIR/GeoClic_Suite/deploy"

# Générer des mots de passe sécurisés
DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
JWT_SECRET=$(openssl rand -base64 64 | tr -dc 'a-zA-Z0-9' | head -c 48)

# Créer le fichier .env
cat > .env << EOF
# ═══════════════════════════════════════════════════════════════════════════════
# Configuration GéoClic Suite V${GEOCLIC_VERSION}
# Généré automatiquement le $(date)
# DOMAINE : ${DOMAIN}
# ═══════════════════════════════════════════════════════════════════════════════

# Base de données PostgreSQL
DB_USER=geoclic
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=geoclic_db
DB_PORT=5432

# API FastAPI
JWT_SECRET_KEY=${JWT_SECRET}
JWT_EXPIRE_MINUTES=480
API_PORT=8000
APP_ENV=production
DEBUG=false

# URLs publiques
API_PUBLIC_URL=https://${DOMAIN}

# Ports des applications (internes Docker)
ADMIN_PORT=3000
PORTAIL_PORT=5174
DEMANDES_PORT=5175
MOBILE_PORT=5176
SIG_PORT=5177

# Photos
PHOTO_MAX_SIZE=10

# CORS
CORS_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}

# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL - Décommentez UNE des deux options ci-dessous
# ═══════════════════════════════════════════════════════════════════════════════

# Option 1: SMTP classique
# EMAIL_PROVIDER=smtp
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=noreply@${DOMAIN}
# SMTP_PASSWORD=votre_mot_de_passe
# EMAIL_FROM=noreply@${DOMAIN}
# EMAIL_FROM_NAME=GéoClic

# Option 2: Microsoft 365 (recommandé pour mairies)
# EMAIL_PROVIDER=microsoft
# MS_TENANT_ID=votre-tenant-id
# MS_CLIENT_ID=votre-client-id
# MS_CLIENT_SECRET=votre-client-secret
# EMAIL_FROM=noreply@${DOMAIN}
# EMAIL_FROM_NAME=GéoClic
EOF

chmod 600 .env
log_ok "Configuration créée"

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 5 : CONFIGURATION NGINX
# ═══════════════════════════════════════════════════════════════════════════════
print_step "ÉTAPE 5/8 : Configuration du serveur web (Nginx)"

# Vérifier si nginx est installé
if ! command -v nginx &> /dev/null; then
    log_info "Installation de Nginx..."
    apt-get install -y -qq nginx
fi

# Installer Certbot pour Let's Encrypt
if ! command -v certbot &> /dev/null; then
    log_info "Installation de Certbot (Let's Encrypt)..."
    apt-get install -y -qq certbot python3-certbot-nginx
fi

# Créer d'abord une configuration HTTP simple pour obtenir le certificat SSL
cat > /etc/nginx/sites-available/geoclic << EOF
# Configuration temporaire HTTP pour Let's Encrypt
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 200 'GéoClic - Installation en cours...';
        add_header Content-Type text/plain;
    }
}
EOF

# Activer le site temporaire
ln -sf /etc/nginx/sites-available/geoclic /etc/nginx/sites-enabled/geoclic
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
systemctl reload nginx

# Obtenir le certificat SSL avec Let's Encrypt
log_info "Obtention du certificat SSL Let's Encrypt..."
if [[ -n "$EMAIL" ]]; then
    certbot certonly --nginx -d ${DOMAIN} -d www.${DOMAIN} --non-interactive --agree-tos --email ${EMAIL} || {
        log_warn "Impossible d'obtenir le certificat pour www.${DOMAIN}, essai sans www..."
        certbot certonly --nginx -d ${DOMAIN} --non-interactive --agree-tos --email ${EMAIL} || {
            log_error "Échec de l'obtention du certificat SSL."
            log_info "Vérifiez que le domaine ${DOMAIN} pointe vers ce serveur."
            log_info "Vous pourrez relancer : sudo certbot --nginx -d ${DOMAIN}"
        }
    }
else
    certbot certonly --nginx -d ${DOMAIN} --non-interactive --agree-tos --register-unsafely-without-email || {
        log_warn "Échec du certificat SSL. Vous pourrez le configurer plus tard."
    }
fi

# Maintenant créer la configuration HTTPS complète
cat > /etc/nginx/sites-available/geoclic << EOF
# ═══════════════════════════════════════════════════════════════════════════════
# Configuration Nginx pour GéoClic Suite
# Domaine : ${DOMAIN}
# ═══════════════════════════════════════════════════════════════════════════════

# Redirection HTTP -> HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Configuration HTTPS
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name ${DOMAIN} www.${DOMAIN};

    # Certificats SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    # Configuration SSL sécurisée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Headers de sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Taille max des uploads (photos)
    client_max_body_size 20M;

    # ═══════════════════════════════════════════════════════════════════════════
    # API FastAPI
    # ═══════════════════════════════════════════════════════════════════════════
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    # ═══════════════════════════════════════════════════════════════════════════
    # Admin Patrimoine (GéoClic Data)
    # ═══════════════════════════════════════════════════════════════════════════
    location /admin {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # ═══════════════════════════════════════════════════════════════════════════
    # Back-office Demandes Citoyens
    # ═══════════════════════════════════════════════════════════════════════════
    location /demandes {
        proxy_pass http://127.0.0.1:5175;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # ═══════════════════════════════════════════════════════════════════════════
    # Mobile PWA (relevé terrain)
    # ═══════════════════════════════════════════════════════════════════════════
    location /mobile {
        proxy_pass http://127.0.0.1:5176;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # ═══════════════════════════════════════════════════════════════════════════
    # SIG Web (cartographie)
    # ═══════════════════════════════════════════════════════════════════════════
    location /sig {
        proxy_pass http://127.0.0.1:5177;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # ═══════════════════════════════════════════════════════════════════════════
    # Portail Citoyen (page d'accueil)
    # ═══════════════════════════════════════════════════════════════════════════
    location / {
        proxy_pass http://127.0.0.1:5174;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Activer le site
ln -sf /etc/nginx/sites-available/geoclic /etc/nginx/sites-enabled/geoclic

# Désactiver le site par défaut s'il existe
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# Tester la configuration
nginx -t

# Recharger Nginx
systemctl reload nginx

log_ok "Nginx configuré pour ${DOMAIN}"

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 6 : DÉMARRAGE DES SERVICES
# ═══════════════════════════════════════════════════════════════════════════════
print_step "ÉTAPE 6/8 : Démarrage de GéoClic"

cd "$GEOCLIC_DIR/GeoClic_Suite/deploy"

log_info "Construction des images Docker (cela peut prendre plusieurs minutes)..."

# Désactiver le service nginx interne (on utilise celui du host)
# Modifier docker-compose pour ne pas utiliser le nginx interne
# On va juste ne pas exposer les ports 80/443

# Créer un docker-compose override pour la production
cat > docker-compose.override.yml << EOF
# Override pour production avec Nginx externe
version: "3.9"

services:
  # Désactiver le nginx interne, on utilise celui du serveur
  nginx:
    profiles:
      - disabled
EOF

# Build et démarrage
$DOCKER_COMPOSE build --quiet
$DOCKER_COMPOSE up -d

log_info "Attente du démarrage des services..."
sleep 15

# Vérifier l'état
if $DOCKER_COMPOSE ps | grep -q "Up\|running"; then
    log_ok "Services démarrés avec succès !"
else
    log_warn "Certains services peuvent mettre plus de temps à démarrer"
    log_info "Vérifiez avec : $DOCKER_COMPOSE ps"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 7 : INITIALISATION DE LA BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════
print_step "ÉTAPE 7/8 : Initialisation de la base de données"

log_info "Attente que PostgreSQL soit prêt..."
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if $DOCKER_COMPOSE exec -T db pg_isready -U geoclic -d geoclic_db > /dev/null 2>&1; then
        log_ok "PostgreSQL est prêt"
        break
    fi
    RETRY=$((RETRY + 1))
    log_info "Attente de PostgreSQL... ($RETRY/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    log_error "PostgreSQL n'a pas démarré à temps"
    exit 1
fi

# Vérifier si les tables existent déjà
TABLES_EXIST=$($DOCKER_COMPOSE exec -T db psql -U geoclic -d geoclic_db -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users';" 2>/dev/null || echo "0")

if [ "$TABLES_EXIST" = "0" ]; then
    log_info "Création des tables de la base de données..."

    # Script principal
    log_info "Exécution du script d'initialisation principal..."
    if $DOCKER_COMPOSE exec -T db psql -U geoclic -d geoclic_db < "$GEOCLIC_DIR/GeoClic_Suite/database/init_v12_pro.sql" 2>&1 | tee /tmp/db_init.log | grep -i "error\|erreur" > /dev/null; then
        log_warn "Des erreurs ont été détectées lors de l'initialisation. Vérifiez /tmp/db_init.log"
    else
        log_ok "Script d'initialisation exécuté"
    fi

    # Migrations (dans l'ordre alphabétique)
    log_info "Application des migrations..."
    MIGRATION_ERRORS=0
    for migration in $(ls "$GEOCLIC_DIR/GeoClic_Suite/database/migrations/"*.sql 2>/dev/null | sort); do
        if [ -f "$migration" ]; then
            MIGRATION_NAME=$(basename "$migration")
            log_info "  → $MIGRATION_NAME"

            # Exécuter la migration et capturer les erreurs
            MIGRATION_OUTPUT=$($DOCKER_COMPOSE exec -T db psql -U geoclic -d geoclic_db < "$migration" 2>&1)
            MIGRATION_EXIT=$?

            if [ $MIGRATION_EXIT -ne 0 ] || echo "$MIGRATION_OUTPUT" | grep -qi "error"; then
                log_warn "    ⚠ Erreur possible dans $MIGRATION_NAME"
                echo "$MIGRATION_OUTPUT" | grep -i "error\|erreur" | head -3
                MIGRATION_ERRORS=$((MIGRATION_ERRORS + 1))
            fi
        fi
    done

    if [ $MIGRATION_ERRORS -gt 0 ]; then
        log_warn "$MIGRATION_ERRORS migration(s) avec des avertissements (peut être normal si déjà exécutées)"
    fi

    log_ok "Base de données initialisée"
else
    log_ok "Base de données déjà initialisée"

    # Vérifier et appliquer les nouvelles migrations même si la DB existe
    log_info "Vérification des migrations manquantes..."
    for migration in $(ls "$GEOCLIC_DIR/GeoClic_Suite/database/migrations/"*.sql 2>/dev/null | sort); do
        if [ -f "$migration" ]; then
            MIGRATION_NAME=$(basename "$migration")
            # Appliquer silencieusement (les IF NOT EXISTS éviteront les doublons)
            $DOCKER_COMPOSE exec -T db psql -U geoclic -d geoclic_db < "$migration" > /dev/null 2>&1 || true
        fi
    done
    log_ok "Migrations vérifiées"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 8 : CONFIGURATION FINALE
# ═══════════════════════════════════════════════════════════════════════════════
print_step "ÉTAPE 8/8 : Configuration finale"

# CRÉATION DU SERVICE SYSTEMD
# ═══════════════════════════════════════════════════════════════════════════════
# Déterminer le chemin de la commande docker compose pour systemd
if [[ "$DOCKER_COMPOSE" == "docker compose" ]]; then
    SYSTEMD_COMPOSE_START="/usr/bin/docker compose up -d"
    SYSTEMD_COMPOSE_STOP="/usr/bin/docker compose down"
else
    SYSTEMD_COMPOSE_START="/usr/bin/docker-compose up -d"
    SYSTEMD_COMPOSE_STOP="/usr/bin/docker-compose down"
fi

cat > /etc/systemd/system/geoclic.service << EOF
[Unit]
Description=GéoClic Suite
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${GEOCLIC_DIR}/GeoClic_Suite/deploy
ExecStart=${SYSTEMD_COMPOSE_START}
ExecStop=${SYSTEMD_COMPOSE_STOP}
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable geoclic.service

# ═══════════════════════════════════════════════════════════════════════════════
# SCRIPT DE SAUVEGARDE
# ═══════════════════════════════════════════════════════════════════════════════
mkdir -p /var/backups/geoclic

cat > "${GEOCLIC_DIR}/backup.sh" << 'BACKUP_SCRIPT'
#!/bin/bash
BACKUP_DIR="/var/backups/geoclic"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Sauvegarde base de données
docker exec geoclic_db pg_dump -U geoclic geoclic_db > "$BACKUP_DIR/geoclic_db_$DATE.sql"
gzip "$BACKUP_DIR/geoclic_db_$DATE.sql"

# Nettoyage des vieilles sauvegardes (garder 7 jours)
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete

echo "Sauvegarde terminée : $BACKUP_DIR/geoclic_db_$DATE.sql.gz"
BACKUP_SCRIPT

chmod +x "${GEOCLIC_DIR}/backup.sh"

# Ajouter au cron (sauvegarde quotidienne à 3h du matin)
(crontab -l 2>/dev/null | grep -v backup.sh; echo "0 3 * * * ${GEOCLIC_DIR}/backup.sh") | crontab -

# ═══════════════════════════════════════════════════════════════════════════════
# FIN DE L'INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                                                                               ${NC}"
echo -e "${GREEN}   ✓ INSTALLATION TERMINÉE AVEC SUCCÈS !                                      ${NC}"
echo -e "${GREEN}                                                                               ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Vos applications sont accessibles ici :${NC}"
echo ""
echo -e "   ${GREEN}●${NC} Portail Citoyen :     ${BLUE}https://${DOMAIN}${NC}"
echo -e "   ${GREEN}●${NC} Admin Patrimoine :    ${BLUE}https://${DOMAIN}/admin${NC}"
echo -e "   ${GREEN}●${NC} Gestion Demandes :    ${BLUE}https://${DOMAIN}/demandes${NC}"
echo -e "   ${GREEN}●${NC} Mobile PWA :          ${BLUE}https://${DOMAIN}/mobile${NC}"
echo -e "   ${GREEN}●${NC} Documentation API :   ${BLUE}https://${DOMAIN}/api/docs${NC}"
echo ""
echo -e "${CYAN}Identifiants par défaut :${NC}"
echo ""
echo -e "   Email :     ${YELLOW}admin@geoclic.local${NC}"
echo -e "   Mot de passe : ${YELLOW}admin123${NC}"
echo ""
echo -e "${RED}⚠ IMPORTANT : Changez ce mot de passe après la première connexion !${NC}"
echo ""
echo -e "${CYAN}Commandes utiles :${NC}"
echo ""
echo -e "   Voir l'état :    ${YELLOW}cd ${GEOCLIC_DIR}/GeoClic_Suite/deploy && $DOCKER_COMPOSE ps${NC}"
echo -e "   Voir les logs :  ${YELLOW}cd ${GEOCLIC_DIR}/GeoClic_Suite/deploy && $DOCKER_COMPOSE logs -f${NC}"
echo -e "   Redémarrer :     ${YELLOW}sudo systemctl restart geoclic${NC}"
echo -e "   Sauvegarde :     ${YELLOW}sudo ${GEOCLIC_DIR}/backup.sh${NC}"
echo ""
echo -e "${CYAN}Configuration :${NC}"
echo ""
echo -e "   Fichier .env :   ${YELLOW}${GEOCLIC_DIR}/GeoClic_Suite/deploy/.env${NC}"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

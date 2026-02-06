#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# GéoClic Fleet Manager - Outil centralisé de gestion multi-serveurs
# ═══════════════════════════════════════════════════════════════════════════════
#
# Le code est poussé directement depuis cette machine vers les serveurs
# clients via rsync (pas de dépendance GitHub sur les serveurs).
#
# Commandes:
#   provision   Installer GéoClic sur un VPS vierge
#   update      Mettre à jour un ou tous les serveurs
#   status      Vérifier l'état d'un ou tous les serveurs
#   dashboard   Monitoring en temps réel (rafraîchissement auto)
#   list        Lister les clients enregistrés
#   add         Enregistrer un client existant
#   remove      Retirer un client du registre
#   ssh         Se connecter en SSH à un client
#   logs        Voir les logs d'un client
#   backup      Déclencher une sauvegarde sur un client
#
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────────
FLEET_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$FLEET_DIR/.." && pwd)"
CLIENTS_FILE="$FLEET_DIR/clients.conf"
GEOCLIC_REMOTE_DIR="/opt/geoclic"
GEOCLIC_VERSION="14.5"
SSH_TIMEOUT=10
HEALTH_TIMEOUT=5

# Fichiers/dossiers exclus du rsync (pas besoin sur le serveur)
RSYNC_EXCLUDES=(
    "node_modules"
    ".git"
    ".github"
    "backups/"
    "deploy/nginx/ssl/"
    "deploy/nginx/logs/"
    "deploy/logs/"
    "deploy/.env"
    "fleet/clients.conf"
    "*.log"
    ".DS_Store"
    "__pycache__"
    ".vscode"
    ".idea"
)

# ─── Couleurs ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

log_ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
log_info()  { echo -e "  ${BLUE}→${NC} $1"; }
log_warn()  { echo -e "  ${YELLOW}!${NC} $1"; }
log_error() { echo -e "  ${RED}✗${NC} $1"; }
log_step()  { echo -e "\n${CYAN}━━━ $1 ━━━${NC}\n"; }

die() {
    log_error "$1"
    exit 1
}

get_client() {
    local name="$1"
    grep -v '^#' "$CLIENTS_FILE" 2>/dev/null | grep -v '^$' | grep "^${name}|" | head -1
}

parse_client() {
    local line="$1"
    CLIENT_NAME=$(echo "$line" | cut -d'|' -f1)
    CLIENT_DOMAIN=$(echo "$line" | cut -d'|' -f2)
    CLIENT_IP=$(echo "$line" | cut -d'|' -f3)
    CLIENT_SSH_USER=$(echo "$line" | cut -d'|' -f4)
    CLIENT_SSH_PORT=$(echo "$line" | cut -d'|' -f5)
    CLIENT_BRANCH=$(echo "$line" | cut -d'|' -f6)
    CLIENT_DATE=$(echo "$line" | cut -d'|' -f7)
}

list_clients() {
    grep -v '^#' "$CLIENTS_FILE" 2>/dev/null | grep -v '^$' || true
}

ssh_cmd() {
    local ip="$1" user="$2" port="$3"
    shift 3
    ssh -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=$SSH_TIMEOUT \
        -o BatchMode=yes \
        -p "$port" "${user}@${ip}" "$@"
}

# Retourne "sudo" si l'utilisateur n'est pas root, "" sinon
get_sudo() {
    local user="$1"
    if [[ "$user" != "root" ]]; then echo "sudo"; else echo ""; fi
}

# Synchronise le code local vers un serveur distant via rsync
sync_code() {
    local ip="$1" user="$2" port="$3"
    local SUDO=$(get_sudo "$user")

    # Construire les arguments --exclude
    local exclude_args=()
    for excl in "${RSYNC_EXCLUDES[@]}"; do
        exclude_args+=("--exclude=$excl")
    done

    # Si non-root, rsync doit utiliser sudo sur le serveur distant
    local rsync_path_arg=""
    if [[ -n "$SUDO" ]]; then
        rsync_path_arg="--rsync-path=sudo rsync"
    fi

    rsync -az --delete \
        "${exclude_args[@]}" \
        ${rsync_path_arg:+"$rsync_path_arg"} \
        -e "ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=$SSH_TIMEOUT -p $port" \
        "$PROJECT_ROOT/" \
        "${user}@${ip}:${GEOCLIC_REMOTE_DIR}/"
}

print_banner() {
    echo -e "${BOLD}${CYAN}"
    echo "  ╔═══════════════════════════════════════════════════╗"
    echo "  ║          GéoClic Fleet Manager v${GEOCLIC_VERSION}           ║"
    echo "  ╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: provision
# ═══════════════════════════════════════════════════════════════════════════════
cmd_provision() {
    local name="" domain="" ip="" email="" ssh_user="root" ssh_port="22"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --name)     name="$2"; shift 2 ;;
            --domain)   domain="$2"; shift 2 ;;
            --ip)       ip="$2"; shift 2 ;;
            --email)    email="$2"; shift 2 ;;
            --ssh-user) ssh_user="$2"; shift 2 ;;
            --ssh-port) ssh_port="$2"; shift 2 ;;
            *) die "Option inconnue: $1" ;;
        esac
    done

    [[ -z "$name" ]]   && die "--name requis (ex: ville-lyon)"
    [[ -z "$domain" ]] && die "--domain requis (ex: lyon.geoclic.fr)"
    [[ -z "$ip" ]]     && die "--ip requis (ex: 51.210.42.100)"
    [[ -z "$email" ]]  && die "--email requis (ex: admin@lyon.fr)"

    if [[ -n "$(get_client "$name" 2>/dev/null)" ]]; then
        die "Le client '$name' existe déjà dans le registre"
    fi

    local SUDO=$(get_sudo "$ssh_user")

    print_banner
    echo -e "${BOLD}Provisioning: ${CYAN}$name${NC}"
    echo -e "  Domaine:  $domain"
    echo -e "  IP:       $ip"
    echo -e "  User SSH: $ssh_user ${SUDO:+(avec sudo)}"
    echo -e "  Email:    $email"
    echo -e "  Source:   $PROJECT_ROOT"
    echo ""

    # ─── 1. Test SSH ──────────────────────────────────────────────────────────
    log_step "1/7 - Test de connectivité SSH"
    if ! ssh_cmd "$ip" "$ssh_user" "$ssh_port" "echo ok" > /dev/null 2>&1; then
        die "Impossible de se connecter à ${ssh_user}@${ip}:${ssh_port}
  Vérifiez:
  - Que le VPS est allumé
  - Que votre clé SSH est autorisée: ssh-copy-id -p ${ssh_port} ${ssh_user}@${ip}
  - Que le port SSH (${ssh_port}) est ouvert"
    fi
    log_ok "Connexion SSH OK"

    # Vérifier que sudo fonctionne sans mot de passe (pour les utilisateurs non-root)
    if [[ -n "$SUDO" ]]; then
        if ! ssh_cmd "$ip" "$ssh_user" "$ssh_port" "sudo -n true" > /dev/null 2>&1; then
            die "L'utilisateur '$ssh_user' ne peut pas utiliser sudo sans mot de passe.
  Connectez-vous au serveur et exécutez:
    echo '${ssh_user} ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/${ssh_user}"
        fi
        log_ok "sudo sans mot de passe OK"
    fi

    # ─── 2. Mise à jour système ───────────────────────────────────────────────
    log_step "2/7 - Mise à jour du système"
    ssh_cmd "$ip" "$ssh_user" "$ssh_port" "
        export DEBIAN_FRONTEND=noninteractive
        $SUDO apt-get update -qq
        $SUDO apt-get upgrade -y -qq
    "
    log_ok "Système mis à jour"

    # ─── 3. Installation Docker + outils ──────────────────────────────────────
    log_step "3/7 - Installation de Docker"
    ssh_cmd "$ip" "$ssh_user" "$ssh_port" "
        SUDO='$SUDO'
        if command -v docker &> /dev/null; then
            echo 'Docker déjà installé'
        else
            \$SUDO apt-get install -y -qq ca-certificates curl gnupg lsb-release
            \$SUDO install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \$SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            \$SUDO chmod a+r /etc/apt/keyrings/docker.gpg
            echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo \"\$VERSION_CODENAME\") stable\" | \$SUDO tee /etc/apt/sources.list.d/docker.list > /dev/null
            \$SUDO apt-get update -qq
            \$SUDO apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            \$SUDO systemctl start docker
            \$SUDO systemctl enable docker
            # Ajouter l'utilisateur au groupe docker
            \$SUDO usermod -aG docker \$(whoami) 2>/dev/null || true
        fi
        \$SUDO apt-get install -y -qq certbot rsync
    "
    log_ok "Docker installé"

    # ─── 4. Envoi du code via rsync ──────────────────────────────────────────
    log_step "4/7 - Envoi du code source (rsync)"
    ssh_cmd "$ip" "$ssh_user" "$ssh_port" "$SUDO mkdir -p '${GEOCLIC_REMOTE_DIR}' && $SUDO chown \$(whoami):\$(whoami) '${GEOCLIC_REMOTE_DIR}'"
    log_info "Synchronisation de ${PROJECT_ROOT} vers ${ssh_user}@${ip}:${GEOCLIC_REMOTE_DIR}/ ..."
    sync_code "$ip" "$ssh_user" "$ssh_port"
    ssh_cmd "$ip" "$ssh_user" "$ssh_port" "
        SUDO='$SUDO'
        mkdir -p '${GEOCLIC_REMOTE_DIR}/backups'
        mkdir -p '${GEOCLIC_REMOTE_DIR}/deploy/logs'
        mkdir -p '${GEOCLIC_REMOTE_DIR}/deploy/nginx/ssl'
        mkdir -p '${GEOCLIC_REMOTE_DIR}/deploy/nginx/logs'
        chmod +x '${GEOCLIC_REMOTE_DIR}/scripts/'*.sh 2>/dev/null || true
    "
    log_ok "Code déployé dans ${GEOCLIC_REMOTE_DIR}"

    # ─── 5. Configuration .env ────────────────────────────────────────────────
    log_step "5/7 - Configuration (.env + secrets)"
    ssh_cmd "$ip" "$ssh_user" "$ssh_port" "
        cd '${GEOCLIC_REMOTE_DIR}/deploy'

        if [ -f .env ]; then
            echo '.env existe déjà, conservé'
        else
            DB_PWD=\$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
            JWT_KEY=\$(openssl rand -base64 64 | tr -dc 'a-zA-Z0-9' | head -c 48)

            cat > .env << ENVEOF
# GéoClic Suite - ${name}
# Domaine: ${domain}
# Généré le: \$(date '+%Y-%m-%d %H:%M:%S')

DB_USER=geoclic
DB_PASSWORD=\${DB_PWD}
DB_NAME=geoclic_db
DB_PORT=5432

JWT_SECRET_KEY=\${JWT_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
API_PORT=8000
APP_ENV=production
DEBUG=false

API_PUBLIC_URL=https://${domain}
CORS_ORIGINS=https://${domain},https://www.${domain}

ADMIN_PORT=3000
PORTAIL_PORT=5174
DEMANDES_PORT=5175
MOBILE_PORT=5176
SIG_PORT=5177
SERVICES_PORT=5178
TERRAIN_PORT=5180

PHOTO_MAX_SIZE=10
ENVEOF
            chmod 600 .env
        fi

        # Marqueur fleet
        cat > '${GEOCLIC_REMOTE_DIR}/.geoclic-meta' << METAEOF
CLIENT_NAME=${name}
DOMAIN=${domain}
VERSION=${GEOCLIC_VERSION}
INSTALLED=\$(date '+%Y-%m-%d %H:%M:%S')
LAST_UPDATE=\$(date '+%Y-%m-%d %H:%M:%S')
METAEOF
    "
    log_ok "Configuration générée"

    # ─── 6. SSL + Build Docker ────────────────────────────────────────────────
    log_step "6/7 - Certificat SSL + build Docker"

    ssh_cmd "$ip" "$ssh_user" "$ssh_port" "
        SUDO='$SUDO'
        # SSL
        \$SUDO systemctl stop nginx 2>/dev/null || true

        \$SUDO certbot certonly --standalone \
            -d '${domain}' \
            --non-interactive --agree-tos --email '${email}' 2>&1 || {
            echo 'WARN: Certificat SSL non obtenu'
        }

        SSL_DIR='${GEOCLIC_REMOTE_DIR}/deploy/nginx/ssl'
        if [ -f '/etc/letsencrypt/live/${domain}/fullchain.pem' ]; then
            \$SUDO cp /etc/letsencrypt/live/${domain}/fullchain.pem \"\$SSL_DIR/fullchain.pem\"
            \$SUDO cp /etc/letsencrypt/live/${domain}/privkey.pem \"\$SSL_DIR/privkey.pem\"
            \$SUDO chmod 600 \"\$SSL_DIR/privkey.pem\"
            \$SUDO chown \$(whoami):\$(whoami) \"\$SSL_DIR\"/*
        else
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout \"\$SSL_DIR/privkey.pem\" \
                -out \"\$SSL_DIR/fullchain.pem\" \
                -subj '/CN=${domain}' 2>/dev/null
        fi

        # Hook de renouvellement SSL
        \$SUDO mkdir -p /etc/letsencrypt/renewal-hooks/deploy
        \$SUDO tee /etc/letsencrypt/renewal-hooks/deploy/geoclic-ssl.sh > /dev/null << 'HOOKEOF'
#!/bin/bash
cp /etc/letsencrypt/live/${domain}/fullchain.pem ${GEOCLIC_REMOTE_DIR}/deploy/nginx/ssl/fullchain.pem
cp /etc/letsencrypt/live/${domain}/privkey.pem ${GEOCLIC_REMOTE_DIR}/deploy/nginx/ssl/privkey.pem
chmod 600 ${GEOCLIC_REMOTE_DIR}/deploy/nginx/ssl/privkey.pem
cd ${GEOCLIC_REMOTE_DIR}/deploy && docker compose restart nginx 2>/dev/null || true
HOOKEOF
        \$SUDO chmod +x /etc/letsencrypt/renewal-hooks/deploy/geoclic-ssl.sh
        \$SUDO systemctl enable certbot.timer 2>/dev/null || true
        \$SUDO systemctl start certbot.timer 2>/dev/null || true
    "
    log_ok "SSL configuré"

    log_info "Build Docker (peut prendre 5-10 min)..."
    ssh_cmd "$ip" "$ssh_user" "$ssh_port" "
        SUDO='$SUDO'
        cd '${GEOCLIC_REMOTE_DIR}/deploy'
        \$SUDO docker compose build 2>&1
        \$SUDO docker compose up -d 2>&1
    " | while IFS= read -r l; do echo -e "    ${DIM}$l${NC}"; done
    log_ok "Conteneurs démarrés"

    # ─── 7. Init DB + cron + systemd ─────────────────────────────────────────
    log_step "7/7 - Base de données + services système"
    ssh_cmd "$ip" "$ssh_user" "$ssh_port" "
        SUDO='$SUDO'
        cd '${GEOCLIC_REMOTE_DIR}/deploy'

        # Attendre PostgreSQL
        for i in \$(seq 1 30); do
            \$SUDO docker compose exec -T db pg_isready -U geoclic -d geoclic_db > /dev/null 2>&1 && break
            sleep 2
        done

        # Init DB si nécessaire
        TABLES=\$(\$SUDO docker compose exec -T db psql -U geoclic -d geoclic_db -tAc \
            \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';\" 2>/dev/null || echo '0')

        if [ \"\$TABLES\" -lt 5 ]; then
            \$SUDO docker compose exec -T db psql -U geoclic -d geoclic_db \
                < '${GEOCLIC_REMOTE_DIR}/database/init_v12_pro.sql' 2>/dev/null || true

            for migration in \$(ls '${GEOCLIC_REMOTE_DIR}/database/migrations/'*.sql 2>/dev/null | sort); do
                echo \"  Migration: \$(basename \$migration)\"
                \$SUDO docker compose exec -T db psql -U geoclic -d geoclic_db < \"\$migration\" 2>/dev/null || true
            done
        fi

        # Cron
        (crontab -l 2>/dev/null | grep -v geoclic; echo '0 2 * * * $SUDO ${GEOCLIC_REMOTE_DIR}/scripts/backup_db.sh >> /var/log/geoclic_backup.log 2>&1'; echo '*/5 * * * * ${GEOCLIC_REMOTE_DIR}/scripts/monitor.sh > /dev/null 2>&1') | crontab -

        # Systemd
        \$SUDO tee /etc/systemd/system/geoclic.service > /dev/null << 'SVCEOF'
[Unit]
Description=GéoClic Suite
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${GEOCLIC_REMOTE_DIR}/deploy
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
SVCEOF
        \$SUDO systemctl daemon-reload
        \$SUDO systemctl enable geoclic.service
    "
    log_ok "Base de données, cron et systemd configurés"

    # ─── Enregistrement ──────────────────────────────────────────────────────
    echo "${name}|${domain}|${ip}|${ssh_user}|${ssh_port}|rsync|$(date '+%Y-%m-%d')" >> "$CLIENTS_FILE"

    # ─── Résumé ──────────────────────────────────────────────────────────────
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Installation terminée: ${BOLD}${name}${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  Portail citoyen:    ${BLUE}https://${domain}${NC}"
    echo -e "  Admin (Data):       ${BLUE}https://${domain}/admin${NC}"
    echo -e "  Back-office:        ${BLUE}https://${domain}/demandes${NC}"
    echo -e "  SIG:                ${BLUE}https://${domain}/sig${NC}"
    echo -e "  Services terrain:   ${BLUE}https://${domain}/services${NC}"
    echo -e "  Terrain PWA:        ${BLUE}https://${domain}/terrain${NC}"
    echo -e "  Mobile PWA:         ${BLUE}https://${domain}/mobile${NC}"
    echo -e "  API docs:           ${BLUE}https://${domain}/api/docs${NC}"
    echo ""
    echo -e "  Login:  ${YELLOW}admin@geoclic.local${NC} / ${YELLOW}admin123${NC}"
    echo -e "  ${RED}Changez ce mot de passe immédiatement !${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: update
# ═══════════════════════════════════════════════════════════════════════════════
cmd_update() {
    local client_name="" all=false services=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --client)   client_name="$2"; shift 2 ;;
            --all)      all=true; shift ;;
            --services) services="$2"; shift 2 ;;
            *) die "Option inconnue: $1" ;;
        esac
    done

    if [[ "$all" == false && -z "$client_name" ]]; then
        die "Spécifiez --client <nom> ou --all"
    fi

    print_banner

    local clients_to_update=""
    if [[ "$all" == true ]]; then
        clients_to_update=$(list_clients)
        [[ -z "$clients_to_update" ]] && die "Aucun client enregistré"
        local count
        count=$(echo "$clients_to_update" | wc -l)
        echo -e "${BOLD}Mise à jour de ${count} serveur(s) depuis ${PROJECT_ROOT}${NC}\n"
    else
        clients_to_update=$(get_client "$client_name")
        [[ -z "$clients_to_update" ]] && die "Client '$client_name' non trouvé"
        echo -e "${BOLD}Mise à jour de: ${CYAN}${client_name}${NC}\n"
    fi

    local success=0 fail=0

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        parse_client "$line"

        echo -e "\n${CYAN}━━━ ${CLIENT_NAME} (${CLIENT_DOMAIN}) ━━━${NC}"

        # Test SSH
        if ! ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" "echo ok" > /dev/null 2>&1; then
            log_error "Connexion SSH impossible"
            fail=$((fail + 1))
            continue
        fi

        local SUDO=$(get_sudo "$CLIENT_SSH_USER")

        # Backup avant mise à jour
        log_info "Backup rapide de la DB..."
        ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" "
            SUDO='$SUDO'
            mkdir -p '${GEOCLIC_REMOTE_DIR}/backups'
            \$SUDO docker exec geoclic_db pg_dump -U geoclic geoclic_db 2>/dev/null | gzip > '${GEOCLIC_REMOTE_DIR}/backups/pre_update_\$(date +%Y%m%d_%H%M%S).sql.gz'
        " > /dev/null 2>&1 || true
        log_ok "Backup pré-update créé"

        # Rsync du code
        log_info "Envoi du code (rsync)..."
        if sync_code "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" > /dev/null 2>&1; then
            log_ok "Code synchronisé"
        else
            log_error "Échec du rsync"
            fail=$((fail + 1))
            continue
        fi

        # Rétablir les permissions des scripts
        ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" "
            chmod +x '${GEOCLIC_REMOTE_DIR}/scripts/'*.sh 2>/dev/null || true
        " > /dev/null 2>&1

        # Appliquer les migrations
        log_info "Migrations SQL..."
        ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" "
            SUDO='$SUDO'
            cd '${GEOCLIC_REMOTE_DIR}/deploy'
            for migration in \$(ls '${GEOCLIC_REMOTE_DIR}/database/migrations/'*.sql 2>/dev/null | sort); do
                \$SUDO docker compose exec -T db psql -U geoclic -d geoclic_db < \"\$migration\" 2>/dev/null || true
            done
        " > /dev/null 2>&1
        log_ok "Migrations appliquées"

        # Rebuild
        local build_targets="${services:-api admin portail demandes sig services terrain mobile}"
        log_info "Rebuild Docker: $build_targets..."
        if ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" "
            SUDO='$SUDO'
            cd '${GEOCLIC_REMOTE_DIR}/deploy'
            \$SUDO docker compose build --no-cache $build_targets 2>&1
            \$SUDO docker compose up -d 2>&1
            \$SUDO docker image prune -f > /dev/null 2>&1
        " > /dev/null 2>&1; then
            log_ok "Conteneurs reconstruits et redémarrés"
        else
            log_error "Échec du rebuild"
            fail=$((fail + 1))
            continue
        fi

        # Mettre à jour le marqueur
        ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" "
            if [ -f '${GEOCLIC_REMOTE_DIR}/.geoclic-meta' ]; then
                sed -i \"s/^LAST_UPDATE=.*/LAST_UPDATE=\$(date '+%Y-%m-%d %H:%M:%S')/\" '${GEOCLIC_REMOTE_DIR}/.geoclic-meta'
                sed -i \"s/^VERSION=.*/VERSION=${GEOCLIC_VERSION}/\" '${GEOCLIC_REMOTE_DIR}/.geoclic-meta'
            fi
        " > /dev/null 2>&1

        # Health check
        log_info "Vérification de santé..."
        sleep 10
        local http_code
        http_code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time $HEALTH_TIMEOUT "https://${CLIENT_DOMAIN}/api/health" 2>/dev/null || echo "000")
        if [[ "$http_code" == "200" ]]; then
            log_ok "API en ligne (HTTP 200)"
        else
            log_warn "API HTTP $http_code - le démarrage peut prendre du temps"
        fi
        success=$((success + 1))

    done <<< "$clients_to_update"

    echo ""
    echo -e "${BOLD}Résumé:${NC} ${GREEN}$success OK${NC} / ${RED}$fail échec(s)${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: status
# ═══════════════════════════════════════════════════════════════════════════════
cmd_status() {
    local client_name="" all=false detailed=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --client)   client_name="$2"; shift 2 ;;
            --all)      all=true; shift ;;
            --detailed) detailed=true; shift ;;
            *) die "Option inconnue: $1" ;;
        esac
    done

    [[ "$all" == false && -z "$client_name" ]] && all=true

    local clients=""
    if [[ "$all" == true ]]; then
        clients=$(list_clients)
    else
        clients=$(get_client "$client_name")
        [[ -z "$clients" ]] && die "Client '$client_name' non trouvé"
    fi

    [[ -z "$clients" ]] && die "Aucun client enregistré"

    print_banner

    printf "${BOLD}%-18s %-28s %-8s %-10s %-12s${NC}\n" "CLIENT" "DOMAINE" "API" "SSL" "CONTAINERS"
    printf "%-18s %-28s %-8s %-10s %-12s\n" "──────────────────" "────────────────────────────" "────────" "──────────" "────────────"

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        parse_client "$line"

        # API health
        local api_status api_color
        local http_code
        http_code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time $HEALTH_TIMEOUT "https://${CLIENT_DOMAIN}/api/health" 2>/dev/null || echo "000")

        if [[ "$http_code" == "200" ]]; then
            api_status="OK"; api_color="$GREEN"
        elif [[ "$http_code" == "000" ]]; then
            api_status="DOWN"; api_color="$RED"
        else
            api_status="HTTP$http_code"; api_color="$YELLOW"
        fi

        # SSL expiry
        local ssl_status ssl_color
        local ssl_expiry
        ssl_expiry=$(echo | openssl s_client -connect "${CLIENT_DOMAIN}:443" -servername "${CLIENT_DOMAIN}" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
        if [[ -n "$ssl_expiry" ]]; then
            local expiry_epoch now_epoch days_left
            expiry_epoch=$(date -d "$ssl_expiry" +%s 2>/dev/null || echo "0")
            now_epoch=$(date +%s)
            days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
            if [[ $days_left -gt 30 ]]; then
                ssl_status="${days_left}j"; ssl_color="$GREEN"
            elif [[ $days_left -gt 7 ]]; then
                ssl_status="${days_left}j"; ssl_color="$YELLOW"
            else
                ssl_status="${days_left}j!"; ssl_color="$RED"
            fi
        else
            ssl_status="N/A"; ssl_color="$DIM"
        fi

        # Containers (SSH, si --detailed)
        local containers_status containers_color
        if [[ "$detailed" == true ]]; then
            local SUDO=$(get_sudo "$CLIENT_SSH_USER")
            local running
            running=$(ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" \
                "cd '${GEOCLIC_REMOTE_DIR}/deploy' && $SUDO docker compose ps --format '{{.State}}' 2>/dev/null | grep -c running" 2>/dev/null || echo "?")
            containers_status="${running}/10"
            if [[ "$running" == "10" ]]; then containers_color="$GREEN"
            elif [[ "$running" == "?" ]]; then containers_color="$DIM"; containers_status="SSH fail"
            else containers_color="$YELLOW"
            fi
        else
            containers_status="-"; containers_color="$DIM"
        fi

        printf "%-18s %-28s ${api_color}%-8s${NC} ${ssl_color}%-10s${NC} ${containers_color}%-12s${NC}\n" \
            "$CLIENT_NAME" "$CLIENT_DOMAIN" "$api_status" "$ssl_status" "$containers_status"

    done <<< "$clients"

    echo ""
    [[ "$detailed" == false ]] && echo -e "${DIM}Astuce: --detailed pour voir les conteneurs (via SSH)${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: dashboard
# ═══════════════════════════════════════════════════════════════════════════════
cmd_dashboard() {
    local interval=30

    while [[ $# -gt 0 ]]; do
        case $1 in
            --interval) interval="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    local clients
    clients=$(list_clients)
    [[ -z "$clients" ]] && die "Aucun client enregistré"

    while true; do
        clear

        echo -e "${BOLD}${CYAN}"
        echo "  ╔═════════════════════════════════════════════════════════════════╗"
        echo "  ║              GéoClic Fleet Dashboard                            ║"
        echo "  ║              $(date '+%Y-%m-%d %H:%M:%S')                                  ║"
        echo "  ╚═════════════════════════════════════════════════════════════════╝"
        echo -e "${NC}"

        local total=0 up=0 down=0 warn=0

        printf "  ${BOLD}%-3s %-16s %-24s %-8s %-10s %-8s${NC}\n" "#" "CLIENT" "DOMAINE" "STATUT" "LATENCE" "SSL"
        printf "  %-3s %-16s %-24s %-8s %-10s %-8s\n" "───" "────────────────" "────────────────────────" "────────" "──────────" "────────"

        local idx=0
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            parse_client "$line"
            idx=$((idx + 1))
            total=$((total + 1))

            # API + latence
            local start_time end_time latency_str http_code status_icon status_color
            start_time=$(date +%s%N 2>/dev/null || date +%s)
            http_code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time $HEALTH_TIMEOUT "https://${CLIENT_DOMAIN}/api/health" 2>/dev/null || echo "000")
            end_time=$(date +%s%N 2>/dev/null || date +%s)

            if [[ ${#start_time} -gt 10 ]]; then
                local latency_ms=$(( (end_time - start_time) / 1000000 ))
                latency_str="${latency_ms}ms"
            else
                latency_str="-"
            fi

            if [[ "$http_code" == "200" ]]; then
                status_icon="● OK"; status_color="$GREEN"; up=$((up + 1))
            elif [[ "$http_code" == "000" ]]; then
                status_icon="● DOWN"; status_color="$RED"; down=$((down + 1)); latency_str="-"
            else
                status_icon="● WARN"; status_color="$YELLOW"; warn=$((warn + 1))
            fi

            # SSL
            local ssl_info
            local ssl_exp
            ssl_exp=$(echo | openssl s_client -connect "${CLIENT_DOMAIN}:443" -servername "${CLIENT_DOMAIN}" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
            if [[ -n "$ssl_exp" ]]; then
                local exp_epoch now_epoch days_left
                exp_epoch=$(date -d "$ssl_exp" +%s 2>/dev/null || echo "0")
                now_epoch=$(date +%s)
                days_left=$(( (exp_epoch - now_epoch) / 86400 ))
                if [[ $days_left -gt 30 ]]; then ssl_info="${GREEN}${days_left}j${NC}"
                elif [[ $days_left -gt 7 ]]; then ssl_info="${YELLOW}${days_left}j${NC}"
                else ssl_info="${RED}${days_left}j!${NC}"
                fi
            else
                ssl_info="${DIM}N/A${NC}"
            fi

            printf "  %-3s %-16s %-24s ${status_color}%-8s${NC} %-10s " \
                "$idx" "$CLIENT_NAME" "$CLIENT_DOMAIN" "$status_icon" "$latency_str"
            echo -e "$ssl_info"

        done <<< "$clients"

        echo ""
        echo -e "  ─────────────────────────────────────────────────────────────────"
        printf "  ${BOLD}Total: %d${NC}  │  ${GREEN}En ligne: %d${NC}  │  ${RED}Hors ligne: %d${NC}  │  ${YELLOW}Warn: %d${NC}\n" \
            "$total" "$up" "$down" "$warn"
        echo -e "  ─────────────────────────────────────────────────────────────────"
        echo ""
        echo -e "  ${DIM}Rafraîchissement: ${interval}s - Ctrl+C pour quitter${NC}"

        sleep "$interval"
    done
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: list
# ═══════════════════════════════════════════════════════════════════════════════
cmd_list() {
    local clients
    clients=$(list_clients)

    if [[ -z "$clients" ]]; then
        echo "Aucun client enregistré."
        echo ""
        echo "Pour installer un nouveau client:"
        echo "  ./geoclic-fleet.sh provision --name ville-x --domain ville-x.fr --ip 1.2.3.4 --email admin@ville-x.fr"
        echo ""
        echo "Pour enregistrer un serveur existant:"
        echo "  ./geoclic-fleet.sh add --name ville-x --domain ville-x.fr --ip 1.2.3.4"
        return
    fi

    print_banner

    printf "${BOLD}%-18s %-28s %-16s %-6s %-12s${NC}\n" "NOM" "DOMAINE" "IP" "PORT" "AJOUTÉ LE"
    printf "%-18s %-28s %-16s %-6s %-12s\n" "──────────────────" "────────────────────────────" "────────────────" "──────" "────────────"

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        parse_client "$line"
        printf "%-18s %-28s %-16s %-6s %-12s\n" \
            "$CLIENT_NAME" "$CLIENT_DOMAIN" "$CLIENT_IP" "$CLIENT_SSH_PORT" "$CLIENT_DATE"
    done <<< "$clients"

    local count
    count=$(echo "$clients" | wc -l)
    echo -e "\n${DIM}$count client(s) enregistré(s)${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: add
# ═══════════════════════════════════════════════════════════════════════════════
cmd_add() {
    local name="" domain="" ip="" ssh_user="root" ssh_port="22"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --name)     name="$2"; shift 2 ;;
            --domain)   domain="$2"; shift 2 ;;
            --ip)       ip="$2"; shift 2 ;;
            --ssh-user) ssh_user="$2"; shift 2 ;;
            --ssh-port) ssh_port="$2"; shift 2 ;;
            *) die "Option inconnue: $1" ;;
        esac
    done

    [[ -z "$name" ]]   && die "--name requis"
    [[ -z "$domain" ]] && die "--domain requis"
    [[ -z "$ip" ]]     && die "--ip requis"

    [[ -n "$(get_client "$name" 2>/dev/null)" ]] && die "Le client '$name' existe déjà"

    echo "${name}|${domain}|${ip}|${ssh_user}|${ssh_port}|rsync|$(date '+%Y-%m-%d')" >> "$CLIENTS_FILE"
    log_ok "Client '$name' enregistré"
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: remove
# ═══════════════════════════════════════════════════════════════════════════════
cmd_remove() {
    local name=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --name|--client) name="$2"; shift 2 ;;
            *) die "Option inconnue: $1" ;;
        esac
    done

    [[ -z "$name" ]] && die "--name requis"
    [[ -z "$(get_client "$name" 2>/dev/null)" ]] && die "Client '$name' non trouvé"

    local tmp; tmp=$(mktemp)
    grep -v "^${name}|" "$CLIENTS_FILE" > "$tmp"
    mv "$tmp" "$CLIENTS_FILE"

    log_ok "Client '$name' retiré du registre"
    log_warn "Le serveur n'a pas été désinstallé"
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: ssh
# ═══════════════════════════════════════════════════════════════════════════════
cmd_ssh() {
    local client_name="${1:-}"
    [[ -z "$client_name" ]] && die "Usage: geoclic-fleet.sh ssh <nom-client>"

    local client_line
    client_line=$(get_client "$client_name")
    [[ -z "$client_line" ]] && die "Client '$client_name' non trouvé"

    parse_client "$client_line"
    echo -e "Connexion à ${CYAN}${CLIENT_NAME}${NC} (${CLIENT_IP})..."
    exec ssh -p "$CLIENT_SSH_PORT" "${CLIENT_SSH_USER}@${CLIENT_IP}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: logs
# ═══════════════════════════════════════════════════════════════════════════════
cmd_logs() {
    local client_name="" service="api" lines=50

    while [[ $# -gt 0 ]]; do
        case $1 in
            --client)  client_name="$2"; shift 2 ;;
            --service) service="$2"; shift 2 ;;
            --lines)   lines="$2"; shift 2 ;;
            *) client_name="$1"; shift ;;
        esac
    done

    [[ -z "$client_name" ]] && die "Usage: geoclic-fleet.sh logs <nom> [--service api] [--lines 50]"

    local client_line
    client_line=$(get_client "$client_name")
    [[ -z "$client_line" ]] && die "Client '$client_name' non trouvé"

    parse_client "$client_line"
    local SUDO=$(get_sudo "$CLIENT_SSH_USER")
    echo -e "Logs ${CYAN}${CLIENT_NAME}${NC} / ${service} (${lines} lignes)"
    echo ""
    ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" \
        "cd '${GEOCLIC_REMOTE_DIR}/deploy' && $SUDO docker compose logs --tail=$lines $service"
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: backup
# ═══════════════════════════════════════════════════════════════════════════════
cmd_backup() {
    local client_name="" all=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --client) client_name="$2"; shift 2 ;;
            --all)    all=true; shift ;;
            *) die "Option inconnue: $1" ;;
        esac
    done

    [[ "$all" == false && -z "$client_name" ]] && die "Spécifiez --client <nom> ou --all"

    local clients=""
    if [[ "$all" == true ]]; then clients=$(list_clients)
    else
        clients=$(get_client "$client_name")
        [[ -z "$clients" ]] && die "Client '$client_name' non trouvé"
    fi

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        parse_client "$line"

        echo -e "${CYAN}━━━ Backup: ${CLIENT_NAME} ━━━${NC}"

        if ! ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" "echo ok" > /dev/null 2>&1; then
            log_error "Connexion SSH impossible"
            continue
        fi

        local SUDO=$(get_sudo "$CLIENT_SSH_USER")
        ssh_cmd "$CLIENT_IP" "$CLIENT_SSH_USER" "$CLIENT_SSH_PORT" "
            SUDO='$SUDO'
            if [ -x '${GEOCLIC_REMOTE_DIR}/scripts/backup_db.sh' ]; then
                \$SUDO '${GEOCLIC_REMOTE_DIR}/scripts/backup_db.sh'
            else
                mkdir -p '${GEOCLIC_REMOTE_DIR}/backups'
                \$SUDO docker exec geoclic_db pg_dump -U geoclic geoclic_db | gzip > '${GEOCLIC_REMOTE_DIR}/backups/geoclic_backup_\$(date +%Y%m%d_%H%M%S).sql.gz'
            fi
        "
        log_ok "Backup terminé sur ${CLIENT_NAME}"
    done <<< "$clients"
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDE: help
# ═══════════════════════════════════════════════════════════════════════════════
cmd_help() {
    print_banner
    cat << 'HELP'
COMMANDES:

  provision   Installer GéoClic sur un VPS vierge (Ubuntu)
              --name        Nom du client (ex: ville-lyon)
              --domain      Domaine (ex: lyon.geoclic.fr)
              --ip          Adresse IP du VPS
              --email       Email pour Let's Encrypt
              --ssh-user    Utilisateur SSH (défaut: root)
              --ssh-port    Port SSH (défaut: 22)

  update      Mettre à jour un ou tous les serveurs
              --client      Nom du client
              --all         Tous les clients
              --services    Services à rebuild (ex: "api portail")

  status      État des serveurs (API + SSL)
              --client      Nom du client
              --all         Tous (défaut)
              --detailed    + état conteneurs via SSH

  dashboard   Monitoring temps réel (auto-refresh)
              --interval    Intervalle en sec (défaut: 30)

  list        Lister les clients enregistrés

  add         Enregistrer un client existant (sans install)
              --name / --domain / --ip

  remove      Retirer un client du registre
              --name        Nom du client

  ssh         Ouvrir un terminal SSH vers un client
  logs        Voir les logs Docker d'un client
  backup      Déclencher un backup sur un ou tous les clients

FONCTIONNEMENT:

  Le code est envoyé depuis CETTE machine vers les serveurs
  via rsync (pas de dépendance GitHub sur les serveurs).

  Source locale: $PROJECT_ROOT → Serveur: /opt/geoclic/

EXEMPLES:

  # Installer un nouveau client sur un VPS vierge
  ./geoclic-fleet.sh provision \
    --name ville-lyon \
    --domain lyon.geoclic.fr \
    --ip 51.210.42.100 \
    --email admin@lyon.fr

  # Mettre à jour TOUS les clients
  ./geoclic-fleet.sh update --all

  # Mettre à jour seulement l'API + portail d'un client
  ./geoclic-fleet.sh update --client ville-lyon --services "api portail"

  # Dashboard temps réel
  ./geoclic-fleet.sh dashboard

  # Sauvegarder tous les clients
  ./geoclic-fleet.sh backup --all

PRÉREQUIS:

  1. SSH avec clé publique sur chaque VPS:
     ssh-copy-id root@IP_DU_VPS

  2. rsync, curl, openssl installés localement

  3. VPS: Ubuntu 22.04+ avec accès root

HELP
}

# ═══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════════════════════

if [[ ! -f "$CLIENTS_FILE" ]]; then
    mkdir -p "$FLEET_DIR"
    cat > "$CLIENTS_FILE" << 'EOF'
# GéoClic Fleet - Registre des serveurs clients
# Format: NOM|DOMAINE|IP|SSH_USER|SSH_PORT|METHOD|DATE_AJOUT
EOF
fi

COMMAND="${1:-help}"
shift 2>/dev/null || true

case "$COMMAND" in
    provision)  cmd_provision "$@" ;;
    update)     cmd_update "$@" ;;
    status)     cmd_status "$@" ;;
    dashboard)  cmd_dashboard "$@" ;;
    list)       cmd_list "$@" ;;
    add)        cmd_add "$@" ;;
    remove)     cmd_remove "$@" ;;
    ssh)        cmd_ssh "$@" ;;
    logs)       cmd_logs "$@" ;;
    backup)     cmd_backup "$@" ;;
    help|--help|-h)  cmd_help ;;
    *)          die "Commande inconnue: $COMMAND (tapez 'help')" ;;
esac

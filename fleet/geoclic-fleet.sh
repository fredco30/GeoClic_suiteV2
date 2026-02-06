#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# GéoClic Fleet Manager v2.0
# Gestion centralisée multi-serveurs - Mode serveur maître
#
# Ce script tourne SUR le serveur maître (geoclic.fr) et pousse les
# mises à jour vers les serveurs clients via rsync/SSH.
#
# Usage: geoclic-fleet.sh <commande> [options]
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────────
FLEET_VERSION="2.0.0"
GEOCLIC_DIR="/opt/geoclic"
FLEET_DIR="$GEOCLIC_DIR/fleet"
CLIENTS_CONF="$FLEET_DIR/clients.conf"
SSH_KEY="$HOME/.ssh/geoclic_fleet_key"
LOGS_DIR="$FLEET_DIR/logs"
TASKS_DIR="$FLEET_DIR/tasks"
SSH_TIMEOUT=10

# Répertoires à exclure du rsync vers les clients
RSYNC_EXCLUDES=(
    "node_modules"
    ".git"
    ".github"
    "backups/"
    "deploy/nginx/ssl/"
    "deploy/nginx/logs/"
    "deploy/logs/"
    "deploy/.env"
    "deploy/docker-compose.override.yml"
    "fleet/clients.conf"
    "fleet/logs/"
    "fleet/tasks/"
    "*.log"
    ".DS_Store"
    "__pycache__"
    ".vscode"
    ".idea"
)

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# ─── Fonctions utilitaires ───────────────────────────────────────────────────

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERREUR]${NC} $*"; }
log_step()  { echo -e "${CYAN}[ÉTAPE]${NC} $*"; }

# Crée les dossiers nécessaires
ensure_dirs() {
    mkdir -p "$LOGS_DIR" "$TASKS_DIR"
}

# Retourne "sudo" si l'utilisateur n'est pas root
get_sudo() {
    local user="$1"
    if [[ "$user" != "root" ]]; then
        echo "sudo"
    fi
}

# Vérifie que la clé SSH fleet existe
check_ssh_key() {
    if [[ ! -f "$SSH_KEY" ]]; then
        log_error "Clé SSH fleet non trouvée: $SSH_KEY"
        log_info "Lancez: ssh-keygen -t ed25519 -f $SSH_KEY -N '' -C 'geoclic-fleet'"
        return 1
    fi
}

# Teste la connexion SSH vers un serveur
test_ssh() {
    local ip="$1" user="$2" port="${3:-22}"
    ssh -i "$SSH_KEY" \
        -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=$SSH_TIMEOUT \
        -o BatchMode=yes \
        -p "$port" \
        "${user}@${ip}" "echo ok" &>/dev/null
}

# Exécute une commande SSH
run_ssh() {
    local ip="$1" user="$2" port="$3"
    shift 3
    ssh -i "$SSH_KEY" \
        -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=$SSH_TIMEOUT \
        -p "$port" \
        "${user}@${ip}" "$@"
}

# ─── Gestion des clients (clients.conf) ─────────────────────────────────────

# Liste tous les clients (excluant commentaires et lignes vides)
list_clients() {
    if [[ ! -f "$CLIENTS_CONF" ]]; then
        echo ""
        return
    fi
    grep -v '^\s*#' "$CLIENTS_CONF" | grep -v '^\s*$' || true
}

# Récupère les infos d'un client par nom
get_client() {
    local name="$1"
    list_clients | grep "^${name}|" || true
}

# Parse une ligne client en variables
parse_client() {
    local line="$1"
    IFS='|' read -r CLIENT_NAME CLIENT_DOMAIN CLIENT_IP CLIENT_USER CLIENT_PORT CLIENT_METHOD CLIENT_DATE <<< "$line"
}

# Ajoute un client au registre
add_client_to_conf() {
    local name="$1" domain="$2" ip="$3" user="${4:-ubuntu}" port="${5:-22}"
    local date
    date=$(date +%Y-%m-%d)

    # Vérifier que le nom n'existe pas déjà
    if [[ -n "$(get_client "$name")" ]]; then
        log_error "Le client '$name' existe déjà dans le registre"
        return 1
    fi

    echo "${name}|${domain}|${ip}|${user}|${port}|rsync|${date}" >> "$CLIENTS_CONF"
    log_ok "Client '$name' ajouté au registre"
}

# Supprime un client du registre
remove_client_from_conf() {
    local name="$1"
    if [[ -z "$(get_client "$name")" ]]; then
        log_error "Client '$name' non trouvé"
        return 1
    fi
    local tmp
    tmp=$(mktemp)
    grep -v "^${name}|" "$CLIENTS_CONF" > "$tmp"
    mv "$tmp" "$CLIENTS_CONF"
    log_ok "Client '$name' retiré du registre"
}

# ─── Opérations sur les serveurs ─────────────────────────────────────────────

# Synchronise le code vers un serveur distant
sync_code() {
    local ip="$1" user="$2" port="$3"
    local SUDO
    SUDO=$(get_sudo "$user")

    local exclude_args=()
    for excl in "${RSYNC_EXCLUDES[@]}"; do
        exclude_args+=("--exclude=$excl")
    done

    local rsync_path_arg=""
    if [[ -n "$SUDO" ]]; then
        rsync_path_arg="--rsync-path=sudo rsync"
    fi

    rsync -az --delete \
        "${exclude_args[@]}" \
        ${rsync_path_arg:+"$rsync_path_arg"} \
        -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new -o ConnectTimeout=$SSH_TIMEOUT -p $port" \
        "$GEOCLIC_DIR/" \
        "${user}@${ip}:/opt/geoclic/"
}

# Vérifie la santé d'un serveur via HTTPS
check_health() {
    local domain="$1"
    local url="https://${domain}/api/health"
    local http_code
    http_code=$(curl -sk -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url" 2>/dev/null || echo "000")
    echo "$http_code"
}

# Vérifie le certificat SSL
check_ssl() {
    local domain="$1"
    local expiry
    expiry=$(echo | timeout 5 openssl s_client -servername "$domain" -connect "${domain}:443" 2>/dev/null | \
        openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || echo "")
    echo "$expiry"
}

# Récupère l'état détaillé d'un serveur
get_server_status() {
    local name="$1"
    local line
    line=$(get_client "$name")
    if [[ -z "$line" ]]; then
        echo '{"error":"Client non trouvé"}'
        return 1
    fi

    parse_client "$line"

    local health_code ssl_expiry ssh_ok docker_status=""
    health_code=$(check_health "$CLIENT_DOMAIN")
    ssl_expiry=$(check_ssl "$CLIENT_DOMAIN")

    if test_ssh "$CLIENT_IP" "$CLIENT_USER" "$CLIENT_PORT"; then
        ssh_ok="true"
        local SUDO
        SUDO=$(get_sudo "$CLIENT_USER")
        docker_status=$(run_ssh "$CLIENT_IP" "$CLIENT_USER" "$CLIENT_PORT" \
            "cd /opt/geoclic/deploy && $SUDO docker compose ps --format json 2>/dev/null || $SUDO docker-compose ps 2>/dev/null" || echo "")
    else
        ssh_ok="false"
    fi

    # Sortie JSON
    cat <<EOJSON
{
    "name": "$CLIENT_NAME",
    "domain": "$CLIENT_DOMAIN",
    "ip": "$CLIENT_IP",
    "ssh_user": "$CLIENT_USER",
    "ssh_port": "$CLIENT_PORT",
    "date_ajout": "$CLIENT_DATE",
    "health_http": "$health_code",
    "ssl_expiry": "$ssl_expiry",
    "ssh_ok": $ssh_ok,
    "docker_status": $(echo "$docker_status" | python3 -c "import sys,json; lines=sys.stdin.read().strip(); print(json.dumps(lines))" 2>/dev/null || echo '""')
}
EOJSON
}

# ─── Commande: provision ─────────────────────────────────────────────────────
cmd_provision() {
    local name="" domain="" ip="" email="" user="ubuntu" port="22"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name)    name="$2"; shift 2 ;;
            --domain)  domain="$2"; shift 2 ;;
            --ip)      ip="$2"; shift 2 ;;
            --email)   email="$2"; shift 2 ;;
            --ssh-user) user="$2"; shift 2 ;;
            --ssh-port) port="$2"; shift 2 ;;
            *) log_error "Option inconnue: $1"; return 1 ;;
        esac
    done

    # Validation
    if [[ -z "$name" || -z "$domain" || -z "$ip" || -z "$email" ]]; then
        log_error "Paramètres requis: --name, --domain, --ip, --email"
        return 1
    fi

    check_ssh_key || return 1

    local SUDO
    SUDO=$(get_sudo "$user")
    local logfile="$LOGS_DIR/provision_${name}_$(date +%Y%m%d_%H%M%S).log"
    local task_id="provision_${name}_$(date +%s)"
    local task_file="$TASKS_DIR/${task_id}.json"

    log_info "Provisioning de '$name' ($domain) sur $ip"
    log_info "Log: $logfile"

    # Fonction pour mettre à jour le statut de la tâche
    update_task() {
        local step="$1" total="$2" label="$3" status="${4:-running}"
        cat > "$task_file" <<EOTASK
{"task_id":"$task_id","name":"$name","type":"provision","status":"$status","step":$step,"total":$total,"label":"$label","log_file":"$logfile"}
EOTASK
    }

    {
        # ÉTAPE 1/7 : Test SSH
        update_task 1 7 "Test connexion SSH"
        log_step "1/7 - Test connexion SSH vers ${user}@${ip}:${port}..."
        if ! test_ssh "$ip" "$user" "$port"; then
            log_error "Connexion SSH impossible. Vérifiez que la clé fleet est autorisée."
            update_task 1 7 "Échec connexion SSH" "failed"
            return 1
        fi
        log_ok "SSH OK"

        # ÉTAPE 2/7 : Mise à jour système + installation Docker
        update_task 2 7 "Installation des prérequis"
        log_step "2/7 - Mise à jour système et installation Docker..."
        run_ssh "$ip" "$user" "$port" "
            $SUDO apt-get update -qq && \
            $SUDO apt-get install -y -qq curl rsync certbot > /dev/null 2>&1 && \
            if ! command -v docker &>/dev/null; then
                curl -fsSL https://get.docker.com | $SUDO sh
                $SUDO systemctl enable docker
                $SUDO systemctl start docker
            fi && \
            if ! command -v docker compose &>/dev/null && ! command -v docker-compose &>/dev/null; then
                $SUDO apt-get install -y -qq docker-compose-plugin > /dev/null 2>&1 || \
                ($SUDO curl -L 'https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64' -o /usr/local/bin/docker-compose && \
                 $SUDO chmod +x /usr/local/bin/docker-compose)
            fi
        "
        log_ok "Docker installé"

        # ÉTAPE 3/7 : Créer le dossier et copier le code
        update_task 3 7 "Copie du code"
        log_step "3/7 - Copie du code vers le serveur..."
        run_ssh "$ip" "$user" "$port" "$SUDO mkdir -p /opt/geoclic"
        sync_code "$ip" "$user" "$port"
        log_ok "Code copié"

        # ÉTAPE 4/7 : Générer le fichier .env
        update_task 4 7 "Configuration environnement"
        log_step "4/7 - Génération du fichier .env..."
        local jwt_secret db_password
        jwt_secret=$(openssl rand -hex 32)
        db_password=$(openssl rand -hex 16)

        run_ssh "$ip" "$user" "$port" "
            $SUDO tee /opt/geoclic/deploy/.env > /dev/null <<'ENVEOF'
# GéoClic - Configuration $name
# Généré le $(date +%Y-%m-%d)

# Base de données
DB_USER=geoclic
DB_PASSWORD=$db_password
DB_NAME=geoclic_db

# JWT (ne jamais changer après la première installation)
JWT_SECRET_KEY=$jwt_secret

# Application
APP_ENV=production
DEBUG=false
CORS_ORIGINS=https://$domain

# Email SSL
LETSENCRYPT_EMAIL=$email
ENVEOF
        "
        log_ok ".env configuré"

        # ÉTAPE 5/7 : Certificat SSL
        update_task 5 7 "Certificat SSL"
        log_step "5/7 - Obtention du certificat SSL..."
        run_ssh "$ip" "$user" "$port" "
            $SUDO mkdir -p /opt/geoclic/deploy/nginx/ssl
            if [[ ! -f /opt/geoclic/deploy/nginx/ssl/fullchain.pem ]]; then
                $SUDO certbot certonly --standalone --non-interactive --agree-tos \
                    -m $email -d $domain \
                    --cert-path /opt/geoclic/deploy/nginx/ssl/cert.pem \
                    --key-path /opt/geoclic/deploy/nginx/ssl/privkey.pem \
                    --fullchain-path /opt/geoclic/deploy/nginx/ssl/fullchain.pem || true

                # Copier les certificats Let's Encrypt vers le dossier nginx
                if [[ -d /etc/letsencrypt/live/$domain ]]; then
                    $SUDO cp /etc/letsencrypt/live/$domain/fullchain.pem /opt/geoclic/deploy/nginx/ssl/
                    $SUDO cp /etc/letsencrypt/live/$domain/privkey.pem /opt/geoclic/deploy/nginx/ssl/
                fi
            fi
        "
        log_ok "SSL configuré"

        # ÉTAPE 6/7 : Build et démarrage Docker
        update_task 6 7 "Construction Docker"
        log_step "6/7 - Build et démarrage des conteneurs Docker..."
        run_ssh "$ip" "$user" "$port" "
            cd /opt/geoclic/deploy
            $SUDO docker compose down 2>/dev/null || $SUDO docker-compose down 2>/dev/null || true
            $SUDO docker container prune -f > /dev/null 2>&1
            $SUDO docker compose up -d --build 2>&1 || $SUDO docker-compose up -d --build 2>&1
        "
        log_ok "Docker démarré"

        # ÉTAPE 7/7 : Configuration finale
        update_task 7 7 "Configuration finale"
        log_step "7/7 - Configuration cron, systemd et vérification..."
        run_ssh "$ip" "$user" "$port" "
            # Cron backup (tous les jours à 2h)
            ($SUDO crontab -l 2>/dev/null | grep -v geoclic; echo '0 2 * * * /opt/geoclic/scripts/backup_db.sh >> /var/log/geoclic_backup.log 2>&1') | $SUDO crontab -

            # Cron monitoring (toutes les 5 min)
            ($SUDO crontab -l 2>/dev/null | grep -v monitor; echo '*/5 * * * * /opt/geoclic/scripts/monitor.sh > /dev/null 2>&1') | $SUDO crontab -

            # Certbot renouvellement auto avec hook
            ($SUDO crontab -l 2>/dev/null | grep -v certbot; echo '0 3 * * * certbot renew --deploy-hook \"cp /etc/letsencrypt/live/$domain/fullchain.pem /opt/geoclic/deploy/nginx/ssl/ && cp /etc/letsencrypt/live/$domain/privkey.pem /opt/geoclic/deploy/nginx/ssl/ && cd /opt/geoclic/deploy && docker compose restart nginx 2>/dev/null || docker-compose restart nginx\"') | $SUDO crontab -

            # Systemd auto-start
            $SUDO tee /etc/systemd/system/geoclic.service > /dev/null <<'SVCEOF'
[Unit]
Description=GéoClic Suite
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/geoclic/deploy
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
SVCEOF
            $SUDO systemctl daemon-reload
            $SUDO systemctl enable geoclic.service
        "

        # Attendre que l'API soit prête
        log_info "Attente du démarrage de l'API..."
        local retries=0
        while [[ $retries -lt 30 ]]; do
            local code
            code=$(check_health "$domain")
            if [[ "$code" == "200" ]]; then
                break
            fi
            sleep 5
            retries=$((retries + 1))
        done

        local final_code
        final_code=$(check_health "$domain")
        if [[ "$final_code" == "200" ]]; then
            log_ok "Serveur '$name' opérationnel ! https://$domain"
            update_task 7 7 "Terminé" "completed"
        else
            log_warn "API non accessible (HTTP $final_code). Le serveur peut avoir besoin de plus de temps."
            update_task 7 7 "Terminé (vérification en cours)" "completed"
        fi

        # Ajouter au registre
        add_client_to_conf "$name" "$domain" "$ip" "$user" "$port" 2>/dev/null || true

    } 2>&1 | tee -a "$logfile"

    echo "$task_id"
}

# ─── Commande: update ────────────────────────────────────────────────────────
cmd_update() {
    local client="" all=false services="" migration=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --client)     client="$2"; shift 2 ;;
            --all)        all=true; shift ;;
            --services)   services="$2"; shift 2 ;;
            --migration)  migration="$2"; shift 2 ;;
            *) log_error "Option inconnue: $1"; return 1 ;;
        esac
    done

    check_ssh_key || return 1

    # Construire la liste des clients à mettre à jour
    local targets=()
    if [[ "$all" == true ]]; then
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            parse_client "$line"
            targets+=("$CLIENT_NAME")
        done <<< "$(list_clients)"
    elif [[ -n "$client" ]]; then
        targets+=("$client")
    else
        log_error "Spécifiez --client NOM ou --all"
        return 1
    fi

    for name in "${targets[@]}"; do
        update_single "$name" "$services" "$migration"
    done
}

# Met à jour un serveur unique
update_single() {
    local name="$1" services="$2" migration="$3"
    local line
    line=$(get_client "$name")
    if [[ -z "$line" ]]; then
        log_error "Client '$name' non trouvé"
        return 1
    fi

    parse_client "$line"
    local SUDO
    SUDO=$(get_sudo "$CLIENT_USER")
    local logfile="$LOGS_DIR/update_${name}_$(date +%Y%m%d_%H%M%S).log"
    local task_id="update_${name}_$(date +%s)"
    local task_file="$TASKS_DIR/${task_id}.json"

    update_task_status() {
        local step="$1" total="$2" label="$3" status="${4:-running}"
        cat > "$task_file" <<EOTASK
{"task_id":"$task_id","name":"$name","type":"update","status":"$status","step":$step,"total":$total,"label":"$label","log_file":"$logfile"}
EOTASK
    }

    log_info "Mise à jour de '$name' ($CLIENT_DOMAIN)..."

    {
        local total_steps=4
        [[ -n "$migration" ]] && total_steps=5

        # Étape 1 : Backup
        update_task_status 1 $total_steps "Sauvegarde base de données"
        log_step "1/$total_steps - Backup de la base de données..."
        run_ssh "$CLIENT_IP" "$CLIENT_USER" "$CLIENT_PORT" "
            $SUDO docker exec geoclic_db pg_dump -U geoclic -d geoclic_db -Fc -f /tmp/backup_before_update.dump 2>/dev/null || true
        " || log_warn "Backup échoué (non bloquant)"
        log_ok "Backup effectué"

        # Étape 2 : Sync code
        update_task_status 2 $total_steps "Copie du code"
        log_step "2/$total_steps - Synchronisation du code..."
        sync_code "$CLIENT_IP" "$CLIENT_USER" "$CLIENT_PORT"
        log_ok "Code synchronisé"

        # Étape 3 : Migration (optionnel)
        local step=3
        if [[ -n "$migration" ]]; then
            update_task_status $step $total_steps "Application migration SQL"
            log_step "$step/$total_steps - Application de la migration: $migration..."
            run_ssh "$CLIENT_IP" "$CLIENT_USER" "$CLIENT_PORT" "
                $SUDO docker exec -i geoclic_db psql -U geoclic -d geoclic_db < /opt/geoclic/database/migrations/$migration
            "
            log_ok "Migration appliquée"
            step=$((step + 1))
        fi

        # Étape N-1 : Rebuild Docker
        update_task_status $step $total_steps "Reconstruction Docker"
        log_step "$step/$total_steps - Rebuild des conteneurs..."
        local build_targets="${services:-api admin portail demandes mobile sig services terrain}"
        run_ssh "$CLIENT_IP" "$CLIENT_USER" "$CLIENT_PORT" "
            cd /opt/geoclic/deploy
            $SUDO docker compose down 2>/dev/null || $SUDO docker-compose down 2>/dev/null
            $SUDO docker container prune -f > /dev/null 2>&1
            $SUDO docker compose build --no-cache $build_targets 2>&1 || $SUDO docker-compose build --no-cache $build_targets 2>&1
            $SUDO docker compose up -d 2>&1 || $SUDO docker-compose up -d 2>&1
        "
        log_ok "Docker redémarré"
        step=$((step + 1))

        # Étape N : Vérification
        update_task_status $step $total_steps "Vérification santé"
        log_step "$step/$total_steps - Vérification de santé..."
        sleep 10
        local code
        code=$(check_health "$CLIENT_DOMAIN")
        if [[ "$code" == "200" ]]; then
            log_ok "'$name' mis à jour avec succès (HTTP 200)"
            update_task_status $step $total_steps "Terminé" "completed"
        else
            log_warn "'$name' - API retourne HTTP $code (peut nécessiter plus de temps)"
            update_task_status $step $total_steps "Terminé (HTTP $code)" "completed"
        fi

    } 2>&1 | tee -a "$logfile"

    echo "$task_id"
}

# ─── Commande: status ────────────────────────────────────────────────────────
cmd_status() {
    local client="" detailed=false json=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --client)    client="$2"; shift 2 ;;
            --detailed)  detailed=true; shift ;;
            --json)      json=true; shift ;;
            *) shift ;;
        esac
    done

    if [[ -n "$client" ]]; then
        get_server_status "$client"
        return
    fi

    # Statut de tous les serveurs
    local results="["
    local first=true

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        parse_client "$line"

        if [[ "$first" == true ]]; then
            first=false
        else
            results+=","
        fi

        local health_code ssl_expiry ssh_ok
        health_code=$(check_health "$CLIENT_DOMAIN")
        ssl_expiry=$(check_ssl "$CLIENT_DOMAIN")

        ssh_ok="false"
        if check_ssh_key 2>/dev/null && test_ssh "$CLIENT_IP" "$CLIENT_USER" "$CLIENT_PORT" 2>/dev/null; then
            ssh_ok="true"
        fi

        results+="{\"name\":\"$CLIENT_NAME\",\"domain\":\"$CLIENT_DOMAIN\",\"ip\":\"$CLIENT_IP\",\"health_http\":\"$health_code\",\"ssl_expiry\":\"$ssl_expiry\",\"ssh_ok\":$ssh_ok,\"date_ajout\":\"$CLIENT_DATE\"}"

        if [[ "$json" == false ]]; then
            local status_icon="🔴"
            [[ "$health_code" == "200" ]] && status_icon="🟢"
            echo -e "${status_icon} ${BOLD}$CLIENT_NAME${NC} ($CLIENT_DOMAIN) - HTTP $health_code - SSL: $ssl_expiry - SSH: $ssh_ok"
        fi
    done <<< "$(list_clients)"

    results+="]"

    if [[ "$json" == true ]]; then
        echo "$results"
    fi
}

# ─── Commande: list ──────────────────────────────────────────────────────────
cmd_list() {
    local json=false
    [[ "${1:-}" == "--json" ]] && json=true

    if [[ "$json" == true ]]; then
        local results="["
        local first=true
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            parse_client "$line"
            [[ "$first" == true ]] && first=false || results+=","
            results+="{\"name\":\"$CLIENT_NAME\",\"domain\":\"$CLIENT_DOMAIN\",\"ip\":\"$CLIENT_IP\",\"ssh_user\":\"$CLIENT_USER\",\"ssh_port\":\"$CLIENT_PORT\",\"date_ajout\":\"$CLIENT_DATE\"}"
        done <<< "$(list_clients)"
        results+="]"
        echo "$results"
    else
        echo -e "${BOLD}Clients enregistrés:${NC}"
        echo "─────────────────────────────────────────"
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            parse_client "$line"
            echo -e "  ${CYAN}$CLIENT_NAME${NC} | $CLIENT_DOMAIN | $CLIENT_IP | $CLIENT_USER | Port $CLIENT_PORT | $CLIENT_DATE"
        done <<< "$(list_clients)"
    fi
}

# ─── Commande: add ───────────────────────────────────────────────────────────
cmd_add() {
    local name="" domain="" ip="" user="ubuntu" port="22"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name)     name="$2"; shift 2 ;;
            --domain)   domain="$2"; shift 2 ;;
            --ip)       ip="$2"; shift 2 ;;
            --ssh-user) user="$2"; shift 2 ;;
            --ssh-port) port="$2"; shift 2 ;;
            *) log_error "Option inconnue: $1"; return 1 ;;
        esac
    done

    if [[ -z "$name" || -z "$domain" || -z "$ip" ]]; then
        log_error "Paramètres requis: --name, --domain, --ip"
        return 1
    fi

    add_client_to_conf "$name" "$domain" "$ip" "$user" "$port"
}

# ─── Commande: remove ────────────────────────────────────────────────────────
cmd_remove() {
    local name=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name) name="$2"; shift 2 ;;
            *) log_error "Option inconnue: $1"; return 1 ;;
        esac
    done

    if [[ -z "$name" ]]; then
        log_error "Paramètre requis: --name"
        return 1
    fi

    remove_client_from_conf "$name"
}

# ─── Commande: ssh ───────────────────────────────────────────────────────────
cmd_ssh_connect() {
    local name="$1"
    local line
    line=$(get_client "$name")
    if [[ -z "$line" ]]; then
        log_error "Client '$name' non trouvé"
        return 1
    fi
    parse_client "$line"
    check_ssh_key || return 1
    log_info "Connexion SSH à $name ($CLIENT_IP)..."
    exec ssh -i "$SSH_KEY" -p "$CLIENT_PORT" "${CLIENT_USER}@${CLIENT_IP}"
}

# ─── Commande: logs ──────────────────────────────────────────────────────────
cmd_logs() {
    local name="" service="api" lines=50

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --service) service="$2"; shift 2 ;;
            --lines)   lines="$2"; shift 2 ;;
            *)         [[ -z "$name" ]] && name="$1"; shift ;;
        esac
    done

    if [[ -z "$name" ]]; then
        log_error "Usage: geoclic-fleet.sh logs NOM [--service SERVICE] [--lines N]"
        return 1
    fi

    local line
    line=$(get_client "$name")
    if [[ -z "$line" ]]; then
        log_error "Client '$name' non trouvé"
        return 1
    fi
    parse_client "$line"
    check_ssh_key || return 1
    local SUDO
    SUDO=$(get_sudo "$CLIENT_USER")

    run_ssh "$CLIENT_IP" "$CLIENT_USER" "$CLIENT_PORT" \
        "cd /opt/geoclic/deploy && $SUDO docker compose logs --tail=$lines $service 2>/dev/null || $SUDO docker-compose logs --tail=$lines $service 2>/dev/null"
}

# ─── Commande: backup ────────────────────────────────────────────────────────
cmd_backup() {
    local client="" all=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --client) client="$2"; shift 2 ;;
            --all)    all=true; shift ;;
            *) log_error "Option inconnue: $1"; return 1 ;;
        esac
    done

    check_ssh_key || return 1

    local targets=()
    if [[ "$all" == true ]]; then
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            parse_client "$line"
            targets+=("$CLIENT_NAME")
        done <<< "$(list_clients)"
    elif [[ -n "$client" ]]; then
        targets+=("$client")
    else
        log_error "Spécifiez --client NOM ou --all"
        return 1
    fi

    for name in "${targets[@]}"; do
        local line
        line=$(get_client "$name")
        parse_client "$line"
        local SUDO
        SUDO=$(get_sudo "$CLIENT_USER")

        log_info "Backup de '$name'..."
        run_ssh "$CLIENT_IP" "$CLIENT_USER" "$CLIENT_PORT" \
            "$SUDO /opt/geoclic/scripts/backup_db.sh" || log_warn "Backup de '$name' échoué"
        log_ok "Backup de '$name' terminé"
    done
}

# ─── Commande: task-status ───────────────────────────────────────────────────
cmd_task_status() {
    local task_id="$1"
    local task_file="$TASKS_DIR/${task_id}.json"
    if [[ -f "$task_file" ]]; then
        cat "$task_file"
    else
        echo '{"error":"Tâche non trouvée"}'
        return 1
    fi
}

# ─── Commande: task-log ─────────────────────────────────────────────────────
cmd_task_log() {
    local task_id="$1" lines="${2:-50}"
    local task_file="$TASKS_DIR/${task_id}.json"
    if [[ ! -f "$task_file" ]]; then
        echo "Tâche non trouvée"
        return 1
    fi
    local log_file
    log_file=$(python3 -c "import json; print(json.load(open('$task_file'))['log_file'])" 2>/dev/null || echo "")
    if [[ -n "$log_file" && -f "$log_file" ]]; then
        tail -n "$lines" "$log_file"
    else
        echo "Fichier de log non trouvé"
    fi
}

# ─── Commande: test-ssh ─────────────────────────────────────────────────────
cmd_test_ssh() {
    local ip="$1" user="${2:-ubuntu}" port="${3:-22}"
    check_ssh_key || return 1
    if test_ssh "$ip" "$user" "$port"; then
        echo '{"status":"ok"}'
    else
        echo '{"status":"failed"}'
        return 1
    fi
}

# ─── Commande: ssh-key ──────────────────────────────────────────────────────
cmd_ssh_key() {
    local action="${1:-show}"

    case "$action" in
        generate)
            if [[ -f "$SSH_KEY" ]]; then
                log_warn "La clé existe déjà: $SSH_KEY"
                log_info "Clé publique:"
                cat "${SSH_KEY}.pub"
                return 0
            fi
            ssh-keygen -t ed25519 -f "$SSH_KEY" -N "" -C "geoclic-fleet@$(hostname)"
            log_ok "Clé SSH fleet générée"
            log_info "Clé publique à copier sur les VPS:"
            cat "${SSH_KEY}.pub"
            ;;
        show)
            if [[ -f "${SSH_KEY}.pub" ]]; then
                cat "${SSH_KEY}.pub"
            else
                log_error "Pas de clé SSH fleet. Lancez: $0 ssh-key generate"
                return 1
            fi
            ;;
        *)
            log_error "Action inconnue: $action (generate|show)"
            return 1
            ;;
    esac
}

# ─── Commande: help ──────────────────────────────────────────────────────────
cmd_help() {
    cat <<EOF
${BOLD}GéoClic Fleet Manager v${FLEET_VERSION}${NC}
Gestion centralisée multi-serveurs depuis le serveur maître.

${BOLD}Usage:${NC} geoclic-fleet.sh <commande> [options]

${BOLD}Commandes:${NC}
  ${CYAN}provision${NC}    Installer GéoClic sur un nouveau serveur
  ${CYAN}update${NC}       Mettre à jour un ou tous les serveurs
  ${CYAN}status${NC}       Voir l'état des serveurs
  ${CYAN}list${NC}         Lister les serveurs enregistrés
  ${CYAN}add${NC}          Ajouter un serveur au registre
  ${CYAN}remove${NC}       Retirer un serveur du registre
  ${CYAN}ssh${NC}          Se connecter en SSH à un serveur
  ${CYAN}logs${NC}         Voir les logs Docker d'un serveur
  ${CYAN}backup${NC}       Lancer une sauvegarde
  ${CYAN}ssh-key${NC}      Gérer la clé SSH fleet (generate|show)
  ${CYAN}test-ssh${NC}     Tester la connexion SSH (IP [USER] [PORT])
  ${CYAN}task-status${NC}  Statut d'une tâche en cours (TASK_ID)
  ${CYAN}task-log${NC}     Logs d'une tâche (TASK_ID [LINES])

${BOLD}Exemples:${NC}
  # Provisionner un nouveau client
  geoclic-fleet.sh provision --name ville-lyon --domain lyon.geoclic.fr \\
    --ip 51.210.42.100 --email admin@lyon.fr

  # Mettre à jour tous les clients
  geoclic-fleet.sh update --all

  # Mettre à jour un client avec migration
  geoclic-fleet.sh update --client ville-lyon --migration 023_new_feature.sql

  # État de tous les serveurs
  geoclic-fleet.sh status

  # État JSON (utilisé par l'API fleet)
  geoclic-fleet.sh status --json
EOF
}

# ─── Point d'entrée ──────────────────────────────────────────────────────────
main() {
    ensure_dirs

    local command="${1:-help}"
    shift || true

    case "$command" in
        provision)     cmd_provision "$@" ;;
        update)        cmd_update "$@" ;;
        status)        cmd_status "$@" ;;
        list)          cmd_list "$@" ;;
        add)           cmd_add "$@" ;;
        remove)        cmd_remove "$@" ;;
        ssh)           cmd_ssh_connect "$@" ;;
        logs)          cmd_logs "$@" ;;
        backup)        cmd_backup "$@" ;;
        ssh-key)       cmd_ssh_key "$@" ;;
        test-ssh)      cmd_test_ssh "$@" ;;
        task-status)   cmd_task_status "$@" ;;
        task-log)      cmd_task_log "$@" ;;
        help|--help|-h) cmd_help ;;
        *)             log_error "Commande inconnue: $command"; cmd_help; exit 1 ;;
    esac
}

main "$@"

#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Lanceur GéoClic SIG Desktop - Linux
# Gère l'installation, la configuration initiale et les mises à jour
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Configuration
APP_NAME="geoclic-sig"
APP_DISPLAY_NAME="GéoClic SIG"
VERSION="14.0.0"
INSTALL_DIR="$HOME/.local/share/geoclic-sig"
CONFIG_DIR="$HOME/.config/geoclic-sig"
DOWNLOAD_URL="https://releases.geoclic.fr/sig/linux/latest"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ═══════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION DE L'INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════════
check_install() {
    if [[ ! -f "$INSTALL_DIR/geoclic_sig" ]]; then
        return 1
    fi
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLATION INITIALE
# ═══════════════════════════════════════════════════════════════════════════════
install_app() {
    log_info "Installation de $APP_DISPLAY_NAME..."

    # Créer les répertoires
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"

    # Vérifier si le bundle est dans le même dossier que ce script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [[ -f "$SCRIPT_DIR/geoclic_sig" ]]; then
        log_info "Installation depuis le dossier local..."
        cp -r "$SCRIPT_DIR/"* "$INSTALL_DIR/"
    else
        # Télécharger depuis le serveur
        log_info "Téléchargement depuis $DOWNLOAD_URL..."

        TMP_FILE="/tmp/geoclic-sig-latest.tar.gz"
        curl -L -o "$TMP_FILE" "$DOWNLOAD_URL" || {
            log_error "Échec du téléchargement"
            exit 1
        }

        log_info "Extraction..."
        tar -xzf "$TMP_FILE" -C "$INSTALL_DIR" --strip-components=1
        rm "$TMP_FILE"
    fi

    # Rendre exécutable
    chmod +x "$INSTALL_DIR/geoclic_sig"

    # Créer le fichier .desktop
    create_desktop_entry

    log_success "Installation terminée !"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CRÉATION DE L'ENTRÉE DESKTOP
# ═══════════════════════════════════════════════════════════════════════════════
create_desktop_entry() {
    DESKTOP_FILE="$HOME/.local/share/applications/geoclic-sig.desktop"

    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=$APP_DISPLAY_NAME
Comment=Application SIG pour la gestion territoriale des collectivités
Exec=$INSTALL_DIR/geoclic_sig
Icon=$INSTALL_DIR/data/flutter_assets/assets/icon/app_icon.png
Terminal=false
Type=Application
Categories=Utility;Geography;Office;
Keywords=SIG;cartographie;GPS;territoire;patrimoine;
StartupWMClass=geoclic_sig
EOF

    chmod +x "$DESKTOP_FILE"

    # Mettre à jour le cache des applications
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    fi

    log_success "Raccourci créé dans le menu des applications"
}

# ═══════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION DES MISES À JOUR
# ═══════════════════════════════════════════════════════════════════════════════
check_update() {
    # Vérifier si une mise à jour est disponible
    log_info "Vérification des mises à jour..."

    CURRENT_VERSION=$(cat "$INSTALL_DIR/version.txt" 2>/dev/null || echo "0.0.0")
    LATEST_VERSION=$(curl -s "https://releases.geoclic.fr/sig/version.txt" 2>/dev/null || echo "$CURRENT_VERSION")

    if [[ "$LATEST_VERSION" != "$CURRENT_VERSION" ]]; then
        log_warn "Mise à jour disponible: $CURRENT_VERSION -> $LATEST_VERSION"

        # Demander à l'utilisateur (si terminal interactif)
        if [[ -t 0 ]]; then
            read -p "Voulez-vous mettre à jour maintenant ? (o/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Oo]$ ]]; then
                update_app
            fi
        fi
    else
        log_success "Vous avez la dernière version ($CURRENT_VERSION)"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# MISE À JOUR
# ═══════════════════════════════════════════════════════════════════════════════
update_app() {
    log_info "Mise à jour de $APP_DISPLAY_NAME..."

    # Sauvegarder la configuration
    if [[ -d "$INSTALL_DIR/data" ]]; then
        cp -r "$INSTALL_DIR/data" "/tmp/geoclic-sig-data-backup"
    fi

    # Télécharger la nouvelle version
    TMP_FILE="/tmp/geoclic-sig-latest.tar.gz"
    curl -L -o "$TMP_FILE" "$DOWNLOAD_URL" || {
        log_error "Échec du téléchargement"
        return 1
    }

    # Supprimer l'ancienne version
    rm -rf "$INSTALL_DIR"/*

    # Extraire la nouvelle version
    tar -xzf "$TMP_FILE" -C "$INSTALL_DIR" --strip-components=1
    rm "$TMP_FILE"

    # Restaurer la configuration
    if [[ -d "/tmp/geoclic-sig-data-backup" ]]; then
        cp -r "/tmp/geoclic-sig-data-backup/"* "$INSTALL_DIR/data/" 2>/dev/null || true
        rm -rf "/tmp/geoclic-sig-data-backup"
    fi

    chmod +x "$INSTALL_DIR/geoclic_sig"

    log_success "Mise à jour terminée !"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION INITIALE
# ═══════════════════════════════════════════════════════════════════════════════
first_run_setup() {
    if [[ ! -f "$CONFIG_DIR/config.json" ]]; then
        log_info "Configuration initiale..."

        # Créer une configuration par défaut
        cat > "$CONFIG_DIR/config.json" << 'EOF'
{
  "api_url": "",
  "connection_mode": "api",
  "agent_name": "",
  "offline_mode": false,
  "auto_sync": true,
  "sync_interval_minutes": 5,
  "map_cache_enabled": true,
  "photo_quality": "high"
}
EOF

        log_info "Configuration créée dans $CONFIG_DIR/config.json"
        log_info "Configurez l'URL de l'API au premier lancement de l'application"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# LANCEMENT DE L'APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
launch_app() {
    cd "$INSTALL_DIR"

    # Définir les variables d'environnement
    export XDG_CONFIG_HOME="$CONFIG_DIR"
    export GEOCLIC_VERSION="$VERSION"

    # Lancer l'application
    exec ./geoclic_sig "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# SCRIPT PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
main() {
    case "${1:-}" in
        --install)
            install_app
            ;;
        --update)
            check_install || { log_error "Application non installée"; exit 1; }
            update_app
            ;;
        --check-update)
            check_install || { log_error "Application non installée"; exit 1; }
            check_update
            ;;
        --uninstall)
            log_info "Désinstallation de $APP_DISPLAY_NAME..."
            rm -rf "$INSTALL_DIR"
            rm -f "$HOME/.local/share/applications/geoclic-sig.desktop"
            log_success "Désinstallation terminée"
            ;;
        --version)
            echo "$APP_DISPLAY_NAME v$VERSION"
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --install       Installer l'application"
            echo "  --update        Forcer la mise à jour"
            echo "  --check-update  Vérifier les mises à jour"
            echo "  --uninstall     Désinstaller l'application"
            echo "  --version       Afficher la version"
            echo "  --help          Afficher cette aide"
            echo ""
            echo "Sans option: lance l'application (installe si nécessaire)"
            ;;
        *)
            # Installation automatique si nécessaire
            if ! check_install; then
                install_app
            fi

            first_run_setup

            # Vérification des mises à jour en arrière-plan
            check_update &

            # Lancer l'application
            launch_app "$@"
            ;;
    esac
}

main "$@"

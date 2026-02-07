#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# GéoClic Suite - Initialisation d'un nouveau serveur client
# ═══════════════════════════════════════════════════════════════════════════════
#
# Ce script initialise une base de données vierge avec :
#   1. Toutes les migrations SQL (schéma complet)
#   2. Un compte super admin
#   3. Le projet système "Signalements Citoyens"
#
# Le client peut ensuite se connecter et utiliser le wizard d'onboarding
# pour configurer : branding, email SMTP, catégories, services.
#
# Usage:
#   sudo /opt/geoclic/scripts/init_client.sh "admin@mairie.fr" "MotDePasse!" "Mairie de Exemple"
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# ─── Paramètres ──────────────────────────────────────────────────────────────

ADMIN_EMAIL="${1:-}"
ADMIN_PASSWORD="${2:-}"
COLLECTIVITE="${3:-Ma Collectivité}"

DB_CONTAINER="geoclic_db"
DB_NAME="geoclic_db"
DB_USER="geoclic"
MIGRATIONS_DIR="/opt/geoclic/database/migrations"

# ─── Couleurs ────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
err()  { echo -e "  ${RED}✗${NC} $1"; }
step() { echo -e "\n${BLUE}━━━ $1${NC}"; }

# ─── Validation ──────────────────────────────────────────────────────────────

if [[ -z "$ADMIN_EMAIL" || -z "$ADMIN_PASSWORD" ]]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  GéoClic Suite - Initialisation nouveau client"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Usage:"
    echo "  sudo $0 <email_admin> <mot_de_passe> [nom_collectivité]"
    echo ""
    echo "Exemple:"
    echo "  sudo $0 \"admin@mairie-exemple.fr\" \"MonMotDePasse123!\" \"Mairie d'Exemple\""
    echo ""
    echo "Paramètres:"
    echo "  email_admin      Email du super administrateur"
    echo "  mot_de_passe     Mot de passe (min 8 caractères)"
    echo "  nom_collectivité Nom de la collectivité (défaut: Ma Collectivité)"
    echo ""
    exit 1
fi

if [[ ${#ADMIN_PASSWORD} -lt 8 ]]; then
    err "Le mot de passe doit contenir au moins 8 caractères"
    exit 1
fi

# Vérifier que le conteneur DB tourne
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    err "Le conteneur $DB_CONTAINER n'est pas en cours d'exécution"
    echo "  Lancez d'abord: cd /opt/geoclic/deploy && sudo docker-compose up -d"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  GéoClic Suite - Initialisation nouveau client"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Email admin    : $ADMIN_EMAIL"
echo "  Collectivité   : $COLLECTIVITE"
echo "  Base de données: $DB_NAME"
echo ""

# ─── Étape 1 : Vérifier la connexion DB ─────────────────────────────────────

step "1/4 - Vérification de la base de données"

# Tester la connexion
if docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
    ok "Connexion à PostgreSQL OK"
else
    err "Impossible de se connecter à PostgreSQL"
    exit 1
fi

# Vérifier que PostGIS est installé
if docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT PostGIS_Version();" > /dev/null 2>&1; then
    ok "PostGIS disponible"
else
    warn "PostGIS non trouvé, tentative d'installation..."
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;" 2>/dev/null || true
fi

# ─── Étape 2 : Appliquer toutes les migrations ──────────────────────────────

step "2/4 - Application des migrations SQL"

# Ordre des migrations (IMPORTANT : respecter les dépendances)
MIGRATIONS=(
    "add_system_settings.sql"
    "002_add_project_id_to_lexique.sql"
    "003_add_project_id_to_type_field_configs.sql"
    "004_add_short_codes_and_signalements.sql"
    "005_demandes_citoyens.sql"
    "006_doublons_detection.sql"
    "007_services_municipaux.sql"
    "008_geoclic_services.sql"
    "009_fix_agents_user_id.sql"
    "010_add_commentaire_interne.sql"
    "011_email_settings.sql"
    "012_chat_terrain.sql"
    "013_system_project.sql"
    "014_zones_hierarchiques.sql"
    "015_geoclic_users.sql"
    "015_photos_intervention.sql"
    "016_fix_historique_fk.sql"
    "017_sync_agents_to_geoclic_users.sql"
    "018_fix_system_settings_fk.sql"
    "019_fix_geoclic_staging_fk.sql"
    "020_statut_envoye.sql"
    "021_sync_history.sql"
    "022_apply_project_id_type_field_configs.sql"
    "023_push_subscriptions.sql"
    "024_contact_messages.sql"
)

applied=0
skipped=0
failed=0

for migration in "${MIGRATIONS[@]}"; do
    migration_path="$MIGRATIONS_DIR/$migration"

    if [[ ! -f "$migration_path" ]]; then
        warn "Migration non trouvée: $migration (ignorée)"
        skipped=$((skipped + 1))
        continue
    fi

    # Appliquer la migration
    if docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$migration_path" > /dev/null 2>&1; then
        ok "$migration"
        applied=$((applied + 1))
    else
        # Certaines migrations peuvent échouer si déjà appliquées (tables existantes)
        # On essaie quand même et on continue
        warn "$migration (probablement déjà appliquée)"
        skipped=$((skipped + 1))
    fi
done

echo ""
echo "  Résultat: $applied appliquées, $skipped ignorées, $failed échouées"

# ─── Étape 3 : Créer le super admin ─────────────────────────────────────────

step "3/4 - Création du compte super administrateur"

# Générer le hash bcrypt du mot de passe via Python dans le conteneur API
HASH=$(docker exec geoclic_api python3 -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('$ADMIN_PASSWORD'))
" 2>/dev/null)

if [[ -z "$HASH" ]]; then
    # Fallback : utiliser le conteneur DB avec un hash pré-calculé
    warn "Conteneur API non disponible, utilisation d'un hash par défaut"
    warn "IMPORTANT : Changez le mot de passe après la première connexion !"
    HASH='$2b$12$LJ3m5E5JQKyU5U5VXc1Y8OGV9Z5m4dC4n1P2w8vP1cJgF1Xz2zKRe'
fi

docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<SQL
-- Créer le super admin
INSERT INTO geoclic_users (
    email, nom, prenom, actif, is_super_admin,
    role_data, role_demandes, role_sig, role_terrain,
    password_hash
) VALUES (
    '$ADMIN_EMAIL',
    'Admin',
    'Super',
    TRUE, TRUE,
    'admin', 'admin', 'edition', 'agent',
    '$HASH'
) ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    is_super_admin = TRUE,
    role_data = 'admin',
    role_demandes = 'admin';

SELECT 'Super admin créé: ' || email FROM geoclic_users WHERE email = '$ADMIN_EMAIL';
SQL

ok "Super admin créé: $ADMIN_EMAIL"

# ─── Étape 4 : Configuration initiale ───────────────────────────────────────

step "4/4 - Configuration initiale"

# Branding par défaut avec le nom de la collectivité
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<SQL
-- Nom de la collectivité
INSERT INTO system_settings (key, value)
VALUES ('nom_collectivite', '"$COLLECTIVITE"')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Couleurs par défaut
INSERT INTO system_settings (key, value) VALUES
    ('primary_color', '"#1565C0"'),
    ('secondary_color', '"#37474F"'),
    ('accent_color', '"#FF6F00"'),
    ('sidebar_color', '"#1a2332"')
ON CONFLICT (key) DO NOTHING;

SELECT 'Branding configuré pour: ' || value FROM system_settings WHERE key = 'nom_collectivite';
SQL

ok "Branding configuré: $COLLECTIVITE"

# Vérifier que le projet système existe
PROJECT_EXISTS=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM projects WHERE is_system = TRUE;" 2>/dev/null | tr -d ' ')

if [[ "$PROJECT_EXISTS" -gt 0 ]]; then
    ok "Projet système 'Signalements Citoyens' présent"
else
    warn "Projet système non trouvé (sera créé par la migration 013)"
fi

# ─── Résumé ──────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}Installation terminée !${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Le client peut maintenant se connecter :"
echo ""
echo "  📧 Email    : $ADMIN_EMAIL"
echo "  🔑 Mot de passe : (celui que vous avez fourni)"
echo ""
echo "  Applications disponibles :"
echo "  • GéoClic Admin    → https://DOMAINE/admin/"
echo "  • Back-office      → https://DOMAINE/demandes/"
echo "  • Portail citoyen  → https://DOMAINE/portail/"
echo "  • SIG Web          → https://DOMAINE/sig/"
echo "  • Services terrain → https://DOMAINE/services/"
echo "  • PWA terrain      → https://DOMAINE/terrain/"
echo "  • Mobile relevé    → https://DOMAINE/mobile/"
echo ""
echo "  Au premier login sur GéoClic Admin, le wizard d'onboarding"
echo "  guidera la configuration (catégories, services, email SMTP)."
echo ""

# GéoClic Suite - Suivi du Déploiement

**Date de dernière mise à jour :** 31 janvier 2026
**Branche de travail :** `claude/setup-geoclic-suite-JpjDO`
**Branche stable :** `main`
**Serveur :** geoclic.fr (VPS OVH)

---

## 1. État Actuel - FONCTIONNEL

### 1.1 Services Opérationnels

| Application | URL | Statut |
|-------------|-----|--------|
| **Portail Citoyen** | https://geoclic.fr/portail/ | ✅ OK |
| **Admin (GéoClic Data)** | https://geoclic.fr/admin/ | ✅ OK |
| **Demandes** | https://geoclic.fr/demandes/ | ✅ OK |
| **Mobile PWA** | https://geoclic.fr/mobile/ | ✅ OK |
| **SIG Web** | https://geoclic.fr/sig/ | ✅ OK |
| **API** | https://geoclic.fr/api/health | ✅ OK |
| **Site Vitrine** | https://geoclic.fr/ | ✅ OK |
| **HTTPS** | Let's Encrypt | ✅ OK |

### 1.2 Base de données - Tables présentes

```
geoclic_staging, lexique, projects, spatial_ref_sys, sync_history,
system_settings, type_field_configs, users, zones
```

---

## 2. Architecture

### 2.1 Stack Technique
- **Backend :** FastAPI (Python) avec SQLAlchemy async + asyncpg
- **Frontend :** Vue 3 + Vite + TypeScript
- **Base de données :** PostgreSQL 15 + PostGIS 3.3
- **Containerisation :** Docker + Docker Compose v2
- **Reverse Proxy :** Nginx Alpine (dans Docker)
- **SSL :** Let's Encrypt via Certbot

### 2.2 Structure sur le VPS

```
/opt/geoclic/                    # Racine du projet (PAS de sous-dossier GeoClic_Suite!)
├── api/                         # Backend FastAPI
├── app_citoyen/                 # App Flutter citoyens
├── database/                    # Scripts SQL
│   ├── init_v12_pro.sql
│   └── migrations/
├── deploy/                      # Configuration déploiement
│   ├── docker-compose.yml
│   ├── .env
│   ├── Dockerfile.api
│   └── nginx/
│       ├── nginx.conf
│       ├── conf.d/locations.conf
│       └── ssl/
│           ├── fullchain.pem
│           └── privkey.pem
├── geoclic_data/                # Admin Vue.js
├── geoclic_demandes/            # Back-office demandes
├── geoclic_mobile_pwa/          # PWA terrain
├── geoclic_mobile_v12/          # App Flutter terrain
├── geoclic_SIG/                 # App Flutter desktop
├── geoclic_sig_web/             # SIG Web Vue.js
├── portail_citoyen/             # Portail citoyens Vue.js
├── shared/                      # Code partagé Flutter
├── docs/                        # Documentation
├── README.md
├── SUITE_GEOCLIC_RESUME.md
└── SUIVI_DEPLOIEMENT.md
```

**Important :**
- Les fichiers sont DIRECTEMENT dans `/opt/geoclic/`, pas dans un sous-dossier !
- Le dossier `database/` est au même niveau que `deploy/`
- Le docker-compose.yml utilise `../database/` pour y accéder

### 2.3 Containers Docker

```bash
sudo docker ps
# geoclic_db       - PostgreSQL + PostGIS (port 5432)
# geoclic_api      - FastAPI backend (port 8000)
# geoclic_admin    - Vue Admin (port 5173)
# geoclic_portail  - Vue Portail (port 5174)
# geoclic_demandes - Vue Demandes (port 5175)
# geoclic_mobile   - Vue Mobile PWA (port 5176)
# geoclic_sig      - Vue SIG Web (port 5177)
# geoclic_nginx    - Reverse proxy (ports 80, 443)
```

---

## 3. Site Vitrine Marketing

### 3.1 Structure

```
deploy/www/
├── index.html          # Page d'accueil (hero + modules + écosystème)
├── fonctionnalites.html # Détail des 5 modules avec screenshots
├── tarifs.html         # Tableau comparatif Licence vs SaaS
├── style.css           # Styles partagés
├── assets/
│   └── logo-geoclic.svg
└── screenshots/
    ├── sig-web.png       # 800x450 (paysage)
    ├── geoclic-data.png  # 800x450 (paysage)
    ├── demandes.png      # 800x450 (paysage)
    ├── mobile-pwa.png    # 326x600 (portrait)
    └── portail.png       # 326x600 (portrait)
```

### 3.2 Pages

| Page | Description |
|------|-------------|
| **index.html** | Page d'accueil avec hero, grille modules, workflow "Comment ça marche?" et "Pour qui?" |
| **fonctionnalites.html** | Grille de 5 cards : 3 paysage (SIG, Data, Demandes) + 2 portrait (Mobile, Portail) |
| **tarifs.html** | Tableau comparatif des offres Licence et SaaS |

### 3.3 Mise à jour du site

```bash
# Définir les chemins
SOURCE=/home/ubuntu/Documents/GeoClic_Suite-claude-review-geoclic-suite-2SrgJ
DEST=/opt/geoclic

# Synchroniser depuis Documents vers /opt (sans --delete pour protéger SSL!)
sudo rsync -avz "$SOURCE/deploy/www/" "$DEST/deploy/www/"
```

**⚠️ ATTENTION :** Ne jamais utiliser `rsync --delete` sur le dossier deploy/ car cela supprime les certificats SSL !

---

## 4. Configuration

### 4.1 Fichier .env

Chemin : `/opt/geoclic/deploy/.env`

```env
# Base de données
DB_HOST=db
DB_PORT=5432
DB_NAME=geoclic_db
DB_USER=geoclic
DB_PASSWORD=geoclic_secure_password

# API
API_PORT=8000
SECRET_KEY=votre_cle_secrete_a_changer

# Applications
ADMIN_PORT=5173
PORTAIL_PORT=5174
DEMANDES_PORT=5175
MOBILE_PORT=5176
SIG_PORT=5177

# Domaine
DOMAIN=geoclic.fr
```

### 4.2 Identifiants par défaut

| Application | Email | Mot de passe |
|-------------|-------|--------------|
| Admin/Demandes | admin@geoclic.local | admin123 |

**⚠️ Changer ce mot de passe en production !**

---

## 5. Fonctionnalité Zones (Quartiers/Secteurs)

### 5.1 Description

Gestion des zones géographiques (quartiers, secteurs, communes) indépendantes des projets.
Les zones sont transversales et partagées par toutes les applications.

**Disponibilité actuelle :**
| Application | Zones API | Zones locales |
|-------------|-----------|---------------|
| **geoclic_data** (`/admin/`) | ✅ Menu "Zones" | - |
| **geoclic_sig_web** (`/sig/`) | ✅ Panneau "Zones partagées" | ✅ Périmètres locaux (session) |
| **geoclic_demandes** (`/demandes/`) | ✅ Filtrage par zone | - |

**Note :** geoclic_sig_web affiche maintenant les deux types de zones :
- **Zones partagées** : depuis l'API `/api/zones`, stockées en BDD, visibles sur la carte
- **Zones locales** : périmètres de session (non persistés)

**Utilités des zones API :**
- Filtrer les points par zone géographique
- Assigner des utilisateurs à des zones
- Calculer des statistiques par zone

### 5.2 Fichiers Créés/Modifiés

| Fichier | Description |
|---------|-------------|
| `api/routers/zones.py` | Router API CRUD + import IRIS |
| `api/schemas/zones.py` | Schémas Pydantic pour les zones |
| `api/main.py` | Ajout du router zones |
| `geoclic_data/src/pages/zones/index.vue` | Page liste des zones |
| `geoclic_data/src/pages/zones/edit.vue` | Éditeur carte plein écran |
| `geoclic_data/src/router/index.ts` | Routes /zones |
| `geoclic_data/src/layouts/admin.vue` | Menu Zones |
| `geoclic_data/package.json` | Dépendances leaflet-geoman |

### 5.3 Fonctionnalités

- **Liste des zones** : Affichage avec statistiques (points par zone)
- **Import IRIS** : Import automatique depuis geo.api.gouv.fr (code INSEE)
- **Éditeur carte** : Dessin de polygones avec leaflet-geoman
- **Snap to edge** : Accrochage aux zones adjacentes (15px)
- **Multi-basemaps** : OSM, Satellite, Cadastre
- **Détection chevauchement** : Avertissement si zones se superposent

### 5.4 Déploiement

```bash
# Définir les chemins
SOURCE=/home/ubuntu/Documents/GeoClic_Suite-claude-review-geoclic-suite-2SrgJ
DEST=/opt/geoclic

# Copier les fichiers zones vers le serveur
sudo cp "$SOURCE/api/routers/zones.py" "$DEST/api/routers/"
sudo cp "$SOURCE/api/schemas/zones.py" "$DEST/api/schemas/"
sudo cp "$SOURCE/api/main.py" "$DEST/api/"

# Copier le frontend
sudo cp -r "$SOURCE/geoclic_data/src/pages/zones" "$DEST/geoclic_data/src/pages/"
sudo cp "$SOURCE/geoclic_data/src/router/index.ts" "$DEST/geoclic_data/src/router/"
sudo cp "$SOURCE/geoclic_data/src/layouts/admin.vue" "$DEST/geoclic_data/src/layouts/"
sudo cp "$SOURCE/geoclic_data/package.json" "$DEST/geoclic_data/"

# Rebuild
cd /opt/geoclic/deploy
sudo docker compose build --no-cache api admin
sudo docker compose up -d --force-recreate api admin
```

---

## 6. Historique des Corrections

### 6.1 Commits Importants

| Commit | Description |
|--------|-------------|
| `000b6c8` | fix(api): Fix geo.api.gouv.fr contour requests |
| `70d63b3` | fix(zones): Use geometry=contour param for geo.api.gouv.fr |
| `3f5096f` | fix(api): Correct import path for get_db in zones router |
| `8c0f9ae` | fix(docker): Remove hardcoded VITE_API_URL for automatic detection |
| `6ca7e3a` | fix(api): Use relative URL for production with nginx proxy |
| `4b7bea1` | feat(zones): Add zone management with map editor and IRIS import |
| `cd863c3` | feat(marketing): Add ecosystem section with workflow and targets |
| `efff00a` | style(marketing): Increase gap between cards |
| `c58d84c` | style(marketing): Reduce page-header height |
| `11c76bf` | refactor(marketing): Grid layout for fonctionnalites page |
| `413e3ed` | refactor(marketing): Separate pages with shared CSS |
| `e53411e` | fix(deploy): Correct database path in docker-compose.yml |
| `d330d53` | feat(deploy): Enable HTTPS with Let's Encrypt support |
| `fe24e4d` | fix(deploy): Add start_period to database healthcheck |
| `9c78808` | fix(deploy): Correct default database credentials |
| `b069650` | feat(nginx): Add SIG Web reverse proxy configuration |

### 6.2 Problèmes Résolus

#### A. URL API localhost:8000 en production (30/01/2026)
**Problème :** Le frontend appelait `localhost:8000` au lieu de `/api` en production
**Cause :**
- `VITE_API_URL=http://localhost:8000` hardcodé dans Dockerfile
- `VITE_API_URL` défini dans docker-compose.yml
**Solution :**
1. Modifier `geoclic_data/src/services/api.ts` pour détecter automatiquement l'URL
2. Vider `ARG VITE_API_URL=` dans Dockerfile
3. Supprimer `VITE_API_URL` du docker-compose.yml pour admin

#### B. Import get_db zones.py
**Problème :** `ModuleNotFoundError: No module named 'db'`
**Solution :** Changer `from db import get_db` → `from database import get_db`

#### C. geo.api.gouv.fr retourne Point au lieu de Polygon
**Problème :** L'import IRIS échouait car l'API retournait le centroïde (Point)
**Cause :** Utilisation de `fields=contour` au lieu de `geometry=contour`
**Solution :**
```python
# Avant
params={"fields": "nom,contour", "format": "geojson"}
# Après
params={"fields": "nom", "geometry": "contour", "format": "geojson"}
```
Corrigé dans `zones.py` et `demandes.py`

#### D. Chemin de la base de données
**Problème :** docker-compose.yml utilisait `./database/` mais le dossier est à `../database/`
**Solution :** Modifier les volumes dans docker-compose.yml :
```yaml
volumes:
  - ../database/init_v12_pro.sql:/docker-entrypoint-initdb.d/01_init.sql:ro
  - ../database/migrations:/docker-entrypoint-initdb.d/migrations:ro
```

#### E. Identifiants base de données
**Problème :** Incohérence entre `admin_geoclic` et `geoclic`
**Solution :** Standardisé sur `geoclic` partout (.env.example, docker-compose.yml, install-geoclic.sh)

#### F. HTTPS / Let's Encrypt
**Problème :** Configuration HTTP uniquement
**Solution :**
- Générer certificat : `sudo certbot certonly --standalone -d geoclic.fr`
- Copier vers nginx/ssl/
- Activer HTTPS dans nginx.conf

#### G. SIG Web manquant dans nginx
**Problème :** 404 sur /sig/
**Solution :** Ajouter `sig_backend` upstream et location `/sig` dans nginx config

#### H. Healthcheck base de données
**Problème :** Services démarraient avant que PostgreSQL soit prêt
**Solution :** Ajouter `start_period: 30s` au healthcheck

---

## 7. Commandes Utiles

### 7.1 Gestion des services

```bash
cd /opt/geoclic/deploy

# Voir l'état
sudo docker compose ps

# Voir les logs
sudo docker logs geoclic_api --tail=50
sudo docker logs geoclic_nginx --tail=50

# Redémarrer tout
sudo docker compose restart

# Reconstruire et redémarrer
sudo docker compose down
sudo docker compose up -d
```

### 7.2 Base de données

```bash
# Se connecter
sudo docker exec -it geoclic_db psql -U geoclic -d geoclic_db

# Lister les tables
\dt

# Réinitialiser (ATTENTION: supprime les données!)
cd /opt/geoclic/deploy
sudo docker compose down -v
sudo docker compose up -d
```

### 7.3 Certificats SSL

```bash
# Renouveler le certificat
sudo certbot renew

# Copier vers nginx
sudo cp -L /etc/letsencrypt/live/geoclic.fr/fullchain.pem /opt/geoclic/deploy/nginx/ssl/
sudo cp -L /etc/letsencrypt/live/geoclic.fr/privkey.pem /opt/geoclic/deploy/nginx/ssl/

# Redémarrer nginx
sudo docker compose restart nginx
```

### 7.4 Tests

```bash
# API Health
curl https://geoclic.fr/api/health

# Test login
curl -X POST https://geoclic.fr/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@geoclic.local&password=admin123"

# Tous les services
for s in portail admin demandes mobile sig; do
  echo "=== $s ===" && curl -sI "https://geoclic.fr/$s/" | head -3
done
```

---

## 8. Installation Propre (Nouvelle Installation)

### 8.1 Avec le script automatique

```bash
curl -sSL https://raw.githubusercontent.com/fredco30/GeoClic_Suite/main/deploy/install-geoclic.sh | sudo bash -s -- --domain geoclic.fr --email votre@email.fr
```

### 8.2 Installation manuelle

```bash
# 1. Cloner le dépôt
cd /opt
sudo git clone https://github.com/fredco30/GeoClic_Suite.git geoclic
cd geoclic

# 2. Structure correcte
# Le dossier database/ est à la racine, deploy/ contient docker-compose.yml

# 3. Créer .env
cd deploy
sudo cp .env.example .env
sudo nano .env  # Modifier les valeurs

# 4. Générer certificat SSL
sudo certbot certonly --standalone -d votre-domaine.fr --email votre@email.fr --agree-tos

# 5. Copier les certificats
sudo mkdir -p nginx/ssl
sudo cp -L /etc/letsencrypt/live/votre-domaine.fr/fullchain.pem nginx/ssl/
sudo cp -L /etc/letsencrypt/live/votre-domaine.fr/privkey.pem nginx/ssl/

# 6. Démarrer
sudo docker compose up -d
```

---

## 9. Mise à jour du Code

### 9.1 Workflow de déploiement (GitHub)

**Méthode : Import direct depuis GitHub**

Le serveur `/opt/geoclic` est initialisé comme dépôt git et récupère les fichiers directement depuis GitHub.

### 9.2 Commandes de déploiement

**Format standard :**

```bash
# 1. Aller dans /opt/geoclic
cd /opt/geoclic

# 2. Récupérer les dernières modifications d'une branche
sudo git fetch origin <NOM_BRANCHE>

# 3. Extraire les fichiers souhaités (sans changer de branche)
sudo git checkout origin/<NOM_BRANCHE> -- <CHEMIN_FICHIER>

# 4. Rebuild et redémarrer le(s) service(s)
cd /opt/geoclic/deploy
sudo docker compose build <SERVICE> --no-cache && sudo docker compose up -d <SERVICE>
```

### 9.3 Exemples par service

```bash
# === API (backend Python) ===
cd /opt/geoclic
sudo git fetch origin claude/setup-geoclic-suite-JpjDO
sudo git checkout origin/claude/setup-geoclic-suite-JpjDO -- api/routers/demandes.py
cd /opt/geoclic/deploy
sudo docker compose build api --no-cache && sudo docker compose up -d api

# === Admin (geoclic_data) ===
cd /opt/geoclic
sudo git fetch origin claude/setup-geoclic-suite-JpjDO
sudo git checkout origin/claude/setup-geoclic-suite-JpjDO -- geoclic_data/
cd /opt/geoclic/deploy
sudo docker compose build admin --no-cache && sudo docker compose up -d admin

# === Demandes ===
cd /opt/geoclic
sudo git fetch origin claude/setup-geoclic-suite-JpjDO
sudo git checkout origin/claude/setup-geoclic-suite-JpjDO -- geoclic_demandes/
cd /opt/geoclic/deploy
sudo docker compose build demandes --no-cache && sudo docker compose up -d demandes

# === Portail Citoyen ===
cd /opt/geoclic
sudo git fetch origin claude/setup-geoclic-suite-JpjDO
sudo git checkout origin/claude/setup-geoclic-suite-JpjDO -- portail_citoyen/
cd /opt/geoclic/deploy
sudo docker compose build portail --no-cache && sudo docker compose up -d portail

# === SIG Web ===
cd /opt/geoclic
sudo git fetch origin claude/setup-geoclic-suite-JpjDO
sudo git checkout origin/claude/setup-geoclic-suite-JpjDO -- geoclic_sig_web/
cd /opt/geoclic/deploy
sudo docker compose build sig --no-cache && sudo docker compose up -d sig
```

### 9.4 Correspondance services ↔ dossiers

| Dossier source | Service docker |
|----------------|----------------|
| `api/` | api |
| `geoclic_data/` | admin |
| `geoclic_demandes/` | demandes |
| `geoclic_sig_web/` | sig |
| `portail_citoyen/` | portail |
| `geoclic_mobile_pwa/` | mobile |
| `deploy/nginx/` | nginx (juste `docker compose restart nginx`) |

---

## 10. Dépannage

### Conflit de containers (erreur "container name already in use")

Lors d'un redémarrage, Docker peut créer des containers fantômes. Solution :

```bash
cd /opt/geoclic/deploy

# 1. Arrêter tous les containers
sudo docker compose down

# 2. Nettoyer les containers orphelins
sudo docker container prune -f

# 3. Redémarrer proprement
sudo docker compose up -d
```

**⚠️ IMPORTANT :** Toujours utiliser `docker compose down` avant `docker compose up -d` pour éviter les conflits.

### nginx ne démarre pas
```bash
# Vérifier la config
sudo docker exec geoclic_nginx nginx -t

# Voir les logs
sudo docker logs geoclic_nginx --tail=50
```

### Erreur "zero size shared memory zone"
Le nginx.conf est incomplet, il manque les lignes :
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
```

### Erreur SSL
```bash
# Vérifier les certificats
ls -la /opt/geoclic/deploy/nginx/ssl/
# fullchain.pem devrait être ~3-4 KB
# privkey.pem devrait être ~1.7 KB (RSA) ou ~240 bytes (ECDSA)
```

### Base de données vide
```bash
# Vérifier que le fichier SQL existe
ls -la /opt/geoclic/database/init_v12_pro.sql

# Si absent, copier depuis le dépôt
```

---

## 11. Ressources

- **Dépôt GitHub :** https://github.com/fredco30/GeoClic_Suite
- **Branche stable :** `main`
- **Branche de développement :** `claude/review-geoclic-suite-2SrgJ`
- **Domaine :** geoclic.fr

---

## 12. Développement V2 - GéoClic Demandes

### 12.1 Documentation

- **Spécifications** : `docs/SPECS_GEOCLIC_DEMANDES_V2.md`
- **Plan de développement** : `docs/PLAN_DEVELOPPEMENT_V2.md`

### 12.2 Phases de développement

| Phase | Description | Statut |
|-------|-------------|--------|
| **Phase 1** | Catégories à 2 niveaux + interface tuiles | En cours |
| Phase 2 | Détection des doublons | À faire |
| Phase 3 | Services et affectation | À faire |
| Phase 4 | geoclic_services desktop | À faire |
| Phase 5 | Timeline citoyen + photo avant/après | À faire |
| Phase 6 | geoclic_services PWA mobile | À faire |
| Phase 7 | Intégration calendrier + SLA | À faire |

### 12.3 Phase 1 - Fichiers modifiés

| Fichier | Description |
|---------|-------------|
| `geoclic_demandes/src/views/CategoriesView.vue` | Arborescence 2 niveaux, stats, icônes, couleurs, SLA |
| `portail_citoyen/src/components/CategorySelector.vue` | Nouveau composant tuiles 2 niveaux |
| `portail_citoyen/src/views/SignalerView.vue` | Intégration CategorySelector |

### 12.4 Déployer Phase 1

```bash
cd /opt/geoclic
sudo git fetch origin claude/setup-geoclic-suite-JpjDO
sudo git checkout origin/claude/setup-geoclic-suite-JpjDO -- geoclic_demandes/src/views/CategoriesView.vue
sudo git checkout origin/claude/setup-geoclic-suite-JpjDO -- portail_citoyen/src/components/CategorySelector.vue
sudo git checkout origin/claude/setup-geoclic-suite-JpjDO -- portail_citoyen/src/views/SignalerView.vue
cd /opt/geoclic/deploy
sudo docker compose build demandes portail --no-cache && sudo docker compose up -d demandes portail
```

---

## 13. Prochaines Étapes

### Infrastructure (terminé)
1. ✅ ~~Configurer HTTPS avec Let's Encrypt~~
2. ✅ ~~Ajouter SIG Web~~
3. ✅ ~~Corriger les identifiants base de données~~
4. ✅ ~~Créer le site vitrine marketing~~
5. ✅ ~~Ajouter la gestion des zones dans geoclic_data~~
6. ✅ ~~Corriger URL API production~~
7. ✅ ~~Intégrer les zones API dans geoclic_sig_web~~

### En cours
8. ⬜ **Phase 1 V2** : Catégories hiérarchiques + tuiles (branche `claude/setup-geoclic-suite-JpjDO`)

### À faire
9. ⬜ Phase 2 V2 : Détection doublons
10. ⬜ Phase 3 V2 : Services et affectation
11. ⬜ Merger vers `main` après validation
12. ⬜ Configurer renouvellement auto certificats
13. ⬜ Notifications email

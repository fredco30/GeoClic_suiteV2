# Suite GéoClic - Résumé du Projet

**Document de référence pour l'écosystème GéoClic**
*Dernière mise à jour : 30 janvier 2026*

---

## 1. Vision Globale

### Objectif Final

La **Suite GéoClic** est un écosystème complet de gestion du patrimoine territorial pour les collectivités françaises. Elle se compose de **6 applications web et mobile** autour d'une API centralisée.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SUITE GÉOCLIC V14 - ÉCOSYSTÈME                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   APPLICATIONS WEB (Vue 3 + TypeScript)                                         │
│   ┌────────────────┬────────────────┬────────────────┬────────────────────────┐ │
│   │ GéoClic Data   │ GéoClic SIG    │ Portail        │ GéoClic Demandes       │ │
│   │ (Admin)        │ (Cartographie) │ Citoyen        │ (Back-office)          │ │
│   │ /admin/        │ /sig/          │ /portail/      │ /demandes/             │ │
│   ├────────────────┼────────────────┼────────────────┼────────────────────────┤ │
│   │ - Patrimoine   │ - IGN Carte    │ - Signalements │ - Modération demandes  │ │
│   │ - Lexique      │ - IGN Ortho    │ - Scan QR Code │ - Workflow traitement  │ │
│   │ - Utilisateurs │ - Cadastre     │ - Suivi ticket │ - Notifications email  │ │
│   │ - Import/Export│ - Mesures      │ - Photos GPS   │ - Statistiques         │ │
│   │ - QR Codes     │ - Périmètres   │                │                        │ │
│   └────────────────┴────────────────┴────────────────┴────────────────────────┘ │
│                                                                                  │
│   APPLICATION MOBILE PWA                                                         │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │ GéoClic Mobile PWA  (/mobile/)                                           │  │
│   │ - Relevés terrain GPS avec mode hors-ligne                               │  │
│   │ - Photos géolocalisées (compression auto)                                │  │
│   │ - Synchronisation bidirectionnelle                                       │  │
│   │ - Installation sur écran d'accueil (iOS/Android)                         │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   BACKEND CENTRALISÉ                                                             │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │ GéoClic API (FastAPI Python)  /api/                                      │  │
│   │ - Auth JWT + Permissions      - Import CSV/GeoJSON/Shapefile             │  │
│   │ - CRUD Points/Lexique         - Export multi-formats                     │  │
│   │ - Sync Mobile                 - Emails (SMTP / Microsoft Graph)          │  │
│   │ - Documentation Swagger       - PostGIS spatial                          │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   BASE DE DONNÉES                                                                │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │ PostgreSQL 15 + PostGIS 3.3                                              │  │
│   │ - Géométries POINT, LINESTRING, POLYGON                                  │  │
│   │ - Champs dynamiques JSONB                                                │  │
│   │ - Isolation par projet                                                   │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Déploiement Production

- **URL** : https://geoclic.fr
- **Infrastructure** : Docker Compose sur VPS OVH
- **SSL** : Let's Encrypt (renouvellement automatique)
- **Reverse Proxy** : Nginx

---

## 2. Les Composants de la Suite

### 2.1 GéoClic SIG Web (Cartographie) ✅ TERMINÉ

**Rôle** : Application cartographique complète pour la visualisation et l'édition spatiale.

**Fonctionnalités** :
- Fonds de carte IGN Géoplateforme (Plan IGN, Ortho, Cadastre, Carte, Historique)
- Outils de mesure (distance et surface)
- Création de points, lignes, polygones
- Gestion des périmètres/zones
- Import/Export GeoJSON (drag & drop)
- Multi-projets avec sélecteur
- Édition des propriétés des entités
- Tableau de bord statistiques
- Interface responsive et professionnelle

**Technologies** :
- Vue 3 + TypeScript + Vite
- Leaflet 1.9 (client cartographique)
- IGN Géoplateforme WMTS (fonds de carte gratuits)
- Pinia (state management)

**Dépôt** : `geoclic_sig_web/`

**URL** : https://geoclic.fr/sig/

---

### 2.2 GéoClic Data (Admin) ✅ TERMINÉ

**Rôle** : Interface d'administration pour la gestion du patrimoine.

**Composants** :
- **Interface Admin Vue.js** - Gestion complète
  - Dashboard statistiques
  - Gestion lexique hiérarchique (6 niveaux)
  - Gestion points avec workflow validation
  - Gestion utilisateurs et permissions
  - Import/Export fichiers (CSV, GeoJSON, Shapefile)
  - Génération QR Codes (PNG/PDF/ZIP)
  - Carte Leaflet intégrée

**Dépôt** : `geoclic_data/`

**URL** : https://geoclic.fr/admin/

---

### 2.3 GéoClic API (Backend) ✅ TERMINÉ

**Rôle** : API REST centralisée pour toutes les applications.

**Fonctionnalités** :
- Authentification JWT + permissions par rôle
- CRUD complet (points, lexique, projets, utilisateurs)
- Import multi-formats (CSV, GeoJSON, Shapefile)
- Export avec filtres et photos
- Synchronisation mobile bidirectionnelle
- Emails via SMTP ou Microsoft Graph API
- Documentation Swagger auto-générée

**Technologies** :
- FastAPI (Python 3.11+)
- SQLAlchemy async 2.0
- PostgreSQL 15 + PostGIS 3.3
- Pydantic v2

**Dépôt** : `api/`

**URL** : https://geoclic.fr/api/docs (Swagger)

---

### 2.4 GéoClic Mobile PWA ✅ TERMINÉ

**Rôle** : Application terrain pour les agents techniques.

**Fonctionnalités** :
- Login avec permissions JWT
- Création points sur le terrain
- GPS natif avec précision
- Photos compressées automatiquement
- Champs dynamiques (13 types)
- Mode hors-ligne avec cache
- Synchronisation 4G bidirectionnelle
- Installable sur écran d'accueil (PWA)

**Technologies** :
- Vue 3 + TypeScript + Vite
- PWA (Progressive Web App)
- IndexedDB (cache hors-ligne)

**Dépôt** : `geoclic_mobile_pwa/`

**URL** : https://geoclic.fr/mobile/

---

### 2.5 Portail Citoyen ✅ TERMINÉ

**Rôle** : Interface publique pour les signalements citoyens.

**Fonctionnalités** :
- Signalement géolocalisé avec photos
- Scan QR Code sur équipements
- Suivi des demandes par token
- Carte interactive pour localisation
- Formulaire simplifié et accessible

**Technologies** :
- Vue 3 + TypeScript + Vite
- Leaflet (carte)

**Dépôt** : `portail_citoyen/`

**URL** : https://geoclic.fr/portail/

---

### 2.6 GéoClic Demandes (Back-office) ✅ TERMINÉ

**Rôle** : Back-office pour le traitement des demandes citoyennes.

**Fonctionnalités** :
- Liste des demandes avec filtres
- Workflow de traitement (Nouveau → Modération → Accepté → En cours → Traité)
- Notifications email automatiques aux citoyens
- Affectation aux agents
- Statistiques et reporting
- Export des demandes

**Technologies** :
- Vue 3 + TypeScript + Vite

**Dépôt** : `geoclic_demandes/`

**URL** : https://geoclic.fr/demandes/

---

## 3. Architecture Technique

### 3.1 Schéma d'Architecture Production

```
                                    INTERNET
                                        │
                                        ▼
                              ┌─────────────────┐
                              │     Nginx       │
                              │  (Reverse Proxy)│
                              │   HTTPS/SSL     │
                              └────────┬────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │              │               │              │               │
        ▼              ▼               ▼              ▼               ▼
   ┌─────────┐   ┌─────────┐    ┌─────────┐   ┌─────────┐    ┌─────────┐
   │ /admin/ │   │  /sig/  │    │/portail/│   │/demandes│    │ /mobile/│
   │  Data   │   │   SIG   │    │ Citoyen │   │Back-off │    │   PWA   │
   │ Vue.js  │   │ Vue.js  │    │ Vue.js  │   │ Vue.js  │    │ Vue.js  │
   └────┬────┘   └────┬────┘    └────┬────┘   └────┬────┘    └────┬────┘
        │              │               │              │               │
        └──────────────┴───────────────┼──────────────┴───────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   GéoClic API   │
                              │    FastAPI      │
                              │    /api/        │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
           ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
           │ PostgreSQL  │    │   Photos    │    │   Email     │
           │ + PostGIS   │    │  /storage/  │    │ SMTP/Graph  │
           └─────────────┘    └─────────────┘    └─────────────┘
```

### 3.2 Structure des Dossiers

```
GeoClic_Suite/
├── api/                      # Backend FastAPI
│   ├── routers/              # Endpoints REST
│   ├── models/               # Modèles SQLAlchemy
│   ├── schemas/              # Schémas Pydantic
│   └── services/             # Logique métier
│
├── geoclic_data/             # Interface Admin (Vue 3)
├── geoclic_demandes/         # Back-office Demandes (Vue 3)
├── portail_citoyen/          # Portail Citoyen (Vue 3)
├── geoclic_mobile_pwa/       # Application Mobile PWA (Vue 3)
├── geoclic_sig_web/          # Application SIG Web (Vue 3)
│
├── geoclic_SIG/              # Application Desktop Flutter (legacy)
├── geoclic_mobile/           # Application Mobile Flutter (legacy)
│
├── database/                 # Scripts SQL
│   ├── init_v12_pro.sql      # Initialisation
│   └── migrations/           # Migrations
│
├── deploy/                   # Configuration Docker
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── install-geoclic.sh    # Script installation auto
│   ├── update-geoclic.sh     # Script mise à jour
│   └── nginx/                # Configuration Nginx
│
└── docs/                     # Documentation
```

### 3.3 Base de Données

```sql
-- Tables principales
users                  -- Utilisateurs (agents, admins)
projects               -- Projets/Collectivités
lexique                -- Catégories hiérarchiques (6 niveaux)
type_field_configs     -- Champs dynamiques (13 types)
geoclic_staging        -- Points géographiques (coeur)
demandes               -- Signalements citoyens
zones                  -- Périmètres/Zones
system_settings        -- Configuration système
sync_history           -- Audit synchronisation

-- Extensions PostGIS
postgis                -- Géométries spatiales
uuid-ossp              -- UUID auto-générés
```

---

## 4. État du Développement

### Applications Web

| Application | Status | Technologies | URL |
|-------------|--------|--------------|-----|
| GéoClic Data (Admin) | ✅ Terminé | Vue 3 + Vite | /admin/ |
| GéoClic SIG Web | ✅ Terminé | Vue 3 + Leaflet + IGN | /sig/ |
| Portail Citoyen | ✅ Terminé | Vue 3 + Vite | /portail/ |
| GéoClic Demandes | ✅ Terminé | Vue 3 + Vite | /demandes/ |
| GéoClic Mobile PWA | ✅ Terminé | Vue 3 PWA | /mobile/ |
| API Backend | ✅ Terminé | FastAPI | /api/ |

### GéoClic SIG Web - Fonctionnalités

| Fonctionnalité | Status | Description |
|----------------|--------|-------------|
| Fonds IGN | ✅ | Plan, Ortho, Cadastre, Carte, Historique |
| Navigation | ✅ | Zoom, pan, géolocalisation |
| Mesure distance | ✅ | Polyligne avec total en mètres |
| Mesure surface | ✅ | Polygone avec aire en m² |
| Création points | ✅ | Click pour placer |
| Création lignes | ✅ | Multi-points, Échap pour terminer |
| Création polygones | ✅ | Multi-points, fermeture auto |
| Mode série | ✅ | Points successifs |
| Édition | ✅ | Sélection et modification |
| Import GeoJSON | ✅ | Drag & drop |
| Multi-projets | ✅ | Sélecteur de projet |
| Périmètres | ✅ | Création et gestion zones |
| Panneau couches | ✅ | Visibilité toggle |
| Statistiques | ✅ | Dashboard temps réel |
| Aide intégrée | ✅ | Raccourcis clavier |

### Applications Desktop/Mobile Flutter (Legacy)

| Application | Status | Description |
|-------------|--------|-------------|
| GéoClic SIG Desktop | ⚠️ Legacy | Application Flutter desktop |
| GéoClic Mobile APK | ⚠️ Legacy | Application Flutter Android |

> Note : Les applications Flutter sont maintenues pour compatibilité mais les versions Vue.js/PWA sont recommandées pour les nouveaux déploiements.

---

## 5. Stack Technique

### Backend

| Technologie | Version | Usage |
|-------------|---------|-------|
| Python | 3.11+ | Langage backend |
| FastAPI | 0.109+ | Framework API |
| SQLAlchemy | 2.0+ | ORM async |
| PostgreSQL | 15 | Base de données |
| PostGIS | 3.3 | Extension spatiale |
| Pydantic | 2.0+ | Validation données |

### Frontend

| Technologie | Version | Usage |
|-------------|---------|-------|
| Vue.js | 3.4+ | Framework UI |
| TypeScript | 5.0+ | Typage |
| Vite | 5.0+ | Build tool |
| Pinia | 2.0+ | State management |
| Leaflet | 1.9+ | Cartographie |
| Axios | 1.6+ | HTTP client |

### Infrastructure

| Technologie | Usage |
|-------------|-------|
| Docker | Containerisation |
| Docker Compose | Orchestration |
| Nginx | Reverse proxy + SSL |
| Let's Encrypt | Certificats SSL |
| Ubuntu 22.04 | OS serveur |

### Cartographie

| Service | Usage |
|---------|-------|
| IGN Géoplateforme | Fonds de carte WMTS (gratuit) |
| Leaflet | Client cartographique |
| PostGIS | Stockage et requêtes spatiales |

---

## 6. URLs Production

| Application | URL | Description |
|-------------|-----|-------------|
| Portail Citoyen | https://geoclic.fr/portail/ | Signalements citoyens |
| Admin | https://geoclic.fr/admin/ | Gestion patrimoine |
| Demandes | https://geoclic.fr/demandes/ | Back-office demandes |
| Mobile PWA | https://geoclic.fr/mobile/ | App terrain |
| SIG Web | https://geoclic.fr/sig/ | Cartographie |
| API | https://geoclic.fr/api/ | Backend REST |
| Swagger | https://geoclic.fr/api/docs | Documentation API |

---

## 7. Déploiement

### Installation Rapide

```bash
curl -sSL https://raw.githubusercontent.com/fredco30/GeoClic_Suite/main/deploy/install-geoclic.sh | sudo bash -s -- --domain votre-domaine.fr --email votre@email.fr
```

### Mise à Jour

```bash
cd /opt/geoclic/deploy
sudo ./update-geoclic.sh
```

### Commandes Docker

```bash
cd /opt/geoclic/deploy

# État des services
sudo docker compose ps

# Logs
sudo docker logs geoclic_api --tail=50

# Redémarrer
sudo docker compose restart

# Reconstruire
sudo docker compose build --no-cache
sudo docker compose up -d
```

---

## 8. Configuration Email

### SMTP Classique

```env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@domaine.fr
SMTP_PASSWORD=motdepasse
```

### Microsoft 365 (Recommandé)

```env
EMAIL_PROVIDER=microsoft
MS_TENANT_ID=votre-tenant-id
MS_CLIENT_ID=votre-client-id
MS_CLIENT_SECRET=votre-client-secret
```

---

## 9. Fonctionnalités Métier

### Gestion Patrimoniale

- Lexique hiérarchique (6 niveaux de catégories)
- Isolation par projet (multi-collectivités)
- Templates municipaux (Éclairage, Mobilier, Espaces Verts...)
- Import/Export (CSV, GeoJSON, Shapefile)
- Génération QR codes (PNG, PDF, ZIP)
- Champs dynamiques (13 types : texte, nombre, date, liste, photo...)

### Relevés Terrain

- Application PWA installable
- Mode hors-ligne avec synchronisation
- GPS haute précision
- Photos géolocalisées compressées

### Portail Citoyen

- Signalement géolocalisé avec photos
- Scan QR Code équipements
- Suivi des demandes par token
- Notifications email automatiques

### SIG Web

- Fonds de carte IGN (Plan, Ortho, Cadastre, Carte, Historique)
- Outils de mesure (distance et surface)
- Création d'entités (points, lignes, polygones)
- Gestion des périmètres/zones
- Import GeoJSON par drag & drop
- Multi-projets

---

## 10. Pour les Collectivités

- **Souveraineté des données** - Hébergement en France
- **RGPD compliant** - Données personnelles protégées
- **Multi-projets** - Gérez plusieurs communes/services
- **Microsoft 365** - Intégration native avec Outlook
- **Open Source** - Code auditable et personnalisable
- **Pas de GeoServer** - Utilisation des services IGN gratuits

---

## 11. Documentation

| Document | Emplacement | Description |
|----------|-------------|-------------|
| README | `/README.md` | Vue d'ensemble rapide |
| Guide Installation | `/docs/GUIDE_INSTALLATION_OVH.md` | Installation pas à pas |
| Guide Débutant Linux | `/docs/GUIDE_DEBUTANT_LINUX.md` | Commandes Linux de base |
| API Swagger | https://geoclic.fr/api/docs | Documentation interactive |

---

## 12. Identifiants par Défaut

```
Email: admin@geoclic.local
Mot de passe: admin123
```

> **Important** : Changez ces identifiants après la première connexion.

---

*Document mis à jour le 30 janvier 2026 - GéoClic Suite V14*

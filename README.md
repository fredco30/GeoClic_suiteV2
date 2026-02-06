# GéoClic Suite V14

Solution souveraine de gestion de données territoriales pour les collectivités françaises.

> **Statut** : Déploiement HTTPS complet sur geoclic.fr
> **Dernière mise à jour** : 30 janvier 2026

---

## Installation Rapide (VPS)

```bash
# Installation automatique avec HTTPS
curl -sSL https://raw.githubusercontent.com/fredco30/GeoClic_Suite/main/deploy/install-geoclic.sh | sudo bash -s -- --domain votre-domaine.fr --email votre@email.fr
```

---

## Structure du projet

```
GeoClic_Suite/
├── api/                      # Backend FastAPI
├── geoclic_data/             # Interface Admin Web (Vue 3)
├── geoclic_demandes/         # Back-office Demandes Citoyens (Vue 3)
├── portail_citoyen/          # Portail Citoyen Web (Vue 3)
├── geoclic_mobile_pwa/       # Application Mobile PWA (Vue 3)
├── geoclic_sig_web/          # Application SIG cartographique (Vue 3)
├── database/                 # Scripts SQL (init + migrations)
│   ├── init_v12_pro.sql
│   └── migrations/
├── deploy/                   # Configuration Docker
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── install-geoclic.sh
│   ├── update-geoclic.sh
│   └── nginx/
└── docs/                     # Documentation
```

---

## Applications et URLs

| Application | URL | Description |
|-------------|-----|-------------|
| **Portail Citoyen** | https://geoclic.fr/portail/ | Signalements citoyens |
| **Admin** | https://geoclic.fr/admin/ | Gestion patrimoine |
| **Demandes** | https://geoclic.fr/demandes/ | Back-office demandes |
| **Mobile PWA** | https://geoclic.fr/mobile/ | App terrain PWA |
| **SIG Web** | https://geoclic.fr/sig/ | Cartographie avancée |
| **API** | https://geoclic.fr/api/ | Backend REST |
| **Swagger** | https://geoclic.fr/api/docs | Documentation API |

---

## Stack Technique

- **Backend :** FastAPI (Python 3.11+) + SQLAlchemy async 2.0
- **Frontend :** Vue 3 + Vite + TypeScript + Pinia
- **Cartographie :** Leaflet + IGN Géoplateforme (fonds de carte gratuits)
- **Base de données :** PostgreSQL 15 + PostGIS 3.3
- **Containerisation :** Docker + Docker Compose v2
- **Reverse Proxy :** Nginx
- **SSL :** Let's Encrypt (renouvellement automatique)

---

## Démarrage rapide (développement)

### Prérequis
- Docker & Docker Compose v2
- Node.js 18+ (pour le développement)

### Lancer les services

```bash
cd deploy
docker compose up -d
```

### Identifiants par défaut
```
Email: admin@geoclic.local
Mot de passe: admin123
```

---

## Déploiement Production (HTTPS)

### Option 1 : Script automatique

```bash
curl -sSL https://raw.githubusercontent.com/fredco30/GeoClic_Suite/main/deploy/install-geoclic.sh | sudo bash -s -- --domain geoclic.fr --email admin@geoclic.fr
```

### Option 2 : Manuel

```bash
# 1. Cloner
git clone https://github.com/fredco30/GeoClic_Suite.git /opt/geoclic
cd /opt/geoclic/deploy

# 2. Configurer
cp .env.example .env
nano .env

# 3. Certificat SSL
sudo certbot certonly --standalone -d votre-domaine.fr

# 4. Copier certificats
sudo cp -L /etc/letsencrypt/live/votre-domaine.fr/fullchain.pem nginx/ssl/
sudo cp -L /etc/letsencrypt/live/votre-domaine.fr/privkey.pem nginx/ssl/

# 5. Démarrer
sudo docker compose up -d
```

### Mise à jour

```bash
cd /opt/geoclic/deploy
sudo ./update-geoclic.sh
```

---

## Fonctionnalités

### Gestion Patrimoniale
- Lexique hiérarchique (6 niveaux de catégories)
- Isolation par projet (multi-collectivités)
- Templates municipaux (Eclairage, Mobilier, Espaces Verts...)
- Import/Export (CSV, GeoJSON, Shapefile)
- Génération QR codes (PNG, PDF, ZIP)
- Champs dynamiques (13 types)

### Relevés Terrain (Mobile PWA)
- Application PWA installable (iOS/Android/Web)
- Mode hors-ligne avec synchronisation
- GPS haute précision et photos géolocalisées
- Formulaires dynamiques

### Portail Citoyen
- Signalement géolocalisé avec photos
- Scan QR Code sur équipements
- Suivi des demandes par token
- Notifications email automatiques

### SIG Web (Cartographie)
- Fonds de carte IGN Géoplateforme (Plan, Ortho, Cadastre, Carte, Historique)
- Outils de mesure (distance et surface)
- Création d'entités (points, lignes, polygones)
- Gestion des périmètres/zones
- Import GeoJSON par drag & drop
- Multi-projets avec sélecteur
- Édition des propriétés
- Tableau de bord statistiques
- Raccourcis clavier et aide intégrée

---

## Configuration Email

### SMTP classique
```env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@domaine.fr
SMTP_PASSWORD=motdepasse
```

### Microsoft 365 (recommandé pour mairies)
```env
EMAIL_PROVIDER=microsoft
MS_TENANT_ID=votre-tenant-id
MS_CLIENT_ID=votre-client-id
MS_CLIENT_SECRET=votre-client-secret
```

---

## Commandes Utiles

```bash
cd /opt/geoclic/deploy

# Voir l'état
sudo docker compose ps

# Logs
sudo docker logs geoclic_api --tail=50

# Redémarrer
sudo docker compose restart

# Reconstruire
sudo docker compose build --no-cache
sudo docker compose up -d

# Mise à jour depuis GitHub
sudo ./update-geoclic.sh
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [SUITE_GEOCLIC_RESUME.md](./SUITE_GEOCLIC_RESUME.md) | Résumé complet du projet |
| [docs/GUIDE_INSTALLATION_OVH.md](./docs/GUIDE_INSTALLATION_OVH.md) | Guide d'installation pas à pas |
| [docs/GUIDE_DEBUTANT_LINUX.md](./docs/GUIDE_DEBUTANT_LINUX.md) | Commandes Linux de base |
| API Swagger | https://geoclic.fr/api/docs |

---

## Pour les collectivités

- **Souveraineté des données** - Hébergement en France
- **RGPD compliant** - Données personnelles protégées
- **Multi-projets** - Gérez plusieurs communes/services
- **Microsoft 365** - Intégration native avec Outlook
- **Open Source** - Code auditable et personnalisable
- **Sans licence** - Utilisation des services IGN gratuits (pas de GeoServer)

---

## Licence

Développé pour les collectivités françaises.

---

*GéoClic Suite V14 - Gestion territoriale simplifiée*

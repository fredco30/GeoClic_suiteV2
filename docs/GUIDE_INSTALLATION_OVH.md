# Guide d'Installation GéoClic Suite V14 sur OVH

## Pour les Débutants - Pas à Pas

Ce guide vous accompagne dans l'installation complète de GéoClic Suite sur un serveur OVH.
Aucune connaissance préalable en Linux n'est requise.

---

## Table des Matières

1. [Comprendre ce qu'on va faire](#1-comprendre-ce-quon-va-faire)
2. [Commander un serveur OVH](#2-commander-un-serveur-ovh)
3. [Se connecter au serveur](#3-se-connecter-au-serveur)
4. [Préparer le serveur](#4-préparer-le-serveur)
5. [Installer GéoClic Suite](#5-installer-géoclic-suite)
6. [Configurer le nom de domaine](#6-configurer-le-nom-de-domaine)
7. [Configurer les notifications email](#7-configurer-les-notifications-email)
8. [Configurer le Portail Citoyen](#8-configurer-le-portail-citoyen)
9. [Premiers pas après installation](#9-premiers-pas-après-installation)
10. [Maintenance et sauvegardes](#10-maintenance-et-sauvegardes)
11. [Résolution des problèmes](#11-résolution-des-problèmes)

---

## 1. Comprendre ce qu'on va faire

### Qu'est-ce qu'un serveur ?

Un serveur est un ordinateur qui reste allumé 24h/24 et qui est accessible depuis Internet.
C'est sur ce serveur que GéoClic Suite va fonctionner.

### Qu'est-ce qu'OVH ?

OVH est une entreprise française qui loue des serveurs. Vous payez un abonnement mensuel
(environ 5-15€/mois) et vous avez votre propre serveur.

### Ce qu'on va installer

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Votre Serveur OVH                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    APPLICATIONS WEB (Vue.js)                     │  │
│   ├────────────┬────────────┬────────────┬────────────┬────────────┤  │
│   │ GéoClic    │  SIG Web   │  Portail   │  GéoClic   │ Mobile PWA │  │
│   │   Data     │ (Carto)    │  Citoyen   │  Demandes  │ (Terrain)  │  │
│   │  /admin/   │   /sig/    │ /portail/  │ /demandes/ │  /mobile/  │  │
│   └────────────┴────────────┴────────────┴────────────┴────────────┘  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    BACKEND & SERVICES                            │  │
│   ├──────────────────────────┬──────────────────────────────────────┤  │
│   │     GéoClic API          │         PostgreSQL + PostGIS          │  │
│   │     FastAPI V14          │         Base de données               │  │
│   └──────────────────────────┴──────────────────────────────────────┘  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  Nginx (Serveur Web / Reverse Proxy / SSL Let's Encrypt)        │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

**Composants :**
- **GéoClic API** : Le cerveau qui gère les données (FastAPI + Python)
- **GéoClic Data** : Interface d'administration pour les agents (/admin/)
- **SIG Web** : Cartographie avancée avec fonds IGN (/sig/)
- **Portail Citoyen** : Interface web pour les signalements citoyens (/portail/)
- **GéoClic Demandes** : Back-office pour traiter les demandes (/demandes/)
- **Mobile PWA** : Application terrain installable (/mobile/)
- **PostgreSQL + PostGIS** : Base de données spatiales

---

## 2. Commander un serveur OVH

### Étape 2.1 : Créer un compte OVH

1. Allez sur **https://www.ovh.com/fr/**
2. Cliquez sur **"Mon compte"** en haut à droite
3. Cliquez sur **"Créer un compte"**
4. Remplissez le formulaire avec vos informations
5. Validez votre email

### Étape 2.2 : Commander un VPS

Un VPS (Virtual Private Server) est un serveur virtuel. C'est moins cher qu'un serveur dédié
et largement suffisant pour GéoClic.

1. Allez sur **https://www.ovhcloud.com/fr/vps/**
2. Choisissez l'offre **"VPS Starter"** ou **"VPS Value"** :
   - **Starter** (~5€/mois) : Pour tester ou petite collectivité (< 10 utilisateurs)
   - **Value** (~10€/mois) : Recommandé pour une utilisation normale

3. Configuration recommandée :
   ```
   ┌────────────────────────────────────────┐
   │  Configuration minimale recommandée    │
   ├────────────────────────────────────────┤
   │  RAM        : 2 Go minimum (4 Go idéal)│
   │  Stockage   : 40 Go SSD                │
   │  Système    : Ubuntu 22.04 LTS         │
   │  Localisation: France (Gravelines)     │
   └────────────────────────────────────────┘
   ```

4. **IMPORTANT** : Lors du choix du système d'exploitation :
   - Sélectionnez **Ubuntu 22.04 LTS** (ou Ubuntu 24.04 LTS)
   - LTS signifie "Long Term Support" = mises à jour de sécurité pendant 5 ans

5. Validez la commande et payez

### Étape 2.3 : Récupérer vos identifiants

Après la commande (quelques minutes à quelques heures), vous recevrez un email avec :
- **L'adresse IP** de votre serveur (exemple : `51.83.123.45`)
- **Le mot de passe root** (le super-administrateur)

**CONSERVEZ CES INFORMATIONS PRÉCIEUSEMENT !**

---

## 3. Se connecter au serveur

### Qu'est-ce que SSH ?

SSH (Secure Shell) permet de contrôler votre serveur à distance via des commandes texte.
C'est comme si vous étiez devant l'ordinateur, mais à distance.

### Sur Windows 10/11

Windows a un client SSH intégré.

1. **Ouvrir le Terminal** :
   - Appuyez sur les touches `Windows` + `R`
   - Tapez `cmd` et appuyez sur Entrée
   - Une fenêtre noire s'ouvre

2. **Se connecter au serveur** :
   Tapez cette commande en remplaçant `51.83.123.45` par VOTRE adresse IP :
   ```
   ssh root@51.83.123.45
   ```

3. **Première connexion** :
   - Le système vous demande si vous faites confiance à ce serveur
   - Tapez `yes` et appuyez sur Entrée
   - Entrez le mot de passe reçu par email (vous ne voyez pas les caractères, c'est normal)
   - Appuyez sur Entrée

4. **Vous êtes connecté !**
   Vous devriez voir quelque chose comme :
   ```
   root@vps-123456:~#
   ```

### Sur Mac

1. **Ouvrir le Terminal** :
   - Appuyez sur `Cmd` + `Espace`
   - Tapez "Terminal" et appuyez sur Entrée

2. **Se connecter** :
   ```
   ssh root@51.83.123.45
   ```

3. Suivez les mêmes étapes que pour Windows

### Alternative : Utiliser PuTTY (Windows)

Si la méthode ci-dessus ne fonctionne pas :

1. Téléchargez PuTTY : **https://www.putty.org/**
2. Installez-le
3. Ouvrez PuTTY
4. Dans "Host Name", entrez votre adresse IP
5. Cliquez sur "Open"
6. À "login as:", tapez `root`
7. Entrez votre mot de passe

---

## 4. Préparer le serveur

### Comprendre les commandes Linux

Voici les commandes de base que nous allons utiliser :

| Commande | Signification | Exemple |
|----------|---------------|---------|
| `apt update` | Mettre à jour la liste des logiciels | Met à jour l'index |
| `apt install X` | Installer le logiciel X | `apt install git` |
| `cd /chemin` | Aller dans un dossier | `cd /home` |
| `ls` | Lister les fichiers | Voir le contenu |
| `nano fichier` | Éditer un fichier texte | `nano config.txt` |
| `cat fichier` | Afficher un fichier | `cat config.txt` |
| `systemctl start X` | Démarrer un service | `systemctl start docker` |
| `reboot` | Redémarrer le serveur | Redémarre tout |

**CONSEIL** : Vous pouvez copier-coller les commandes.
- Sur Windows : Clic droit pour coller
- Sur Mac : Cmd+V

### Étape 4.1 : Mettre à jour le système

**Pourquoi ?** Les mises à jour corrigent les failles de sécurité.

Tapez ces commandes une par une (appuyez sur Entrée après chaque ligne) :

```bash
apt update
```

Attendez que ça finisse, puis :

```bash
apt upgrade -y
```

Le `-y` signifie "oui à tout" pour ne pas avoir à confirmer chaque mise à jour.
Cette étape peut prendre 2-5 minutes.

### Étape 4.2 : Installer les outils de base

```bash
apt install -y curl wget git nano htop
```

Explication :
- `curl` et `wget` : télécharger des fichiers depuis Internet
- `git` : récupérer le code source
- `nano` : éditeur de texte simple
- `htop` : voir ce qui se passe sur le serveur

### Étape 4.3 : Créer un utilisateur (recommandé mais optionnel)

Travailler en "root" (super-administrateur) est risqué. Créons un utilisateur normal :

```bash
adduser geoclic
```

Le système vous demande :
- Un mot de passe (tapez-le, puis confirmez)
- Des informations (nom, etc.) - appuyez sur Entrée pour ignorer
- Confirmez avec `Y`

Donnez-lui les droits administrateur :

```bash
usermod -aG sudo geoclic
```

---

## 5. Installer GéoClic Suite

### Méthode Automatique (Recommandée)

Cette méthode installe tout automatiquement en une seule commande.

#### Étape 5.1 : Lancer l'installation

```bash
curl -fsSL https://raw.githubusercontent.com/fredco30/GeoClic_Suite/main/deploy/install-geoclic.sh | bash
```

**OU** si vous avez téléchargé les fichiers :

```bash
cd /root
git clone https://github.com/fredco30/GeoClic_Suite.git
cd GeoClic_Suite/deploy
chmod +x install-geoclic.sh
./install-geoclic.sh
```

#### Étape 5.2 : Répondre aux questions

Le script vous pose des questions :

1. **Nom de domaine** :
   ```
   Entrez votre nom de domaine (ex: geoclic.maville.fr):
   ```
   - Si vous avez un nom de domaine, entrez-le
   - Sinon, appuyez sur Entrée pour utiliser l'adresse IP

2. **Email pour les certificats SSL** :
   ```
   Entrez votre email pour Let's Encrypt:
   ```
   - Entrez votre email professionnel
   - Sert à recevoir les alertes de certificat

3. **Mot de passe base de données** :
   ```
   Mot de passe PostgreSQL (laisser vide pour générer):
   ```
   - Appuyez sur Entrée pour un mot de passe sécurisé automatique
   - **NOTEZ CE MOT DE PASSE** s'il s'affiche !

#### Étape 5.3 : Attendre l'installation

L'installation prend 5-15 minutes. Vous verrez défiler des messages.

```
[INFO] Installation de Docker...
[INFO] Téléchargement des images...
[INFO] Configuration de la base de données...
[INFO] Démarrage des services...
[OK] Installation terminée !

╔════════════════════════════════════════════════════════════╗
║           GéoClic Suite V14 - Installation Réussie          ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  API        : https://votre-domaine.fr/api                  ║
║  Admin      : https://votre-domaine.fr/admin                ║
║  Documentation : https://votre-domaine.fr/api/docs          ║
║                                                              ║
║  Utilisateur par défaut :                                   ║
║    Email    : admin@geoclic.local                           ║
║    Mot de passe : (voir fichier .env)                       ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
```

### Méthode Manuelle (Si la méthode automatique échoue)

#### Étape 5.1 : Installer Docker

Docker permet de faire tourner des applications dans des "conteneurs" isolés.

```bash
# Installer les dépendances
apt install -y apt-transport-https ca-certificates curl software-properties-common

# Ajouter la clé Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Ajouter le dépôt Docker
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installer Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Vérifier l'installation
docker --version
```

Vous devriez voir quelque chose comme : `Docker version 24.0.x`

#### Étape 5.2 : Créer les dossiers

```bash
mkdir -p /opt/geoclic
cd /opt/geoclic
```

#### Étape 5.3 : Créer le fichier de configuration

```bash
nano .env
```

Un éditeur s'ouvre. Tapez (ou collez) ceci :

```
# Configuration GéoClic Suite V14

# Base de données
POSTGRES_USER=geoclic
POSTGRES_PASSWORD=VotreMotDePasseSecurise123!
POSTGRES_DB=geoclic_db

# API
API_SECRET_KEY=ChangezCetteClefSecrete12345678901234567890
API_DEBUG=false

# Domaine
DOMAIN=votre-domaine.fr

# Email (optionnel)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=
```

**Pour sauvegarder et quitter nano** :
1. Appuyez sur `Ctrl` + `X`
2. Tapez `Y` pour confirmer
3. Appuyez sur Entrée

#### Étape 5.4 : Créer le fichier Docker Compose

```bash
nano docker-compose.yml
```

Collez ce contenu :

```yaml
version: '3.8'

services:
  # Base de données PostgreSQL avec PostGIS
  db:
    image: postgis/postgis:15-3.3
    container_name: geoclic_db
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # API FastAPI
  api:
    image: geoclic/api:v14
    container_name: geoclic_api
    restart: always
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      SECRET_KEY: ${API_SECRET_KEY}
      DEBUG: ${API_DEBUG}
    ports:
      - "8000:8000"

  # Interface Admin (GéoClic Data)
  admin:
    image: geoclic/admin:v14
    container_name: geoclic_admin
    restart: always
    depends_on:
      - api
    ports:
      - "3000:80"

  # Nginx (reverse proxy)
  nginx:
    image: nginx:alpine
    container_name: geoclic_nginx
    restart: always
    depends_on:
      - api
      - admin
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - certbot_data:/var/www/certbot:ro

volumes:
  postgres_data:
  certbot_data:
```

Sauvegardez avec `Ctrl+X`, `Y`, Entrée.

#### Étape 5.5 : Créer la configuration Nginx

```bash
nano nginx.conf
```

Collez :

```nginx
events {
    worker_connections 1024;
}

http {
    # Redirection HTTP vers HTTPS
    server {
        listen 80;
        server_name _;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # Serveur HTTPS
    server {
        listen 443 ssl;
        server_name _;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # API
        location /api {
            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Admin
        location / {
            proxy_pass http://admin:80;
            proxy_set_header Host $host;
        }
    }
}
```

#### Étape 5.6 : Créer un certificat SSL temporaire

```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/privkey.pem \
    -out ssl/fullchain.pem \
    -subj "/CN=localhost"
```

#### Étape 5.7 : Lancer GéoClic

```bash
docker compose up -d
```

Le `-d` signifie "en arrière-plan" (detached).

Vérifiez que tout fonctionne :

```bash
docker compose ps
```

Vous devriez voir tous les services en état "Up" :

```
NAME              STATUS    PORTS
geoclic_api       Up        0.0.0.0:8000->8000/tcp
geoclic_admin     Up        0.0.0.0:3000->80/tcp
geoclic_db        Up        5432/tcp
geoclic_nginx     Up        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

---

## 6. Configurer le nom de domaine

### Qu'est-ce qu'un nom de domaine ?

Un nom de domaine (ex: `geoclic.maville.fr`) permet d'accéder à votre serveur
avec un nom facile à retenir plutôt qu'une adresse IP.

### Étape 6.1 : Acheter ou utiliser un domaine

**Option A : Acheter un nouveau domaine**
- OVH : https://www.ovh.com/fr/domaines/
- Environ 5-15€/an pour un .fr

**Option B : Utiliser un sous-domaine existant**
Si votre mairie a déjà `maville.fr`, demandez un sous-domaine `geoclic.maville.fr`

### Étape 6.2 : Configurer le DNS

Le DNS fait le lien entre le nom de domaine et l'adresse IP.

1. Connectez-vous à votre **espace client OVH**
2. Allez dans **Web Cloud** > **Domaines**
3. Sélectionnez votre domaine
4. Cliquez sur **Zone DNS**
5. Ajoutez un enregistrement **A** :

```
┌─────────────────────────────────────────────────────────────┐
│  Type   │  Sous-domaine  │  Cible (IP)      │  TTL         │
├─────────────────────────────────────────────────────────────┤
│    A    │  geoclic       │  51.83.123.45    │  3600        │
└─────────────────────────────────────────────────────────────┘
```

- **Type** : A (adresse IPv4)
- **Sous-domaine** : ce que vous voulez (ex: `geoclic`)
- **Cible** : l'adresse IP de votre serveur OVH
- **TTL** : 3600 (1 heure)

6. Cliquez sur **Suivant** puis **Valider**

**Attention** : La propagation DNS peut prendre jusqu'à 24 heures (généralement 1-2 heures).

### Étape 6.3 : Vérifier la configuration DNS

Depuis votre ordinateur, ouvrez un terminal et tapez :

```bash
ping geoclic.maville.fr
```

Si ça fonctionne, vous verrez l'adresse IP de votre serveur.

### Étape 6.4 : Obtenir un certificat SSL gratuit

Un certificat SSL permet le HTTPS (cadenas vert). Let's Encrypt en fournit gratuitement.

Connectez-vous à votre serveur et tapez :

```bash
# Installer Certbot
apt install -y certbot

# Obtenir le certificat (remplacez par votre domaine)
certbot certonly --standalone --agree-tos --email votre@email.com -d geoclic.maville.fr
```

Si ça fonctionne, les certificats sont dans `/etc/letsencrypt/live/geoclic.maville.fr/`

Copiez-les pour Nginx :

```bash
cp /etc/letsencrypt/live/geoclic.maville.fr/fullchain.pem /opt/geoclic/ssl/
cp /etc/letsencrypt/live/geoclic.maville.fr/privkey.pem /opt/geoclic/ssl/
```

Redémarrez Nginx :

```bash
cd /opt/geoclic
docker compose restart nginx
```

### Étape 6.5 : Renouvellement automatique du certificat

Les certificats Let's Encrypt expirent après 90 jours. Automatisons le renouvellement :

```bash
crontab -e
```

Si on vous demande un éditeur, choisissez `1` (nano).

Ajoutez cette ligne à la fin :

```
0 3 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/*/fullchain.pem /opt/geoclic/ssl/ && cp /etc/letsencrypt/live/*/privkey.pem /opt/geoclic/ssl/ && docker compose -f /opt/geoclic/docker-compose.yml restart nginx
```

Sauvegardez et quittez (`Ctrl+X`, `Y`, Entrée).

---

## 7. Configurer les notifications email

GéoClic envoie des emails aux citoyens pour les tenir informés de l'avancement de leurs demandes.
Deux méthodes sont disponibles selon votre infrastructure.

### Option A : SMTP Classique (OVH, Gmail, Mailjet...)

Méthode traditionnelle, fonctionne avec tous les fournisseurs SMTP.

| Fournisseur | Serveur SMTP | Port | TLS |
|-------------|--------------|------|-----|
| OVH | ssl0.ovh.net | 587 | Oui |
| Gmail | smtp.gmail.com | 587 | Oui |
| Mailjet | in-v3.mailjet.com | 587 | Oui |
| Brevo (Sendinblue) | smtp-relay.brevo.com | 587 | Oui |

**Configuration dans le fichier .env :**

```bash
nano /opt/geoclic/.env
```

Ajoutez ou modifiez :

```env
# Provider email
EMAIL_PROVIDER=smtp

# Configuration SMTP
SMTP_HOST=ssl0.ovh.net
SMTP_PORT=587
SMTP_USER=noreply@maville.fr
SMTP_PASSWORD=votre_mot_de_passe
SMTP_USE_TLS=true

# Expéditeur
EMAIL_FROM=noreply@maville.fr
EMAIL_FROM_NAME=Mairie de MaVille
```

### Option B : Microsoft 365 / Outlook (Recommandé pour les mairies)

> **Pourquoi Microsoft Graph ?**
> Microsoft a désactivé l'authentification SMTP basique. L'API Graph est la méthode
> recommandée, plus sécurisée et fiable.

#### Étape 7.1 : Créer une application dans Azure AD

1. Connectez-vous au [Portail Azure](https://portal.azure.com)
2. Allez dans **Azure Active Directory** → **App registrations**
3. Cliquez sur **New registration**
4. Nom : `GéoClic Notifications`
5. Type de compte : **Single tenant**
6. Cliquez sur **Register**

#### Étape 7.2 : Ajouter les permissions

1. Dans l'application créée, allez dans **API permissions**
2. Cliquez sur **Add a permission**
3. Sélectionnez **Microsoft Graph**
4. Choisissez **Application permissions**
5. Cherchez et ajoutez **Mail.Send**
6. Cliquez sur **Grant admin consent** (bouton bleu)

#### Étape 7.3 : Créer un secret client

1. Allez dans **Certificates & secrets**
2. Cliquez sur **New client secret**
3. Description : `GéoClic Email`
4. Expiration : 24 mois
5. **Copiez immédiatement la valeur du secret** (elle ne sera plus visible)

#### Étape 7.4 : Récupérer les identifiants

Dans la page **Overview** de votre application, notez :
- **Application (client) ID**
- **Directory (tenant) ID**

#### Étape 7.5 : Configurer GéoClic

```bash
nano /opt/geoclic/.env
```

Ajoutez :

```env
# Provider email
EMAIL_PROVIDER=microsoft

# Configuration Microsoft Graph API
MS_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MS_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MS_CLIENT_SECRET=votre_secret_client

# Expéditeur (doit être une boîte mail existante dans votre tenant)
EMAIL_FROM=noreply@maville.fr
EMAIL_FROM_NAME=Mairie de MaVille
```

> **Important** : L'adresse EMAIL_FROM doit correspondre à une boîte mail existante
> dans votre tenant Microsoft 365.

#### Redémarrer les services

```bash
cd /opt/geoclic
docker compose restart api
```

---

## 8. Configurer le Portail Citoyen

Le Portail Citoyen permet aux habitants de signaler des problèmes (nids de poule,
éclairage défaillant, dépôts sauvages...) directement depuis leur smartphone ou ordinateur.

### Les applications citoyennes

- **Portail Web** : Site web responsive accessible sur tous les navigateurs
- **App Android** : Application native avec scan QR et GPS
- **Back-office** : Interface agents pour traiter les demandes

### Workflow des demandes

```
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │   Nouveau   │───▶│ Modération  │───▶│   Accepté   │───▶│  En cours   │
   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                            │                                       │
                            ▼                                       ▼
                     ┌─────────────┐                        ┌─────────────┐
                     │   Rejeté    │                        │   Planifié  │
                     └─────────────┘                        └─────────────┘
                                                                    │
                                                                    ▼
                                                            ┌─────────────┐
                                                            │   Traité    │───▶ Clôturé
                                                            └─────────────┘
```

### Configurer les catégories de signalement

Accédez au back-office GéoClic Demandes (`https://geoclic.maville.fr/demandes`)
pour créer vos catégories. Exemples courants :

| Icône | Catégorie | Description |
|-------|-----------|-------------|
| 🚧 | Voirie | Nids de poule, trottoirs endommagés |
| 💡 | Éclairage | Lampadaires défaillants |
| 🗑️ | Propreté | Dépôts sauvages, tags, poubelles |
| 🌳 | Espaces verts | Arbres dangereux, pelouses |
| 🚗 | Stationnement | Véhicules ventouses |
| 🚦 | Signalisation | Panneaux manquants |
| 💧 | Eau | Fuites, canalisations |
| 🏠 | Bâtiments | Dégradations, accessibilité |

### URL des applications

| Application | URL |
|-------------|-----|
| Portail Citoyen | `https://geoclic.maville.fr/citoyen` |
| Back-office Demandes | `https://geoclic.maville.fr/demandes` |
| API Documentation | `https://geoclic.maville.fr/api/docs` |

### Publier l'application Android

L'application Android (App Citoyen) peut être :
- Téléchargée directement (fichier APK) depuis votre site web
- Publiée sur le Google Play Store (nécessite un compte développeur à 25$)

> **Astuce : QR Codes sur les équipements**
>
> Imprimez des QR codes à coller sur vos équipements (lampadaires, bancs, poubelles...).
> Les citoyens pourront scanner le QR code pour signaler un problème sur cet équipement
> précis, avec géolocalisation automatique.

---

## 9. Premiers pas après installation

### Étape 9.1 : Accéder aux différentes interfaces

Ouvrez votre navigateur web et allez sur :

| Interface | URL | Description |
|-----------|-----|-------------|
| GéoClic Data | `https://geoclic.maville.fr/admin/` | Administration patrimoine |
| SIG Web | `https://geoclic.maville.fr/sig/` | Cartographie avancée (IGN) |
| Portail Citoyen | `https://geoclic.maville.fr/portail/` | Interface citoyens |
| GéoClic Demandes | `https://geoclic.maville.fr/demandes/` | Back-office demandes |
| Mobile PWA | `https://geoclic.maville.fr/mobile/` | Application terrain |
| Documentation API | `https://geoclic.maville.fr/api/docs` | API Swagger |

**SIG Web - Fonctionnalités cartographiques :**
- Fonds de carte IGN (Plan, Ortho, Cadastre, Carte, Historique)
- Outils de mesure (distance et surface)
- Création de points, lignes, polygones
- Gestion des périmètres/zones
- Import GeoJSON par drag & drop
- Multi-projets

### Étape 7.2 : Se connecter avec le compte admin

Identifiants par défaut (à changer immédiatement !) :

```
Email    : admin@geoclic.local
Mot de passe : (voir le fichier /opt/geoclic/.env)
```

Pour voir le mot de passe :

```bash
cat /opt/geoclic/.env | grep ADMIN
```

### Étape 7.3 : Changer le mot de passe admin

1. Connectez-vous à l'interface admin
2. Cliquez sur votre nom en haut à droite
3. Allez dans "Mon profil"
4. Changez le mot de passe

### Étape 7.4 : Créer votre premier projet

1. Dans l'admin, cliquez sur "Projets"
2. Cliquez sur "Nouveau projet"
3. Remplissez :
   - **Nom** : Nom de votre collectivité
   - **Code** : Code INSEE ou abréviation
   - **Description** : Description libre

### Étape 7.5 : Configurer le lexique avec les templates

Le lexique définit les catégories d'équipements que vous gérez. GéoClic propose des **templates prédéfinis** pour les collectivités :

**Templates disponibles :**

| Template | Description | Exemples de catégories |
|----------|-------------|------------------------|
| Éclairage Public | Gestion du parc luminaire | Candélabres, Luminaires, Armoires électriques |
| Mobilier Urbain | Équipements de voirie | Bancs, Poubelles, Abris bus, Barrières |
| Espaces Verts | Patrimoine végétal | Arbres, Massifs, Aires de jeux |
| Voirie | Infrastructure routière | Chaussées, Trottoirs, Signalisation |
| Réseaux | Canalisations et réseaux | Eau, Assainissement, Électricité |
| Bâtiments | Patrimoine immobilier | Mairie, Écoles, Équipements sportifs |
| Cimetières | Gestion funéraire | Concessions, Columbariums, Allées |

**Pour utiliser un template :**

1. Lors de la création d'un nouveau projet, sélectionnez un template
2. Le lexique sera automatiquement pré-rempli avec les catégories correspondantes
3. Vous pouvez ensuite personnaliser le lexique selon vos besoins

**Structure du lexique (6 niveaux) :**

```
Niveau 1 : Domaine (ex: Éclairage Public)
└── Niveau 2 : Famille (ex: Candélabres)
    └── Niveau 3 : Catégorie (ex: Candélabre simple)
        └── Niveau 4 : Sous-catégorie (ex: 4m)
            └── Niveau 5 : Type (ex: Fonte)
                └── Niveau 6 : Modèle (ex: Modèle Paris)
```

**Création manuelle :**

1. Allez dans "Lexique"
2. Créez les niveaux hiérarchiques selon vos besoins
3. Associez des champs dynamiques à chaque niveau (texte, nombre, date, liste déroulante, photo...)

---

## 10. Maintenance et sauvegardes

### Sauvegardes automatiques

L'installation configure des sauvegardes quotidiennes. Vérifiez qu'elles fonctionnent :

```bash
ls -la /opt/geoclic/backups/
```

Vous devriez voir des fichiers `.sql.gz` datés.

### Sauvegarde manuelle

Pour faire une sauvegarde immédiate :

```bash
cd /opt/geoclic
docker compose exec db pg_dump -U geoclic geoclic_db | gzip > backups/sauvegarde_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restaurer une sauvegarde

En cas de problème, pour restaurer :

```bash
cd /opt/geoclic

# Arrêter l'API pour éviter les conflits
docker compose stop api admin

# Restaurer la base
gunzip -c backups/sauvegarde_20240115_120000.sql.gz | docker compose exec -T db psql -U geoclic geoclic_db

# Redémarrer
docker compose start api admin
```

### Mettre à jour GéoClic

Quand une nouvelle version sort :

```bash
cd /opt/geoclic

# Télécharger les nouvelles images
docker compose pull

# Redémarrer avec les nouvelles versions
docker compose up -d

# Vérifier que tout fonctionne
docker compose ps
```

### Voir les logs (en cas de problème)

```bash
# Tous les logs
docker compose logs

# Logs de l'API uniquement
docker compose logs api

# Suivre les logs en temps réel
docker compose logs -f api
```

### Redémarrer un service

```bash
# Redémarrer l'API
docker compose restart api

# Redémarrer tout
docker compose restart
```

### Arrêter GéoClic (maintenance)

```bash
docker compose down
```

### Relancer après arrêt

```bash
docker compose up -d
```

---

## 11. Résolution des problèmes

### Problème : "Connection refused" quand j'accède au site

**Causes possibles** :
1. Les services ne sont pas démarrés
2. Le pare-feu bloque les connexions

**Solutions** :

```bash
# Vérifier l'état des services
cd /opt/geoclic
docker compose ps

# Si des services sont "Exit", voir les logs
docker compose logs

# Redémarrer
docker compose restart
```

### Problème : "502 Bad Gateway"

L'API ne répond pas à Nginx.

```bash
# Vérifier l'API
docker compose logs api

# L'erreur la plus courante : problème de base de données
docker compose logs db
```

### Problème : Je ne peux plus me connecter en SSH

**Depuis le panel OVH** :
1. Allez dans votre espace client OVH
2. Trouvez votre VPS
3. Cliquez sur "KVM" (console virtuelle)
4. Connectez-vous directement

### Problème : La base de données est pleine

```bash
# Voir l'espace disque
df -h

# Supprimer les vieilles sauvegardes (garder les 7 derniers jours)
find /opt/geoclic/backups -name "*.gz" -mtime +7 -delete

# Nettoyer Docker
docker system prune -a
```

### Problème : Le certificat SSL a expiré

```bash
# Renouveler manuellement
certbot renew

# Copier les nouveaux certificats
cp /etc/letsencrypt/live/*/fullchain.pem /opt/geoclic/ssl/
cp /etc/letsencrypt/live/*/privkey.pem /opt/geoclic/ssl/

# Redémarrer Nginx
cd /opt/geoclic
docker compose restart nginx
```

### Problème : "Permission denied"

Vous n'avez pas les droits. Ajoutez `sudo` devant la commande :

```bash
sudo docker compose restart
```

### Problème : Docker ne démarre pas au boot

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

---

## Commandes utiles à retenir

| Action | Commande |
|--------|----------|
| Se connecter au serveur | `ssh root@IP_DU_SERVEUR` |
| Voir l'état des services | `docker compose ps` |
| Voir les logs | `docker compose logs` |
| Redémarrer tout | `docker compose restart` |
| Arrêter GéoClic | `docker compose down` |
| Démarrer GéoClic | `docker compose up -d` |
| Faire une sauvegarde | Voir section 8 |
| Mettre à jour | `docker compose pull && docker compose up -d` |
| Espace disque | `df -h` |
| Utilisation mémoire | `htop` (quitter avec `q`) |

---

## Glossaire pour débutants

| Terme | Explication |
|-------|-------------|
| **SSH** | Connexion sécurisée à distance |
| **VPS** | Serveur virtuel privé |
| **Docker** | Système pour faire tourner des applications isolées |
| **Container** | Une application Docker en cours d'exécution |
| **PostgreSQL** | Base de données où sont stockées vos données |
| **PostGIS** | Extension géographique pour PostgreSQL |
| **Nginx** | Serveur web qui reçoit les requêtes |
| **API** | Interface de programmation (le "cerveau" de GéoClic) |
| **DNS** | Système qui traduit les noms de domaine en adresses IP |
| **SSL/TLS** | Chiffrement pour HTTPS (cadenas vert) |
| **Let's Encrypt** | Fournisseur de certificats SSL gratuits |
| **root** | Super-administrateur Linux |
| **sudo** | Exécuter une commande en tant qu'admin |

---

## Besoin d'aide ?

- **Documentation** : https://geoclic.fr/api/docs
- **GitHub** : https://github.com/fredco30/GeoClic_Suite/issues
- **Résumé projet** : [SUITE_GEOCLIC_RESUME.md](../SUITE_GEOCLIC_RESUME.md)

---

*Guide rédigé pour GéoClic Suite V14 - Janvier 2026 (mis à jour le 30 janvier 2026)*

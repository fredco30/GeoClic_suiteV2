# Guide de Compilation et Deploiement - GeoClic Suite

> **IMPORTANT POUR CLAUDE:** Ce guide est fait pour aider Claude lors des futures sessions.
> L'utilisateur n'a AUCUNE connaissance Linux - il faut le guider PAS A PAS comme un bebe.
> Toujours donner les commandes EXACTES a copier-coller.

---

## Contexte du Serveur

### Informations Serveur
- **Type :** VPS OVH avec Ubuntu
- **Acces :** VNC (interface graphique) ou SSH
- **IP :** 51.210.8.158
- **Domaine :** geoclic.fr

### Structure des Dossiers CRITIQUE

```
/home/ubuntu/Documents/
└── GeoClic_Suite-claude-analyze-geoclic-suite-hZOpT/   <-- DOSSIER SOURCE (fichiers dezippes de GitHub)
    ├── api/
    ├── app_citoyen/
    ├── database/
    ├── deploy/
    ├── docs/
    ├── geoclic_data/
    ├── geoclic_demandes/
    ├── geoclic_mobile_pwa/
    ├── geoclic_mobile_v12/
    ├── geoclic_SIG/
    ├── geoclic_sig_web/
    ├── portail_citoyen/
    └── shared/

/opt/geoclic/                                           <-- DOSSIER PRODUCTION (serveur en fonctionnement)
├── api/
├── app_citoyen/
├── database/
├── deploy/
│   ├── docker-compose.yml
│   ├── .env
│   └── nginx/
│       ├── nginx.conf
│       └── ssl/              <-- NE JAMAIS SUPPRIMER (certificats SSL)
├── doc/
├── docs/
├── geoclic_data/
├── geoclic_demandes/
├── geoclic_mobile_pwa/
├── geoclic_mobile_v12/
├── geoclic_SIG/
├── geoclic_sig_web/
├── portail_citoyen/
├── shared/
├── GeoClic_Suite/
├── README.md
├── SUITE_GEOCLIC_RESUME.md
└── SUIVI_DEPLOIEMENT.md
```

---

## Etape 0 : Ouvrir le Terminal

### Si tu es connecte en VNC (interface graphique)
1. Appuie sur **Ctrl + Alt + T** sur le clavier
2. Une fenetre noire s'ouvre avec `ubuntu@...:~$`

### Si tu te connectes depuis ton PC Windows
1. Ouvre PowerShell ou Invite de commandes
2. Tape : `ssh ubuntu@51.210.8.158`
3. Entre ton mot de passe (rien ne s'affiche, c'est normal)

---

## Etape 1 : Telecharger le ZIP depuis GitHub

### 1.1 Telecharger le fichier
1. Va sur GitHub : https://github.com/fredco30/GeoClic_Suite
2. Clique sur le bouton vert **"Code"**
3. Clique sur **"Download ZIP"**
4. Le fichier se telecharge sur ton PC

### 1.2 Transferer vers le serveur
Si tu es en VNC, tu peux :
- Utiliser le navigateur Firefox du serveur pour telecharger directement
- Ou copier-coller le fichier via VNC

### 1.3 Dezipper le fichier
1. Ouvre le gestionnaire de fichiers (icone dossier)
2. Va dans **Documents**
3. Clic droit sur le fichier `.zip`
4. Clique sur **"Extraire ici"**

Tu dois avoir maintenant :
```
/home/ubuntu/Documents/GeoClic_Suite-claude-analyze-geoclic-suite-hZOpT/
```

---

## Etape 2 : Commandes de Mise a Jour par Module

### VARIABLES A UTILISER (copie ces 2 lignes en premier)
```bash
SOURCE="/home/ubuntu/Documents/GeoClic_Suite-claude-analyze-geoclic-suite-hZOpT"
DEST="/opt/geoclic"
```

---

### 2.1 API (Backend Python FastAPI)

#### Copier les fichiers
```bash
sudo cp -r "$SOURCE/api/"* "$DEST/api/"
```

#### Recompiler et relancer
```bash
cd /opt/geoclic/deploy
sudo docker compose build --no-cache api
sudo docker compose up -d --force-recreate api
```

#### Verifier que ca marche
```bash
sudo docker logs geoclic_api --tail=20
```

---

### 2.2 GEOCLIC_DATA (Admin Patrimoine - Vue.js)

#### Copier les fichiers
```bash
sudo cp -r "$SOURCE/geoclic_data/"* "$DEST/geoclic_data/"
```

#### Recompiler et relancer
```bash
cd /opt/geoclic/deploy
sudo docker compose build --no-cache admin
sudo docker compose up -d --force-recreate admin
```

#### Verifier que ca marche
```bash
sudo docker logs geoclic_admin --tail=20
```

---

### 2.3 GEOCLIC_DEMANDES (Gestion des demandes - Vue.js)

#### Copier les fichiers
```bash
sudo cp -r "$SOURCE/geoclic_demandes/"* "$DEST/geoclic_demandes/"
```

#### Recompiler et relancer
```bash
cd /opt/geoclic/deploy
sudo docker compose build --no-cache demandes
sudo docker compose up -d --force-recreate demandes
```

#### Verifier que ca marche
```bash
sudo docker logs geoclic_demandes --tail=20
```

---

### 2.4 PORTAIL_CITOYEN (Vue.js)

#### Copier les fichiers
```bash
sudo cp -r "$SOURCE/portail_citoyen/"* "$DEST/portail_citoyen/"
```

#### Recompiler et relancer
```bash
cd /opt/geoclic/deploy
sudo docker compose build --no-cache portail
sudo docker compose up -d --force-recreate portail
```

#### Verifier que ca marche
```bash
sudo docker logs geoclic_portail --tail=20
```

---

### 2.5 APP_CITOYEN (Application Citoyenne - Vue.js)

#### Copier les fichiers
```bash
sudo cp -r "$SOURCE/app_citoyen/"* "$DEST/app_citoyen/"
```

#### Recompiler et relancer (si container existe)
```bash
cd /opt/geoclic/deploy
sudo docker compose build --no-cache app_citoyen
sudo docker compose up -d --force-recreate app_citoyen
```

---

### 2.6 GEOCLIC_MOBILE_PWA (Application Mobile - Vue.js)

#### Copier les fichiers
```bash
sudo cp -r "$SOURCE/geoclic_mobile_pwa/"* "$DEST/geoclic_mobile_pwa/"
```

#### Recompiler et relancer
```bash
cd /opt/geoclic/deploy
sudo docker compose build --no-cache mobile
sudo docker compose up -d --force-recreate mobile
```

#### Verifier que ca marche
```bash
sudo docker logs geoclic_mobile --tail=20
```

---

### 2.7 GEOCLIC_SIG_WEB (Cartographie Web - Vue.js)

#### Copier les fichiers
```bash
sudo cp -r "$SOURCE/geoclic_sig_web/"* "$DEST/geoclic_sig_web/"
```

#### Recompiler et relancer
```bash
cd /opt/geoclic/deploy
sudo docker compose build --no-cache sig
sudo docker compose up -d --force-recreate sig
```

#### Verifier que ca marche
```bash
sudo docker logs geoclic_sig --tail=20
```

---

### 2.8 DATABASE (Scripts SQL)

#### Copier les fichiers
```bash
sudo cp -r "$SOURCE/database/"* "$DEST/database/"
```

**ATTENTION :** Les scripts SQL ne s'executent qu'a l'initialisation de la base de donnees.
Pour appliquer des migrations :
```bash
sudo docker exec -i geoclic_db psql -U geoclic -d geoclic_db < "$SOURCE/database/migrations/votre_migration.sql"
```

---

### 2.9 DEPLOY (Configuration Docker/Nginx)

#### ATTENTION - NE JAMAIS SUPPRIMER LE DOSSIER SSL !

#### Copier UNIQUEMENT les fichiers de configuration (pas les certificats SSL)
```bash
sudo cp "$SOURCE/deploy/docker-compose.yml" "$DEST/deploy/"
sudo cp "$SOURCE/deploy/.env.example" "$DEST/deploy/"
```

#### Copier la config nginx (sans supprimer les certificats)
```bash
sudo cp "$SOURCE/deploy/nginx/nginx.conf" "$DEST/deploy/nginx/"
sudo cp -r "$SOURCE/deploy/nginx/conf.d/"* "$DEST/deploy/nginx/conf.d/" 2>/dev/null || true
```

#### Redemarrer nginx
```bash
cd /opt/geoclic/deploy
sudo docker compose restart nginx
```

---

### 2.10 SITE VITRINE (HTML/CSS statique)

#### Copier les fichiers
```bash
sudo cp -r "$SOURCE/deploy/www/"* "$DEST/deploy/www/"
```

Pas besoin de recompiler - le site est servi directement par nginx.

---

## Etape 3 : Tout Recompiler (si beaucoup de modifications)

### 3.1 Commande complete pour tout mettre a jour

```bash
# Definir les variables
SOURCE="/home/ubuntu/Documents/GeoClic_Suite-claude-analyze-geoclic-suite-hZOpT"
DEST="/opt/geoclic"

# Copier tous les modules (SAUF deploy complet pour proteger SSL)
sudo cp -r "$SOURCE/api/"* "$DEST/api/"
sudo cp -r "$SOURCE/geoclic_data/"* "$DEST/geoclic_data/"
sudo cp -r "$SOURCE/geoclic_demandes/"* "$DEST/geoclic_demandes/"
sudo cp -r "$SOURCE/portail_citoyen/"* "$DEST/portail_citoyen/"
sudo cp -r "$SOURCE/geoclic_mobile_pwa/"* "$DEST/geoclic_mobile_pwa/"
sudo cp -r "$SOURCE/geoclic_sig_web/"* "$DEST/geoclic_sig_web/"
sudo cp -r "$SOURCE/database/"* "$DEST/database/"
sudo cp -r "$SOURCE/shared/"* "$DEST/shared/"

# Copier le site vitrine
sudo cp -r "$SOURCE/deploy/www/"* "$DEST/deploy/www/"

# Recompiler TOUS les containers
cd /opt/geoclic/deploy
sudo docker compose build --no-cache
sudo docker compose up -d --force-recreate
```

---

## Etape 4 : Verification

### 4.1 Voir l'etat de tous les services
```bash
cd /opt/geoclic/deploy
sudo docker compose ps
```

Tu dois voir tous les services avec **"Up"** ou **"running"**.

### 4.2 Tester chaque URL
```bash
# API
curl https://geoclic.fr/api/health

# Chaque application
curl -I https://geoclic.fr/admin/
curl -I https://geoclic.fr/portail/
curl -I https://geoclic.fr/demandes/
curl -I https://geoclic.fr/mobile/
curl -I https://geoclic.fr/sig/
```

### 4.3 Voir les logs en cas d'erreur
```bash
# Logs de l'API
sudo docker logs geoclic_api --tail=50

# Logs de l'admin (geoclic_data)
sudo docker logs geoclic_admin --tail=50

# Logs nginx
sudo docker logs geoclic_nginx --tail=50

# Suivre les logs en temps reel (Ctrl+C pour arreter)
sudo docker logs -f geoclic_api
```

---

## Etape 5 : En cas de Probleme

### 5.1 "Permission denied"
Ajoute `sudo` devant la commande.

### 5.2 "Container not found"
Le service n'existe pas dans docker-compose.yml ou n'est pas demarre.
```bash
cd /opt/geoclic/deploy
sudo docker compose ps
```

### 5.3 Le build echoue
Voir les erreurs avec :
```bash
cd /opt/geoclic/deploy
sudo docker compose build nom_du_service 2>&1 | tail -100
```

### 5.4 Le service ne demarre pas
```bash
sudo docker logs nom_du_container --tail=100
```

### 5.5 Tout recommencer (RESET COMPLET)
**ATTENTION : Cela supprime toutes les donnees !**
```bash
cd /opt/geoclic/deploy
sudo docker compose down -v
sudo docker compose up -d --build
```

---

## Resume des Noms

| Module dans le depot | Container Docker | URL |
|---------------------|------------------|-----|
| api/ | geoclic_api | /api/ |
| geoclic_data/ | geoclic_admin | /admin/ |
| geoclic_demandes/ | geoclic_demandes | /demandes/ |
| portail_citoyen/ | geoclic_portail | /portail/ |
| geoclic_mobile_pwa/ | geoclic_mobile | /mobile/ |
| geoclic_sig_web/ | geoclic_sig | /sig/ |
| database/ | geoclic_db | (interne) |
| deploy/nginx/ | geoclic_nginx | (reverse proxy) |

---

## Aide-Memoire Rapide

```bash
# Variables (toujours en premier)
SOURCE="/home/ubuntu/Documents/GeoClic_Suite-claude-analyze-geoclic-suite-hZOpT"
DEST="/opt/geoclic"

# Copier un module
sudo cp -r "$SOURCE/NOM_MODULE/"* "$DEST/NOM_MODULE/"

# Recompiler un container
cd /opt/geoclic/deploy
sudo docker compose build --no-cache NOM_SERVICE
sudo docker compose up -d --force-recreate NOM_SERVICE

# Voir les logs
sudo docker logs NOM_CONTAINER --tail=50

# Etat des services
sudo docker compose ps
```

---

## Correspondance Modules <-> Services Docker

| Dossier source | Service docker-compose | Container |
|----------------|------------------------|-----------|
| api | api | geoclic_api |
| geoclic_data | admin | geoclic_admin |
| geoclic_demandes | demandes | geoclic_demandes |
| portail_citoyen | portail | geoclic_portail |
| geoclic_mobile_pwa | mobile | geoclic_mobile |
| geoclic_sig_web | sig | geoclic_sig |
| database | db | geoclic_db |
| deploy/nginx | nginx | geoclic_nginx |

---

*Guide cree le 31 janvier 2026 pour GeoClic Suite*
*A utiliser lors des futures sessions Claude pour eviter de chercher la procedure*

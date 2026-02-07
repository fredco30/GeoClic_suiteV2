# Guide Complet : Déployer GéoClic chez un Nouveau Client

Ce guide est écrit pour quelqu'un qui n'a **aucune connaissance** en Linux ou en réseau.
Il couvre tout, étape par étape, de l'achat du serveur jusqu'au moment où le client se connecte.

---

## Table des matières

1. [Comprendre l'architecture](#1-comprendre-larchitecture)
2. [Ce dont vous avez besoin avant de commencer](#2-ce-dont-vous-avez-besoin-avant-de-commencer)
3. [Étape 1 : Acheter un VPS pour le client](#3-étape-1--acheter-un-vps-pour-le-client)
4. [Étape 2 : Configurer le nom de domaine](#4-étape-2--configurer-le-nom-de-domaine)
5. [Étape 3 : Préparer la clé SSH](#5-étape-3--préparer-la-clé-ssh)
6. [Étape 4 : Provisionner le serveur](#6-étape-4--provisionner-le-serveur)
7. [Étape 5 : Initialiser la base de données](#7-étape-5--initialiser-la-base-de-données)
8. [Étape 6 : Vérifier que tout fonctionne](#8-étape-6--vérifier-que-tout-fonctionne)
9. [Mettre à jour un client existant](#9-mettre-à-jour-un-client-existant)
10. [Commandes de dépannage](#10-commandes-de-dépannage)
11. [Questions fréquentes](#11-questions-fréquentes)

---

## 1. Comprendre l'architecture

Imaginez que vous avez une **photocopieuse de logiciel**. Votre serveur actuel (geoclic.fr) contient le logiciel GéoClic. Quand un nouveau client arrive, vous :

1. Achetez un nouveau petit ordinateur en ligne (un "VPS")
2. Appuyez sur un bouton pour copier le logiciel dessus
3. Appuyez sur un autre bouton pour préparer sa base de données vide
4. Le client se connecte et configure ses catégories, services, etc.

```
Votre serveur (geoclic.fr)              Serveur du client
┌──────────────────────┐                ┌──────────────────────┐
│                      │    Copie du    │                      │
│  GéoClic Suite       │───────────────→│  GéoClic Suite       │
│  (code source)       │    code via    │  (copie identique)   │
│                      │    Internet    │                      │
│  Données La Grande   │                │  Base de données     │
│  Motte (VOS données) │    RIEN ne    │  VIDE (le client     │
│                      │    passe !     │  crée ses données)   │
└──────────────────────┘                └──────────────────────┘
```

**Point important** : Les données de La Grande Motte ne sont JAMAIS copiées chez le client. Chaque client a sa propre base de données vide.

---

## 2. Ce dont vous avez besoin avant de commencer

Avant de déployer chez un nouveau client, vérifiez que vous avez :

| Élément | Où le trouver | Exemple |
|---------|--------------|---------|
| Accès à votre serveur geoclic.fr | Vous l'avez déjà | Via SSH ou le terminal |
| Un nom de domaine pour le client | Vous le choisissez | `lyon.geoclic.fr` |
| Un VPS pour le client | À acheter (voir étape 1) | OVH, 5€/mois |
| L'email de l'admin du client | Le client vous le donne | `admin@mairie-lyon.fr` |
| Un mot de passe pour l'admin | Vous le choisissez | `MonMDP-Lyon-2026!` |

---

## 3. Étape 1 : Acheter un VPS pour le client

Un VPS, c'est un petit ordinateur que vous louez sur Internet. Il coûte entre 4€ et 12€ par mois.

### Où acheter ?

Allez sur **OVH** (le même fournisseur que votre serveur actuel) :
- Allez sur https://www.ovhcloud.com/fr/vps/
- Choisissez la formule **VPS Starter** ou **VPS Essential** (suffisant pour GéoClic)

### Configuration minimale recommandée

| Ressource | Minimum | Recommandé |
|-----------|---------|------------|
| RAM | 2 Go | 4 Go |
| Stockage | 20 Go SSD | 40 Go SSD |
| Système | Ubuntu 22.04 ou 24.04 | Ubuntu 24.04 |
| Localisation | France | France (Roubaix ou Gravelines) |

### Après l'achat

OVH vous enverra un email avec :
- **L'adresse IP** du serveur (exemple : `51.210.42.100`)
- **Le mot de passe root** (vous en aurez besoin une seule fois)

**Notez bien ces informations !**

### Créer un utilisateur `ubuntu` (si nécessaire)

Certains VPS OVH sont livrés avec uniquement le compte `root`. Fleet a besoin d'un utilisateur `ubuntu`. Si vous n'avez que `root`, connectez-vous une première fois et créez l'utilisateur :

```bash
# Depuis votre serveur geoclic.fr, connectez-vous au nouveau VPS
ssh root@51.210.42.100
# (tapez le mot de passe root fourni par OVH)

# Créez l'utilisateur ubuntu
adduser ubuntu
# (suivez les instructions, mettez un mot de passe)

# Donnez-lui les droits sudo (administrateur)
usermod -aG sudo ubuntu

# Autorisez ubuntu à utiliser sudo sans mot de passe
echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu

# Déconnectez-vous
exit
```

---

## 4. Étape 2 : Configurer le nom de domaine

Le client a besoin d'une adresse web (comme `lyon.geoclic.fr`). Voici comment la créer.

### Option A : Sous-domaine de geoclic.fr (recommandé)

C'est le plus simple. Vous ajoutez un sous-domaine à votre domaine existant.

1. Connectez-vous à votre **espace client OVH** : https://www.ovh.com/manager/
2. Allez dans **Domaines** → **geoclic.fr**
3. Cliquez sur l'onglet **Zone DNS**
4. Cliquez sur **Ajouter une entrée**
5. Choisissez le type **A**
6. Remplissez :
   - **Sous-domaine** : `lyon` (ou le nom du client)
   - **Cible** : `51.210.42.100` (l'IP du nouveau VPS)
7. Cliquez sur **Valider**

**Attention** : La propagation DNS peut prendre entre 5 minutes et 24 heures. En général, c'est fait en moins de 30 minutes.

### Option B : Domaine propre du client

Si le client veut utiliser son propre domaine (ex: `geoclic.mairie-lyon.fr`), c'est le client qui doit faire la manipulation DNS de son côté. Donnez-lui ces instructions :

> "Créez un enregistrement DNS de type A pointant vers l'IP `51.210.42.100` pour le sous-domaine `geoclic`."

### Comment vérifier que le domaine fonctionne ?

Attendez quelques minutes, puis tapez cette commande sur votre serveur :

```bash
# Vérifier que le domaine pointe vers la bonne IP
ping -c 1 lyon.geoclic.fr
```

Vous devez voir l'IP du VPS (ex: `51.210.42.100`). Si ça ne fonctionne pas, attendez encore un peu.

---

## 5. Étape 3 : Préparer la clé SSH

La clé SSH, c'est comme un **badge d'accès** qui permet à votre serveur de se connecter au serveur du client sans mot de passe.

### Première fois uniquement : Générer la clé

Si c'est la première fois que vous utilisez Fleet, générez la clé :

```bash
# Sur votre serveur geoclic.fr
sudo /opt/geoclic/fleet/geoclic-fleet.sh ssh-key generate
```

Ça affiche une longue ligne qui commence par `ssh-ed25519`. C'est votre **clé publique**. Copiez-la.

### Copier la clé sur le nouveau VPS

Il faut mettre cette clé sur le serveur du client pour que Fleet puisse s'y connecter :

```bash
# Copier la clé vers le nouveau VPS
# Remplacez 51.210.42.100 par l'IP de votre nouveau VPS
sudo ssh-copy-id -i /root/.ssh/geoclic_fleet_key.pub ubuntu@51.210.42.100
```

Le système vous demandera le mot de passe de l'utilisateur `ubuntu` sur le nouveau VPS. Tapez-le. C'est la dernière fois qu'on vous le demande.

### Vérifier que ça marche

```bash
sudo /opt/geoclic/fleet/geoclic-fleet.sh test-ssh 51.210.42.100 ubuntu
```

Si vous voyez `SSH OK`, c'est bon. Sinon, vérifiez le mot de passe ou l'IP.

---

## 6. Étape 4 : Provisionner le serveur

C'est le gros bouton. Cette commande va :
- Installer Docker sur le nouveau VPS
- Copier tout le code GéoClic
- Créer le certificat SSL (le cadenas vert dans le navigateur)
- Lancer tous les services (API, base de données, interface web, etc.)

### La commande

```bash
# Sur votre serveur geoclic.fr
# Remplacez les valeurs par celles de votre client

sudo /opt/geoclic/fleet/geoclic-fleet.sh provision \
  --name mairie-lyon \
  --domain lyon.geoclic.fr \
  --ip 51.210.42.100 \
  --email admin@mairie-lyon.fr
```

**Explication de chaque paramètre :**

| Paramètre | Signification | Exemple |
|-----------|--------------|---------|
| `--name` | Un nom court pour identifier le client (pas d'espaces, pas d'accents) | `mairie-lyon` |
| `--domain` | L'adresse web du client (configurée à l'étape 2) | `lyon.geoclic.fr` |
| `--ip` | L'adresse IP du VPS (reçue par email d'OVH) | `51.210.42.100` |
| `--email` | Email pour le certificat SSL (n'importe quel email valide) | `admin@mairie-lyon.fr` |

### Ce qui se passe (patientez 5-15 minutes)

Le script affiche la progression :

```
1/7 - Installation des prérequis (Docker, certbot)...    ← ~3 min
2/7 - Création de l'arborescence...                      ← ~10 sec
3/7 - Copie du code GéoClic...                           ← ~2 min
4/7 - Configuration environnement...                     ← ~10 sec
5/7 - Configuration SSL...                               ← ~1 min
6/7 - Construction Docker...                             ← ~5-10 min
7/7 - Configuration finale...                            ← ~1 min
```

**Ne fermez pas le terminal pendant que ça tourne !**

### Si ça échoue

Si une étape échoue, le message d'erreur vous dira laquelle. Les erreurs les plus courantes :

| Erreur | Cause | Solution |
|--------|-------|----------|
| `SSH connection failed` | La clé SSH n'est pas copiée | Refaire l'étape 3 |
| `DNS not pointing` | Le domaine ne pointe pas vers l'IP | Attendre ou vérifier l'étape 2 |
| `Docker build failed` | Pas assez de RAM | Prendre un VPS plus gros (4 Go) |
| `SSL failed` | Le domaine ne pointe pas encore | Attendre 30 min, relancer |

Pour relancer après une erreur :
```bash
# Relancer le provisioning
sudo /opt/geoclic/fleet/geoclic-fleet.sh provision \
  --name mairie-lyon \
  --domain lyon.geoclic.fr \
  --ip 51.210.42.100 \
  --email admin@mairie-lyon.fr
```

---

## 7. Étape 5 : Initialiser la base de données

Le provisioning a installé GéoClic mais la base de données est **vide**. Il faut maintenant :
- Créer toutes les tables nécessaires (les 25 migrations SQL)
- Créer le compte administrateur du client

### La commande

```bash
# Sur votre serveur geoclic.fr
sudo /opt/geoclic/fleet/geoclic-fleet.sh init \
  --client mairie-lyon \
  --email admin@mairie-lyon.fr \
  --password "MotDePasse-Lyon-2026!" \
  --collectivite "Mairie de Lyon"
```

**Explication de chaque paramètre :**

| Paramètre | Signification | Exemple |
|-----------|--------------|---------|
| `--client` | Le nom du client (le même que `--name` dans provision) | `mairie-lyon` |
| `--email` | L'email du super administrateur du client | `admin@mairie-lyon.fr` |
| `--password` | Le mot de passe initial (min 8 caractères) | `MotDePasse-Lyon-2026!` |
| `--collectivite` | Le nom officiel de la collectivité | `Mairie de Lyon` |

### Ce qui se passe (~1 minute)

```
━━━ 1/4 - Vérification de la base de données
  ✓ Connexion à PostgreSQL OK
  ✓ PostGIS disponible

━━━ 2/4 - Application des migrations SQL
  ✓ add_system_settings.sql
  ✓ 002_add_project_id_to_lexique.sql
  ✓ 003_add_project_id_to_type_field_configs.sql
  ... (25 migrations au total)

━━━ 3/4 - Création du compte super administrateur
  ✓ Super admin créé: admin@mairie-lyon.fr

━━━ 4/4 - Configuration initiale
  ✓ Branding configuré: Mairie de Lyon

  Installation terminée !
```

### Option : Charger des données de démonstration

Si vous voulez montrer une **démo pré-remplie** au client (par exemple pour une présentation commerciale avant la signature), ajoutez `--with-demo` :

```bash
sudo /opt/geoclic/fleet/geoclic-fleet.sh init \
  --client mairie-lyon \
  --email admin@demo.geoclic.fr \
  --password "demo2026!" \
  --collectivite "Démo GéoClic" \
  --with-demo
```

Ça ajoute : 12 signalements fictifs, 4 services, 15 catégories, 3 comptes de test.

**Ne faites PAS ça pour un vrai client !** C'est uniquement pour les démos.

---

## 8. Étape 6 : Vérifier que tout fonctionne

### Vérification rapide

```bash
sudo /opt/geoclic/fleet/geoclic-fleet.sh status
```

Vous devez voir quelque chose comme :

```
🟢 mairie-lyon (lyon.geoclic.fr) - HTTP 200 - SSL: 89 jours - SSH: true
```

- `🟢` = le serveur est en ligne
- `HTTP 200` = l'API répond correctement
- `SSL: 89 jours` = le certificat SSL expire dans 89 jours (se renouvelle automatiquement)

### Vérification dans le navigateur

Ouvrez votre navigateur et allez sur ces adresses :

| Application | URL | Ce que vous devez voir |
|-------------|-----|----------------------|
| API (santé) | `https://lyon.geoclic.fr/api/health` | `{"status": "healthy"}` |
| GéoClic Admin | `https://lyon.geoclic.fr/admin/` | Page de connexion |
| Back-office | `https://lyon.geoclic.fr/demandes/` | Page de connexion |
| Portail citoyen | `https://lyon.geoclic.fr/portail/` | Page d'accueil publique |
| SIG Web | `https://lyon.geoclic.fr/sig/` | Page de connexion |

### Tester la connexion

1. Allez sur `https://lyon.geoclic.fr/admin/`
2. Entrez l'email et le mot de passe que vous avez choisis à l'étape 5
3. Vous devez voir le **wizard d'onboarding** (5 étapes de configuration)

### Si ça ne fonctionne pas

```bash
# Voir les logs du serveur du client
sudo /opt/geoclic/fleet/geoclic-fleet.sh logs --client mairie-lyon --service api

# Se connecter directement au serveur du client pour débugger
sudo /opt/geoclic/fleet/geoclic-fleet.sh ssh mairie-lyon

# Une fois connecté, vérifier l'état des conteneurs Docker
sudo docker ps
# Vous devez voir ~10 conteneurs (geoclic_api, geoclic_db, geoclic_nginx, etc.)
```

---

## 9. Mettre à jour un client existant

Quand vous faites des améliorations à GéoClic, il faut les pousser vers les clients.

### Mettre à jour UN client

```bash
# Met à jour le code + reconstruit les applications
sudo /opt/geoclic/fleet/geoclic-fleet.sh update --client mairie-lyon
```

### Mettre à jour TOUS les clients d'un coup

```bash
sudo /opt/geoclic/fleet/geoclic-fleet.sh update --all
```

### Mettre à jour avec une nouvelle migration SQL

Si la mise à jour inclut des changements dans la base de données (une migration), précisez-la :

```bash
sudo /opt/geoclic/fleet/geoclic-fleet.sh update \
  --client mairie-lyon \
  --migration 025_nouvelle_feature.sql
```

### Que fait la mise à jour ?

1. **Sauvegarde** de la base de données du client (sécurité)
2. **Copie** du nouveau code (rsync)
3. **Migration** SQL si précisée
4. **Reconstruction** des applications (Docker build)
5. **Vérification** que tout fonctionne (health check)

---

## 10. Commandes de dépannage

### Voir l'état de tous les serveurs

```bash
sudo /opt/geoclic/fleet/geoclic-fleet.sh status
```

### Voir les logs d'un serveur

```bash
# Logs de l'API (les erreurs backend)
sudo /opt/geoclic/fleet/geoclic-fleet.sh logs --client mairie-lyon --service api

# Logs de la base de données
sudo /opt/geoclic/fleet/geoclic-fleet.sh logs --client mairie-lyon --service db

# Logs de nginx (le serveur web)
sudo /opt/geoclic/fleet/geoclic-fleet.sh logs --client mairie-lyon --service nginx
```

### Se connecter au serveur d'un client

```bash
sudo /opt/geoclic/fleet/geoclic-fleet.sh ssh mairie-lyon
```

Une fois connecté, vous êtes "dans" le serveur du client. Commandes utiles :

```bash
# Voir les conteneurs qui tournent
sudo docker ps

# Redémarrer tous les services
cd /opt/geoclic/deploy && sudo docker-compose restart

# Voir les logs en temps réel de l'API
cd /opt/geoclic/deploy && sudo docker-compose logs -f api

# Revenir à votre serveur
exit
```

### Sauvegarder manuellement un client

```bash
sudo /opt/geoclic/fleet/geoclic-fleet.sh backup --client mairie-lyon
```

### Lister tous les clients enregistrés

```bash
sudo /opt/geoclic/fleet/geoclic-fleet.sh list
```

### Supprimer un client du registre

```bash
# Attention : ne supprime PAS le serveur, juste l'enregistrement dans Fleet
sudo /opt/geoclic/fleet/geoclic-fleet.sh remove --client mairie-lyon
```

---

## 11. Questions fréquentes

### "Combien de temps prend l'installation d'un nouveau client ?"

| Étape | Durée |
|-------|-------|
| Acheter le VPS | 5 minutes |
| Configurer le DNS | 5 minutes (+ attente propagation 5-30 min) |
| Copier la clé SSH | 2 minutes |
| Provisionner (provision) | 10-15 minutes |
| Initialiser la DB (init) | 1 minute |
| **Total** | **~30 minutes** (hors attente DNS) |

### "Est-ce que les données de La Grande Motte sont copiées chez le client ?"

**Non, jamais.** Fleet copie uniquement le code source (les applications). La base de données et les photos restent sur chaque serveur. Le client démarre avec une base vide.

### "Qu'est-ce que le wizard d'onboarding ?"

C'est un assistant qui s'affiche automatiquement au premier login du client sur GéoClic Admin. Il guide le client pour configurer :

1. **Identité** : nom de la collectivité, logo, couleurs
2. **Email** : serveur SMTP pour envoyer des notifications
3. **Catégories** : types de signalements (voirie, propreté, éclairage...)
4. **Services** : services municipaux qui traiteront les signalements
5. **Récapitulatif** : vérification avant validation

### "Comment le client accède à GéoClic ?"

Vous lui envoyez un email avec :

> Bonjour,
>
> Votre plateforme GéoClic est prête !
>
> Connectez-vous sur : https://lyon.geoclic.fr/admin/
> Email : admin@mairie-lyon.fr
> Mot de passe : (celui que vous avez défini)
>
> Au premier login, un assistant vous guidera pour configurer votre collectivité.
>
> Les autres applications :
> - Portail citoyen : https://lyon.geoclic.fr/portail/
> - Back-office demandes : https://lyon.geoclic.fr/demandes/
> - SIG cartographie : https://lyon.geoclic.fr/sig/

### "Et si le VPS tombe en panne ?"

Les sauvegardes sont automatiques (tous les jours à 2h du matin). Pour restaurer :

```bash
# Se connecter au serveur du client
sudo /opt/geoclic/fleet/geoclic-fleet.sh ssh mairie-lyon

# Voir les sauvegardes disponibles
ls -lh /opt/geoclic/backups/

# Restaurer la plus récente
sudo /opt/geoclic/scripts/restore_db.sh geoclic_backup_XXXXXXXX_XXXXXX.sql.gz
```

### "Comment je fais si j'ai un problème que je ne comprends pas ?"

1. Notez le message d'erreur exact (faites un copier-coller)
2. Notez quelle commande vous avez tapée
3. Notez le nom du client concerné
4. Contactez le support avec ces informations

### "Le certificat SSL (cadenas vert) va expirer ?"

Non. Le renouvellement est automatique (certbot le renouvelle tous les 3 mois). Si ça échoue, Fleet vous le signale dans `status` (le nombre de jours restants passe sous 30).

### "Puis-je installer GéoClic chez un client qui n'est pas chez OVH ?"

Oui ! Tout fournisseur de VPS fonctionne (Scaleway, Hetzner, DigitalOcean, AWS...) tant que :
- C'est un Ubuntu 22.04 ou 24.04
- Il a au moins 2 Go de RAM
- Vous avez un accès SSH
- Vous pouvez pointer un nom de domaine dessus

---

## Récapitulatif : Les 5 commandes à retenir

```bash
# 1. Installer un nouveau client
sudo /opt/geoclic/fleet/geoclic-fleet.sh provision --name NOM --domain DOMAINE --ip IP --email EMAIL

# 2. Initialiser sa base de données
sudo /opt/geoclic/fleet/geoclic-fleet.sh init --client NOM --email EMAIL --password MDP --collectivite "Nom"

# 3. Mettre à jour un client
sudo /opt/geoclic/fleet/geoclic-fleet.sh update --client NOM

# 4. Voir l'état de tous les serveurs
sudo /opt/geoclic/fleet/geoclic-fleet.sh status

# 5. Se connecter à un serveur client
sudo /opt/geoclic/fleet/geoclic-fleet.sh ssh NOM
```

C'est tout ce dont vous avez besoin pour gérer votre flotte de clients GéoClic.

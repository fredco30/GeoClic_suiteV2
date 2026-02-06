# GéoClic Fleet Manager - Guide complet

Outil de gestion centralisée pour déployer et maintenir GéoClic sur plusieurs serveurs clients.

## Architecture

```
geoclic.fr (serveur maître)
│
├── GéoClic Suite (production)
├── Fleet Manager (dashboard web + API)
│
├──rsync──→ VPS Client 1 (ville-lyon.geoclic.fr)
├──rsync──→ VPS Client 2 (ville-marseille.geoclic.fr)
└──rsync──→ VPS Client N (...)
```

Le serveur maître (geoclic.fr) centralise le code et le pousse vers les clients via rsync/SSH. Chaque client a sa propre base de données, son propre certificat SSL et fonctionne de manière indépendante.

## Accéder au Fleet Manager

Ouvrez votre navigateur et allez sur :

```
https://geoclic.fr/fleet/
```

Connectez-vous avec votre compte **super admin** GéoClic.

Le dashboard affiche l'état de tous vos serveurs, et vous permet d'ajouter, mettre à jour et gérer chaque client.

**L'aide complète est disponible dans l'application : onglet "Aide" dans la barre de navigation.**

## Installation initiale (une seule fois)

Sur le serveur maître (geoclic.fr), exécutez :

```bash
sudo bash /opt/geoclic/fleet/setup-master.sh
```

Ce script :
1. Génère une clé SSH dédiée au fleet manager
2. Crée les dossiers nécessaires
3. Configure nginx pour la route `/fleet/`
4. Build et démarre le conteneur Docker fleet
5. Affiche l'URL du dashboard et la clé SSH à copier

## Ajouter un nouveau client

### Prérequis

1. **Un VPS chez OVH** (Ubuntu 22.04 ou 24.04)
   - VPS Starter (2 Go RAM) minimum pour une petite commune
2. **Un nom de domaine** pointant vers le VPS
   - Ex: enregistrement DNS A : `ville-lyon.geoclic.fr` → `51.210.42.100`
3. **La clé SSH fleet** copiée sur le VPS

### Procédure (depuis le dashboard web)

1. Allez sur `https://geoclic.fr/fleet/`
2. Cliquez **"+ Nouveau serveur"**
3. Remplissez :
   - **Domaine** : `ville-lyon.geoclic.fr`
   - **IP** : `51.210.42.100`
   - **Email** : `admin@ville-lyon.fr`
4. Copiez la clé SSH affichée et ajoutez-la sur le VPS :
   ```bash
   # Sur le VPS (via la console OVH ou SSH avec mot de passe)
   echo "ssh-ed25519 AAAA... geoclic-fleet" >> ~/.ssh/authorized_keys
   ```
5. Cliquez **"Tester la connexion SSH"** → doit afficher vert
6. Cliquez **"Lancer l'installation"**
7. Attendez ~15 minutes (progression en temps réel)
8. C'est terminé ! Le client est accessible sur `https://ville-lyon.geoclic.fr`

### Procédure alternative (en terminal)

```bash
sudo bash /opt/geoclic/fleet/geoclic-fleet.sh provision \
  --name ville-lyon \
  --domain ville-lyon.geoclic.fr \
  --ip 51.210.42.100 \
  --email admin@ville-lyon.fr
```

## Mettre à jour les serveurs

### Depuis le dashboard

- **Un seul serveur** : Cliquez sur le serveur → "Mettre à jour"
- **Tous les serveurs** : Cliquez "Tout mettre à jour" sur le dashboard

### En terminal

```bash
# Tous les clients
sudo bash /opt/geoclic/fleet/geoclic-fleet.sh update --all

# Un seul client
sudo bash /opt/geoclic/fleet/geoclic-fleet.sh update --client ville-lyon

# Avec une migration SQL
sudo bash /opt/geoclic/fleet/geoclic-fleet.sh update --client ville-lyon --migration 023_new_feature.sql

# Seulement certains services
sudo bash /opt/geoclic/fleet/geoclic-fleet.sh update --client ville-lyon --services "api portail demandes"
```

## Commandes disponibles (terminal)

Toutes les commandes s'exécutent avec :
```bash
sudo bash /opt/geoclic/fleet/geoclic-fleet.sh <commande> [options]
```

| Commande | Description |
|----------|-------------|
| `provision` | Installer GéoClic sur un nouveau VPS |
| `update` | Mettre à jour un ou tous les serveurs |
| `status` | Voir l'état des serveurs |
| `list` | Lister les serveurs enregistrés |
| `add` | Ajouter un serveur au registre |
| `remove` | Retirer un serveur du registre |
| `ssh` | Se connecter en SSH à un serveur |
| `logs` | Voir les logs Docker d'un serveur |
| `backup` | Lancer une sauvegarde |
| `ssh-key` | Gérer la clé SSH fleet |
| `test-ssh` | Tester la connexion SSH |

## Ce qui est installé sur chaque serveur client

| Composant | Détail |
|-----------|--------|
| Docker + Compose | Dernière version |
| Certbot | Certificat SSL Let's Encrypt (renouvellement auto) |
| Cron backup | Sauvegarde DB + photos quotidienne à 2h |
| Cron monitoring | Vérification toutes les 5 minutes |
| Service systemd | Démarrage auto des conteneurs au boot |
| GéoClic Suite | 10 conteneurs Docker |

## Sécurité

- **Accès fleet** : Réservé au super_admin (vérification JWT)
- **Clé SSH dédiée** : Séparée de votre clé personnelle
- **Isolation clients** : Chaque client a sa propre DB et ses propres secrets
- **Pas de code fleet chez les clients** : Le dossier `fleet/` est exclu du rsync
- **Secrets uniques** : JWT_SECRET_KEY et DB_PASSWORD générés aléatoirement par client

## Structure des fichiers

```
fleet/
├── geoclic-fleet.sh          # Script principal (CLI)
├── clients.conf              # Registre des serveurs clients
├── setup-master.sh           # Installation initiale (une seule fois)
├── Dockerfile                # Build du conteneur fleet
├── docker-compose.fleet.yml  # Template docker-compose
├── nginx-fleet.conf          # Configuration nginx pour /fleet/
├── api/                      # API Python FastAPI
│   ├── main.py
│   └── requirements.txt
├── web/                      # Dashboard Vue.js
│   ├── src/views/            # Pages (Dashboard, AddServer, Help...)
│   └── package.json
├── logs/                     # Logs des opérations (auto-créé)
└── tasks/                    # État des tâches en cours (auto-créé)
```

## Dépannage

### Le dashboard est inaccessible
```bash
cd /opt/geoclic/deploy && sudo docker compose ps fleet
sudo docker compose build fleet && sudo docker compose up -d fleet nginx
```

### La connexion SSH échoue
```bash
# Afficher la clé publique
sudo cat /home/ubuntu/.ssh/geoclic_fleet_key.pub

# Tester manuellement
sudo -u ubuntu ssh -i /home/ubuntu/.ssh/geoclic_fleet_key ubuntu@IP_DU_VPS "echo ok"
```

### Le certificat SSL ne s'installe pas
- Vérifier que le domaine pointe vers l'IP : `nslookup ville.geoclic.fr`
- Vérifier que le port 80 est accessible (pas de pare-feu OVH)
- Let's Encrypt : max 5 certificats par domaine par semaine

### Build Docker échoue sur un client
```bash
# Se connecter au client
sudo bash /opt/geoclic/fleet/geoclic-fleet.sh ssh ville-lyon

# Sur le client :
cd /opt/geoclic/deploy
sudo docker compose logs api
sudo docker system prune -f  # Libérer de l'espace disque
```

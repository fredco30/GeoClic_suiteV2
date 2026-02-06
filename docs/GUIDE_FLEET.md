# GéoClic Fleet Manager - Guide d'utilisation

Outil de gestion centralisée pour déployer et maintenir GéoClic sur plusieurs serveurs clients.

## Architecture

```
Votre machine (code source)
    │
    ├── rsync ──→ VPS Client 1 (ville-lyon.geoclic.fr)
    ├── rsync ──→ VPS Client 2 (ville-marseille.geoclic.fr)
    └── rsync ──→ VPS Client N (...)
```

Le code est poussé directement depuis votre machine vers les serveurs via rsync. Pas de dépendance GitHub sur les serveurs.

## Prérequis

### Sur votre machine (gestion)
- `rsync`, `curl`, `openssl`, `ssh`
- Le code source du projet

### Sur chaque VPS client
- Ubuntu 22.04 ou plus récent
- Accès SSH avec clé publique
- L'utilisateur SSH doit pouvoir utiliser `sudo` sans mot de passe

## Premiers pas

### 1. Configurer l'accès SSH au nouveau VPS

```bash
# Copier votre clé SSH sur le VPS
ssh-copy-id ubuntu@51.210.8.158

# Vérifier que ça marche
ssh ubuntu@51.210.8.158 "echo ok"

# Configurer sudo sans mot de passe (si pas déjà fait)
ssh ubuntu@51.210.8.158
echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/ubuntu
exit
```

### 2. Provisionner un nouveau client

```bash
cd fleet/

./geoclic-fleet.sh provision \
  --name ville-test \
  --domain test.geoclic.fr \
  --ip 51.210.8.158 \
  --email admin@test.fr \
  --ssh-user ubuntu
```

Le script fait tout automatiquement :
1. Met à jour le système
2. Installe Docker
3. Envoie le code via rsync
4. Génère le .env avec des secrets uniques
5. Obtient un certificat SSL Let's Encrypt
6. Build et démarre les conteneurs Docker
7. Initialise la base de données
8. Configure cron (backups) et systemd (démarrage auto)

### 3. Enregistrer un serveur existant

Si vous avez déjà un serveur GéoClic en production :

```bash
./geoclic-fleet.sh add \
  --name geoclic-prod \
  --domain geoclic.fr \
  --ip geoclic.fr \
  --ssh-user ubuntu
```

## Commandes

### Mise à jour

```bash
# Mettre à jour tous les clients d'un coup
./geoclic-fleet.sh update --all

# Mettre à jour un seul client
./geoclic-fleet.sh update --client ville-lyon

# Mettre à jour seulement certains services
./geoclic-fleet.sh update --client ville-lyon --services "api portail demandes"
```

Le processus de mise à jour :
1. Backup automatique de la DB avant mise à jour
2. Envoi du nouveau code via rsync
3. Application des migrations SQL
4. Rebuild des conteneurs Docker
5. Vérification de santé (API /health)

### Monitoring

```bash
# État rapide (HTTP check + SSL)
./geoclic-fleet.sh status

# État détaillé (inclut les conteneurs Docker via SSH)
./geoclic-fleet.sh status --detailed

# Dashboard temps réel (se rafraîchit toutes les 30 secondes)
./geoclic-fleet.sh dashboard

# Dashboard avec intervalle personnalisé
./geoclic-fleet.sh dashboard --interval 15
```

### Opérations courantes

```bash
# Lister les clients
./geoclic-fleet.sh list

# Se connecter en SSH à un client
./geoclic-fleet.sh ssh ville-lyon

# Voir les logs
./geoclic-fleet.sh logs ville-lyon
./geoclic-fleet.sh logs ville-lyon --service api --lines 100
./geoclic-fleet.sh logs ville-lyon --service db

# Sauvegarder
./geoclic-fleet.sh backup --client ville-lyon
./geoclic-fleet.sh backup --all

# Retirer un client du registre
./geoclic-fleet.sh remove --name ville-lyon
```

## Fichier clients.conf

Le registre des clients est un fichier texte simple :

```
# Format: NOM|DOMAINE|IP|SSH_USER|SSH_PORT|METHOD|DATE_AJOUT
geoclic-prod|geoclic.fr|geoclic.fr|ubuntu|22|rsync|2026-02-06
ville-lyon|lyon.geoclic.fr|51.210.42.100|ubuntu|22|rsync|2026-02-07
```

Vous pouvez l'éditer à la main si besoin.

## Ce qui est installé sur chaque serveur

| Composant | Détail |
|-----------|--------|
| Docker + Compose | Dernière version |
| Certbot | Certificat SSL Let's Encrypt (renouvellement auto) |
| Cron backup | Sauvegarde DB quotidienne à 2h |
| Cron monitoring | Vérification toutes les 5 minutes |
| Service systemd | Démarrage auto des conteneurs au boot |
| GéoClic Suite | 10 conteneurs Docker (db, api, admin, portail, demandes, sig, services, terrain, mobile, nginx) |

## Dépannage

### "Connexion SSH impossible"
```bash
# Vérifier que la clé SSH est copiée
ssh-copy-id ubuntu@IP_DU_VPS

# Vérifier que le VPS répond
ssh ubuntu@IP_DU_VPS "echo ok"
```

### "sudo sans mot de passe"
```bash
ssh ubuntu@IP_DU_VPS
echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/ubuntu
exit
```

### "Certificat SSL non obtenu"
Le domaine doit pointer vers l'IP du VPS (enregistrement DNS A).
```bash
# Vérifier le DNS
dig +short votre-domaine.fr

# Relancer certbot manuellement
./geoclic-fleet.sh ssh ville-x
sudo certbot certonly --standalone -d votre-domaine.fr
```

### "Build Docker échoue"
```bash
# Se connecter et vérifier les logs
./geoclic-fleet.sh ssh ville-x
cd /opt/geoclic/deploy
sudo docker compose logs api
sudo docker compose build api 2>&1 | tail -30
```

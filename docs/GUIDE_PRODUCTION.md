# GéoClic Suite - Guide de Production

Ce guide explique comment maintenir ton application en production sans faire appel à un développeur.

---

## Table des matières

1. [Vérification quotidienne](#1-vérification-quotidienne)
2. [Sauvegardes](#2-sauvegardes)
3. [Problèmes courants et solutions](#3-problèmes-courants-et-solutions)
4. [Restauration après un crash](#4-restauration-après-un-crash)
5. [Mise à jour de l'application](#5-mise-à-jour-de-lapplication)
6. [Commandes de référence](#6-commandes-de-référence)

---

## 1. Vérification quotidienne

### Vérifier que tout fonctionne (30 secondes)

```bash
sudo /opt/geoclic/scripts/monitor.sh
```

**Ce que tu dois voir:**
```
[OK] API répond correctement
[OK] geoclic_db (running)
[OK] geoclic_api (running)
[OK] geoclic_nginx (running)
...
Tout est OK
```

**Si tu vois des [ERREUR]:** Va à la section [Problèmes courants](#3-problèmes-courants-et-solutions).

---

## 2. Sauvegardes

### Comment ça fonctionne

- **Automatique:** Une sauvegarde est créée chaque nuit à 2h du matin
- **Rétention:** Les 7 dernières sauvegardes sont conservées
- **Emplacement:** `/opt/geoclic/backups/`

### Vérifier les sauvegardes

```bash
# Voir les sauvegardes disponibles
ls -lh /opt/geoclic/backups/
```

Tu dois voir des fichiers comme:
```
geoclic_backup_20260203_020000.sql.gz   24K
geoclic_backup_20260202_020000.sql.gz   24K
...
```

### Faire une sauvegarde manuelle

Avant une opération risquée (mise à jour, modification):
```bash
sudo /opt/geoclic/scripts/backup_db.sh
```

### Restaurer une sauvegarde

**ATTENTION: Cette opération efface toutes les données actuelles!**

```bash
# 1. Voir les sauvegardes disponibles
ls -lh /opt/geoclic/backups/

# 2. Restaurer (remplace XXXXXXXX par la date de la sauvegarde)
sudo /opt/geoclic/scripts/restore_db.sh geoclic_backup_XXXXXXXX_XXXXXX.sql.gz

# 3. Redémarrer l'API
cd /opt/geoclic/deploy && sudo docker-compose restart api
```

---

## 3. Problèmes courants et solutions

### L'API ne répond pas (HTTP erreur ou timeout)

**Symptôme:** Le monitoring affiche `[ERREUR] API ne répond pas`

**Solution:**
```bash
# 1. Vérifier si le conteneur API est actif
sudo docker ps | grep geoclic_api

# 2. Si le conteneur n'apparaît pas, le redémarrer
cd /opt/geoclic/deploy && sudo docker-compose up -d api

# 3. Si ça ne fonctionne toujours pas, voir les logs
sudo docker logs geoclic_api --tail 50
```

### Un conteneur est arrêté

**Symptôme:** Le monitoring affiche `[ERREUR] geoclic_XXX n'est pas en cours d'exécution`

**Solution:**
```bash
# Redémarrer le conteneur problématique (remplace XXX par le nom)
cd /opt/geoclic/deploy && sudo docker-compose up -d XXX

# Exemple pour l'API:
cd /opt/geoclic/deploy && sudo docker-compose up -d api

# Exemple pour Nginx:
cd /opt/geoclic/deploy && sudo docker-compose up -d nginx
```

### Le site est inaccessible (ERR_CONNECTION_REFUSED)

**Cause probable:** Nginx n'est pas démarré.

**Solution:**
```bash
cd /opt/geoclic/deploy && sudo docker-compose up -d nginx
```

### Disque presque plein

**Symptôme:** Le monitoring affiche `[WARN] Utilisation: XX% - ATTENTION disque presque plein`

**Solutions:**
```bash
# 1. Voir ce qui prend de la place
sudo du -sh /opt/geoclic/*

# 2. Nettoyer les vieilles images Docker (sans risque)
sudo docker system prune -f

# 3. Si le problème persiste, nettoyer les logs Docker
sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

### Erreur "KeyError: ContainerConfig" lors d'un rebuild

**Symptôme:** `docker-compose up -d --build` échoue avec cette erreur.

**Solution:**
```bash
# Arrêter et nettoyer
cd /opt/geoclic/deploy
sudo docker-compose down
sudo docker container prune -f

# Reconstruire
sudo docker-compose up -d --build
```

### Le certificat SSL a expiré

**Symptôme:** Message "Connexion non sécurisée" dans le navigateur.

**Vérifier:**
```bash
sudo certbot certificates
```

**Renouveler manuellement:**
```bash
sudo certbot renew
cd /opt/geoclic/deploy && sudo docker-compose restart nginx
```

---

## 4. Restauration après un crash

### Scénario: Le serveur a redémarré

```bash
# 1. Vérifier l'état
cd /opt/geoclic/deploy && sudo docker-compose ps

# 2. Si des services sont arrêtés, tout redémarrer
sudo docker-compose up -d

# 3. Vérifier
sudo /opt/geoclic/scripts/monitor.sh
```

### Scénario: La base de données est corrompue

```bash
# 1. Arrêter l'API
cd /opt/geoclic/deploy && sudo docker-compose stop api

# 2. Restaurer la dernière sauvegarde
ls -lh /opt/geoclic/backups/
sudo /opt/geoclic/scripts/restore_db.sh geoclic_backup_XXXXXXXX_XXXXXX.sql.gz

# 3. Redémarrer
sudo docker-compose up -d
```

### Scénario: Tout est cassé, retour à zéro

```bash
# 1. Arrêter tout
cd /opt/geoclic/deploy && sudo docker-compose down

# 2. Repartir proprement
sudo docker-compose up -d

# 3. Si la DB est vide, restaurer une sauvegarde
sudo /opt/geoclic/scripts/restore_db.sh geoclic_backup_XXXXXXXX_XXXXXX.sql.gz

# 4. Redémarrer l'API
sudo docker-compose restart api
```

---

## 5. Mise à jour de l'application

### Procédure standard

```bash
# 1. Faire une sauvegarde AVANT
sudo /opt/geoclic/scripts/backup_db.sh

# 2. Récupérer les mises à jour
cd /opt/geoclic && sudo git pull origin [NOM_BRANCHE]

# 3. Reconstruire les services modifiés
cd /opt/geoclic/deploy && sudo docker-compose up -d --build api portail demandes

# 4. Vérifier que tout fonctionne
sudo /opt/geoclic/scripts/monitor.sh
```

### Si la mise à jour casse quelque chose

```bash
# 1. Voir les logs pour comprendre
sudo docker logs geoclic_api --tail 100

# 2. Si c'est grave, restaurer la sauvegarde faite avant
sudo /opt/geoclic/scripts/restore_db.sh [fichier_sauvegarde]

# 3. Revenir au code précédent
cd /opt/geoclic && sudo git checkout HEAD~1

# 4. Reconstruire
cd /opt/geoclic/deploy && sudo docker-compose up -d --build
```

---

## 6. Commandes de référence

### Monitoring et diagnostic

| Action | Commande |
|--------|----------|
| Voir l'état général | `sudo /opt/geoclic/scripts/monitor.sh` |
| Voir les conteneurs actifs | `sudo docker ps` |
| Voir les logs d'un conteneur | `sudo docker logs geoclic_api --tail 50` |
| Voir les logs en temps réel | `sudo docker logs -f geoclic_api` |
| Voir l'espace disque | `df -h` |
| Voir la mémoire | `free -h` |

### Gestion des services

| Action | Commande |
|--------|----------|
| Démarrer tout | `cd /opt/geoclic/deploy && sudo docker-compose up -d` |
| Arrêter tout | `cd /opt/geoclic/deploy && sudo docker-compose down` |
| Redémarrer un service | `cd /opt/geoclic/deploy && sudo docker-compose restart api` |
| Reconstruire un service | `cd /opt/geoclic/deploy && sudo docker-compose up -d --build api` |
| Voir l'état | `cd /opt/geoclic/deploy && sudo docker-compose ps` |

### Sauvegardes

| Action | Commande |
|--------|----------|
| Sauvegarde manuelle | `sudo /opt/geoclic/scripts/backup_db.sh` |
| Voir les sauvegardes | `ls -lh /opt/geoclic/backups/` |
| Restaurer | `sudo /opt/geoclic/scripts/restore_db.sh [fichier]` |
| Voir les logs de backup | `sudo tail -50 /var/log/geoclic_backup.log` |

### SSL

| Action | Commande |
|--------|----------|
| Voir les certificats | `sudo certbot certificates` |
| Renouveler manuellement | `sudo certbot renew` |
| Vérifier le timer | `sudo systemctl status certbot.timer` |

---

## Checklist en cas de problème

1. **Exécuter le monitoring:** `sudo /opt/geoclic/scripts/monitor.sh`
2. **Identifier le problème:** Quel conteneur/service est en erreur ?
3. **Consulter les logs:** `sudo docker logs geoclic_XXX --tail 50`
4. **Tenter un redémarrage:** `cd /opt/geoclic/deploy && sudo docker-compose restart XXX`
5. **Si ça ne fonctionne pas:** Redémarrer tout avec `sudo docker-compose down && sudo docker-compose up -d`
6. **En dernier recours:** Restaurer une sauvegarde

---

## Contacts et ressources

- **Logs de monitoring:** `/var/log/geoclic_monitor.log`
- **Logs de backup:** `/var/log/geoclic_backup.log`
- **Documentation technique:** `/opt/geoclic/CLAUDE.md`
- **Sauvegardes:** `/opt/geoclic/backups/`

---

*Document créé le 3 février 2026*

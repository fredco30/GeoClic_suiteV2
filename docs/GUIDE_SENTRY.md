# Guide Sentry - Monitoring des Erreurs GéoClic

## C'est quoi Sentry ?

Sentry est un service qui **surveille votre API en permanence**. Quand une erreur se produit (erreur 500, crash, bug), Sentry :
1. Capture l'erreur automatiquement
2. Vous envoie un **email** immédiatement
3. Vous montre le **détail complet** : quelle URL, quel endpoint, la trace technique

**Sans Sentry :** Vous ne savez pas que ça a cassé (sauf si un utilisateur vous appelle).
**Avec Sentry :** Vous recevez un email en 30 secondes.

---

## Étape 1 : Créer un compte Sentry (gratuit)

1. Allez sur **https://sentry.io/signup/**
2. Créez un compte (email + mot de passe, ou via GitHub/Google)
3. Le plan **Developer** (gratuit) permet **5 000 erreurs/mois** — largement suffisant

---

## Étape 2 : Créer un projet

1. Après connexion, cliquez **"Create Project"**
2. Choisissez la plateforme : **FastAPI** (ou Python si FastAPI n'apparaît pas)
3. Donnez un nom : **geoclic-api**
4. Cliquez **"Create Project"**

---

## Étape 3 : Récupérer votre clé DSN

Après la création du projet, Sentry vous affiche une page avec votre **DSN** (Data Source Name). Ça ressemble à :

```
https://abc123def456@o123456.ingest.sentry.io/789012
```

**Copiez cette clé**, c'est votre identifiant unique.

---

## Étape 4 : Configurer sur le serveur

Connectez-vous au serveur et ajoutez la variable d'environnement :

```bash
# Se connecter au serveur
ssh ubuntu@geoclic.fr

# Créer/éditer le fichier .env
cd /opt/geoclic/deploy
sudo nano .env
```

Ajoutez cette ligne (remplacez par VOTRE DSN) :

```
SENTRY_DSN=https://abc123def456@o123456.ingest.sentry.io/789012
```

Sauvegardez (Ctrl+O, Enter, Ctrl+X).

Puis redéployez l'API :

```bash
cd /opt/geoclic/deploy && sudo docker-compose down
sudo docker container prune -f
sudo docker-compose build --no-cache api
sudo docker-compose up -d
```

---

## Étape 5 : Vérifier que ça marche

```bash
# Vérifier les logs de l'API
sudo docker logs geoclic_api --tail 20
```

Vous devez voir :
```
GéoClic Suite V14 API - Démarrage...
Sentry activé (env: production)
```

Vérifiez aussi via le health endpoint :
```bash
curl -s http://localhost:8000/api/health | python3 -m json.tool
```

Vous devez voir `"sentry": {"status": "ok", "environment": "production"}`.

---

## Étape 6 : Tester avec une erreur volontaire

Pour vérifier que les erreurs arrivent bien dans Sentry, vous pouvez tester :

```bash
# Appeler un endpoint qui va provoquer une erreur
curl -s https://geoclic.fr/api/demandes/not-a-uuid
```

Si tout est bien configuré, vous recevrez un email de Sentry dans les 30 secondes avec le détail de l'erreur.

---

## Utilisation quotidienne

### Consulter les erreurs

1. Allez sur **https://sentry.io** et connectez-vous
2. Cliquez sur votre projet **geoclic-api**
3. Vous verrez la liste des erreurs, triées par fréquence

### Ce que vous voyez pour chaque erreur

| Information | Exemple |
|---|---|
| **Type d'erreur** | `ValueError: invalid UUID` |
| **URL** | `GET /api/demandes/abc` |
| **Nombre d'occurrences** | 15 fois cette semaine |
| **Première/dernière fois** | Première : 3 fév, Dernière : 7 fév |
| **Trace complète** | Fichier, ligne, fonction exacte |

### Notifications par email

Par défaut, Sentry vous envoie un email :
- Quand une **nouvelle** erreur apparaît (jamais vue avant)
- Quand une erreur **revient** après avoir été résolue
- **Résumé hebdomadaire** de toutes les erreurs

Vous pouvez personnaliser dans **Settings > Notifications**.

### Résoudre une erreur

1. Corrigez le bug dans le code
2. Déployez la correction
3. Dans Sentry, cliquez **"Resolve"** sur l'erreur
4. Si l'erreur revient après le déploiement, Sentry vous re-notifie (régression)

---

## Configuration avancée (optionnel)

### Changer l'environnement

Si vous avez un serveur de test et un serveur de production :

```bash
# Serveur de test
SENTRY_ENVIRONMENT=staging

# Serveur de production
SENTRY_ENVIRONMENT=production
```

Dans Sentry, vous pourrez filtrer par environnement.

### Ajuster le taux de traces performance

Par défaut, 10% des requêtes sont tracées pour le monitoring de performance :

```bash
# 10% (par défaut) - suffisant pour voir les tendances
SENTRY_TRACES_RATE=0.1

# 100% (dev/test) - toutes les requêtes sont tracées
SENTRY_TRACES_RATE=1.0

# 1% (si beaucoup de trafic) - pour réduire la consommation du quota
SENTRY_TRACES_RATE=0.01
```

### Désactiver temporairement Sentry

Il suffit de supprimer ou vider la variable `SENTRY_DSN` dans le `.env` et de redémarrer l'API :

```bash
# Dans .env, commenter la ligne :
# SENTRY_DSN=https://...

# Redémarrer
cd /opt/geoclic/deploy && sudo docker-compose restart api
```

---

## Multi-serveurs avec Fleet Manager

Si vous avez plusieurs serveurs clients via le Fleet Manager, **chaque serveur envoie ses erreurs au même dashboard Sentry**. Vous pouvez distinguer les serveurs grâce à `SENTRY_ENVIRONMENT` :

```bash
# Serveur client Mairie de Lyon
SENTRY_ENVIRONMENT=lyon

# Serveur client Mairie de Bordeaux
SENTRY_ENVIRONMENT=bordeaux
```

Dans Sentry, vous filtrez par environnement pour voir les erreurs de chaque client. **Pas besoin de SSH ni de Fleet** pour consulter les erreurs.

---

## Coûts

| Plan | Prix | Quota erreurs | Suffisant pour |
|---|---|---|---|
| **Developer** (gratuit) | 0 EUR/mois | 5 000 erreurs/mois | 1-3 serveurs |
| **Team** | ~26 USD/mois | 50 000 erreurs/mois | 10+ serveurs |
| **Business** | ~80 USD/mois | 100 000+ erreurs/mois | Grosse infrastructure |

Pour commencer, le plan **gratuit** suffit largement.

---

## Résumé des commandes

```bash
# Vérifier que Sentry est actif
sudo docker logs geoclic_api 2>&1 | grep -i sentry

# Vérifier via le health endpoint
curl -s http://localhost:8000/api/health | python3 -m json.tool

# Redémarrer l'API après changement de config
cd /opt/geoclic/deploy && sudo docker-compose restart api
```

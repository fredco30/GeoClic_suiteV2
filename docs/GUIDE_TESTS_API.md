# Guide des Tests Automatisés - GéoClic Suite

> **Pour qui ?** Ce guide est destiné à l'administrateur de GéoClic Suite qui n'a pas de connaissances techniques Linux. Toutes les commandes sont à copier-coller telles quelles.

---

## Pourquoi des tests automatisés ?

### Le problème sans tests

Imagine cette situation :
1. Tu modifies le code pour ajouter une nouvelle fonctionnalité
2. Tu déploies sur le serveur
3. Le lendemain, un utilisateur t'appelle : "L'application ne marche plus !"
4. Tu passes des heures à chercher ce qui a cassé

### La solution avec tests

1. Tu modifies le code pour ajouter une nouvelle fonctionnalité
2. **Tu lances les tests** → En 30 secondes, tu sais si quelque chose est cassé
3. Si tout est vert : tu déploies sereinement
4. Si quelque chose est rouge : tu corriges AVANT de déployer

**Les tests sont ton filet de sécurité.**

---

## Commandes Rapides (Copier-Coller)

### Lancer tous les tests (vérification complète)

```bash
# Copie-colle ces 2 lignes dans ton terminal
cd /opt/geoclic/deploy
sudo docker exec -it geoclic_api pytest -v
```

### Lancer uniquement les tests rapides (santé API)

```bash
cd /opt/geoclic/deploy
sudo docker exec -it geoclic_api pytest tests/test_health.py -v
```

### Installer les dépendances de test (première fois uniquement)

```bash
cd /opt/geoclic/deploy
sudo docker exec -it geoclic_api pip install -r requirements-test.txt
```

---

## Comprendre les Résultats

### Exemple de sortie réussie

```
tests/test_health.py::TestHealthEndpoints::test_root_endpoint PASSED
tests/test_health.py::TestHealthEndpoints::test_health_check PASSED
tests/test_auth.py::TestAuthTokenEndpoints::test_login_with_valid_credentials PASSED

========================= 3 passed in 2.34s =========================
```

**Que signifie `PASSED` ?** Le test a vérifié quelque chose et ça fonctionne correctement.

### Exemple de sortie avec erreur

```
tests/test_health.py::TestHealthEndpoints::test_root_endpoint PASSED
tests/test_demandes.py::TestCategoriesEndpoints::test_create_category FAILED

FAILED tests/test_demandes.py::TestCategoriesEndpoints::test_create_category
    AssertionError: assert 500 == 200

========================= 1 failed, 1 passed in 3.12s =========================
```

**Que signifie `FAILED` ?**
- Le test a détecté un problème
- L'API a répondu avec une erreur 500 au lieu de 200
- **Il y a un bug à corriger AVANT de déployer**

### Les différents statuts

| Statut | Signification | Action |
|--------|---------------|--------|
| `PASSED` | Tout va bien | Rien à faire |
| `FAILED` | Bug détecté | Corriger avant déploiement |
| `SKIPPED` | Test ignoré | Normal (dépendance manquante) |
| `ERROR` | Problème dans le test | Me contacter |

---

## Quand Lancer les Tests ?

### Avant chaque déploiement (OBLIGATOIRE)

```bash
cd /opt/geoclic/deploy
sudo docker exec -it geoclic_api pytest -v
```

Si tous les tests passent → tu peux déployer
Si un test échoue → **NE PAS DÉPLOYER**, corriger d'abord

### Après une mise à jour du code

```bash
# 1. Mettre à jour le code
cd /opt/geoclic && sudo git pull origin claude/setup-geoclic-suite-JpjDO

# 2. Reconstruire l'API
cd /opt/geoclic/deploy && sudo docker-compose up -d --build api

# 3. Lancer les tests
sudo docker exec -it geoclic_api pytest -v

# 4. Si tout est vert, redémarrer les autres services
sudo docker-compose up -d
```

### Pour vérifier que tout fonctionne (diagnostic)

```bash
cd /opt/geoclic/deploy
sudo docker exec -it geoclic_api pytest tests/test_health.py -v
```

Ce test rapide vérifie que :
- L'API démarre correctement
- La base de données est connectée
- Les routes principales répondent

---

## Que Testent les Fichiers ?

### test_health.py - "L'API est-elle vivante ?"
- L'API démarre sans erreur
- L'endpoint `/` répond
- L'endpoint `/api/health` confirme la connexion DB
- La documentation Swagger est accessible

### test_auth.py - "La connexion fonctionne-t-elle ?"
- Login avec identifiants corrects → token reçu
- Login avec mauvais mot de passe → rejeté
- Accès sans token → rejeté
- Token expiré → rejeté

### test_demandes.py - "Les demandes citoyens fonctionnent-elles ?"
- Lister les catégories
- Créer une catégorie
- Lister les demandes
- Voir le détail d'une demande
- Changer le statut d'une demande
- Changer la priorité

### test_services.py - "Les services municipaux fonctionnent-ils ?"
- Lister les services
- Créer un service
- Modifier un service
- Supprimer un service
- Gérer les agents d'un service

---

## Résolution de Problèmes

### "Command not found: pytest"

Les dépendances de test ne sont pas installées.

```bash
cd /opt/geoclic/deploy
sudo docker exec -it geoclic_api pip install -r requirements-test.txt
```

### "Connection refused" ou erreur de base de données

La base de données n'est pas accessible. Vérifie que le conteneur DB tourne :

```bash
cd /opt/geoclic/deploy
sudo docker-compose ps
```

Si `geoclic_db` n'apparaît pas ou est "Exit", relance-le :

```bash
sudo docker-compose up -d db
# Attendre 10 secondes que la DB démarre
sleep 10
# Relancer les tests
sudo docker exec -it geoclic_api pytest -v
```

### Beaucoup de tests échouent

1. **Vérifie que l'API est bien démarrée :**
```bash
cd /opt/geoclic/deploy && sudo docker-compose ps
```

2. **Regarde les logs de l'API :**
```bash
sudo docker-compose logs api --tail=50
```

3. **Redémarre tout :**
```bash
sudo docker-compose down
sudo docker-compose up -d
# Attendre 30 secondes
sleep 30
sudo docker exec -it geoclic_api pytest -v
```

### Un seul test échoue

C'est probablement un vrai bug. Note le nom du test qui échoue et contacte-moi avec :
- Le nom du test (ex: `test_demandes.py::TestCategoriesEndpoints::test_create_category`)
- Le message d'erreur complet
- Ce que tu as fait juste avant (modification de code, mise à jour, etc.)

---

## Bonnes Pratiques

### Avant de déployer une modification

```bash
# 1. Mettre à jour le code
cd /opt/geoclic && sudo git pull origin claude/setup-geoclic-suite-JpjDO

# 2. Reconstruire
cd /opt/geoclic/deploy && sudo docker-compose up -d --build api

# 3. TOUJOURS lancer les tests
sudo docker exec -it geoclic_api pytest -v

# 4. Seulement si tout est vert, continuer
sudo docker-compose up -d
sudo docker-compose ps
```

### Routine de vérification quotidienne (optionnel)

```bash
# Test rapide pour vérifier que tout va bien
cd /opt/geoclic/deploy
sudo docker exec -it geoclic_api pytest tests/test_health.py -v
```

---

## Résumé en 1 Page

| Quoi faire | Commande |
|------------|----------|
| **Lancer tous les tests** | `cd /opt/geoclic/deploy && sudo docker exec -it geoclic_api pytest -v` |
| **Test rapide (santé)** | `cd /opt/geoclic/deploy && sudo docker exec -it geoclic_api pytest tests/test_health.py -v` |
| **Installer dépendances** | `cd /opt/geoclic/deploy && sudo docker exec -it geoclic_api pip install -r requirements-test.txt` |

| Résultat | Signification |
|----------|---------------|
| Tous `PASSED` | Tu peux déployer |
| Un ou plusieurs `FAILED` | Bug détecté - NE PAS DÉPLOYER |

---

*Guide créé le 2 février 2026 - GéoClic Suite*

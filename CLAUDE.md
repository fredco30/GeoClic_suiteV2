# GéoClic Suite - Mémoire Projet

## Informations Serveur

**Serveur de production:**
- Chemin: `/opt/geoclic`
- Docker-compose: `/opt/geoclic/deploy`
- Toutes les commandes nécessitent `sudo`

**Noms des conteneurs Docker:**
- Base de données: `geoclic_db` (PostgreSQL + PostGIS)
- API: `geoclic_api`
- Admin: `geoclic_admin`
- Portail citoyen: `geoclic_portail`
- Back-office demandes: `geoclic_demandes`
- Mobile: `geoclic_mobile`
- SIG: `geoclic_sig`
- Services terrain (desktop): `geoclic_services`
- Services terrain (PWA mobile): `geoclic_terrain`
- Nginx: `geoclic_nginx`

**Noms des services docker-compose:**
- `db`, `api`, `admin`, `portail`, `demandes`, `mobile`, `sig`, `services`, `terrain`, `nginx`

**Base de données:**
- Nom: `geoclic_db`
- Utilisateur: `geoclic`
- Conteneur: `geoclic_db`

## Commandes de Déploiement Standard

```bash
# 1. Arrêter et nettoyer (évite erreur ContainerConfig)
cd /opt/geoclic/deploy && sudo docker-compose down
sudo docker container prune -f

# 2. Mettre à jour le code
cd /opt/geoclic && sudo git pull origin claude/hierarchical-zones-S5XGp

# 3. Appliquer une migration SQL (si nécessaire)
sudo docker exec -i geoclic_db psql -U geoclic -d geoclic_db < /opt/geoclic/database/migrations/NOM_MIGRATION.sql

# 4. Reconstruire les services
cd /opt/geoclic/deploy && sudo docker-compose build --no-cache api portail demandes

# 5. Démarrer tous les services
sudo docker-compose up -d

# 6. Vérifier l'état
sudo docker-compose ps
```

## Contraintes Utilisateur

- L'utilisateur n'a **aucune connaissance Linux** - toujours donner des commandes complètes avec `sudo`
- Ne jamais casser les autres modules (SIG, Mobile, Data, etc.)
- Toujours tester avant de déployer

## Structure du Projet

```
GeoClic_Suite/
├── api/                    # FastAPI backend
│   ├── routers/
│   │   ├── demandes.py     # API demandes citoyens
│   │   └── services.py     # API GeoClic Services
│   └── schemas/
│       ├── demandes.py     # Schémas demandes
│       └── services.py     # Schémas services
├── database/
│   └── migrations/         # Migrations SQL
├── deploy/
│   ├── docker-compose.yml  # Configuration Docker
│   └── www/                # Site commercial (servi par nginx)
│       ├── index.html      # Landing page
│       ├── fonctionnalites.html
│       ├── comparatif.html
│       ├── tarifs.html
│       └── screenshots/    # Images du site
├── fleet/                  # Fleet Manager multi-serveurs
│   ├── geoclic-fleet.sh    # CLI principal
│   └── clients.conf        # Registre serveurs
├── marketing/              # Sources site commercial (dev)
│   ├── index.html
│   ├── fonctionnalites.html
│   ├── comparatif.html
│   └── tarifs.html
├── geoclic_data/           # Admin (GéoClic Data)
├── geoclic_demandes/       # Back-office demandes
├── geoclic_services/       # App services terrain (desktop)
├── geoclic_services_pwa/   # PWA services terrain (mobile)
├── geoclic_mobile_pwa/     # PWA Mobile (relevé terrain)
├── geoclic_sig_web/        # SIG Web
├── portail_citoyen/        # Portail citoyen public
├── scripts/                # Scripts production (backup, monitor)
└── docs/                   # Documentation technique
```

## État d'Avancement - GeoClic Demandes V2

### Phase 1: Catégories hiérarchiques (TERMINÉ)
- Catégories avec parent/enfants
- Interface tuiles avec icônes/couleurs
- Migration `005_categories_hierarchiques.sql`

### Phase 2: Détection doublons (TERMINÉ)
- Colonnes `doublon_de_id`, `est_doublon`
- Fonction SQL `find_duplicate_demandes()`
- Endpoints API: `/doublons/check`, `/{id}/doublons`, `/{id}/marquer-doublon`
- Frontend portail: alerte avant soumission
- Frontend back-office: section doublons potentiels/liés
- Migration `006_doublons_detection.sql`

### Phase 3: Services et affectation (TERMINÉ)
- Table `demandes_services` pour services municipaux
- Table `demandes_services_agents` pour agents par service
- Migration `007_services_municipaux.sql`
- Endpoints API CRUD: `/services`, `/services/{id}`, `/services/stats/all`
- Trigger auto-affectation par catégorie (`trg_auto_assign_service`)
- Vue `v_stats_par_service` pour statistiques
- Interface gestion services: `ServicesView.vue` avec CRUD complet
- Liaison catégories-services: sélecteur service dans modal catégorie
- Affichage du service assigné dans la liste des sous-catégories

## État d'Avancement - GeoClic Services

### Phase 1: Fondations (TERMINÉ)
- Migration `008_geoclic_services.sql`: table messages tchat, colonnes auth agents
- Router API `/api/services/`: authentification JWT, CRUD demandes/messages/agents/stats
- Schémas Pydantic dans `api/schemas/services.py`
- CRUD agents depuis GeoClic Demandes dans `api/routers/demandes.py`
- Frontend Vue 3 complet dans `geoclic_services/`
  - Login, Dashboard, Liste demandes, Détail demande, Tchat, Gestion agents
- Configuration Docker et Nginx pour `/services/`

### Phase 2: Intégration tchat et actions (TERMINÉ)
- **GeoClic Demandes (back-office):**
  - Tchat intégré dans le détail demande (colonne droite)
  - Endpoints API messages dans `demandes.py`: GET/POST `/demandes/{id}/messages`
  - Badge messages non lus dans la liste des demandes
  - Polling 30s pour nouveaux messages
- **GeoClic Services (terrain):**
  - Tchat déplacé en colonne droite (layout 3 colonnes)
  - Boutons d'action: Prendre en charge, Planifier, Terminer, Rejeter
  - Modal affectation agent avec liste déroulante
  - Corrections UUID casting dans requêtes SQL
- Migration `010_add_commentaire_interne.sql`: colonne notes internes agents

### Phase 3: Notifications par email (TERMINÉ)
- Migration `011_email_settings.sql`: tables email_logs, email_reminders
- Service `notifications.py`: envoi emails citoyen et agents
- Interface paramétrage email dans GeoClic Demandes (Paramètres > Email)
- **Notifications citoyen:**
  - Confirmation de réception du signalement
  - Changement de statut (accepté, en cours, traité, rejeté)
- **Notifications agents terrain:**
  - Nouvelle demande assignée au service
  - Nouveau message tchat du back-office
  - Rappel avant intervention planifiée (configurable: 2h à 48h)
- Script `reminder_cron.py` pour rappels planifiés
- Support SMTP: Office 365, Gmail, serveurs classiques

### Améliorations UX (TERMINÉ)
- **Changement de priorité:**
  - API endpoint `PATCH /api/demandes/{id}/priorite`
  - Fonction `updatePriorite()` dans le store Pinia
  - Modal de sélection priorité dans le détail demande (bouton "Modifier")
  - Dropdown rapide dans la liste des demandes (clic sur le badge priorité)
- **Carte interactive:**
  - Composant MiniMap.vue avec Leaflet dans Demandes et Services

### Phase 4: PWA Terrain (TERMINÉ)
- **Application PWA distincte** (`geoclic_services_pwa/`) pour agents terrain sur mobile
- **Canaux de tchat séparés:**
  - Canal `backoffice`: communication Demandes ↔ Services (desktop)
  - Canal `terrain`: communication Services (desktop) ↔ Terrain (PWA mobile)
  - Demandes back-office ne voit PAS les messages terrain
  - Services desktop a 2 colonnes tchat (backoffice + terrain)
- **Types d'expéditeur:** `service` (desktop), `demandes` (back-office), `terrain` (PWA)
- **Filtrage des demandes:**
  - Paramètre API `my_demandes=true` pour filtrer par agent assigné
  - Terrain PWA ne voit que les demandes assignées à l'agent connecté
- **Carte interactive avec navigation:**
  - Composant `MobileMap.vue` avec Leaflet
  - Onglet "Carte" dans le détail demande (si coordonnées GPS présentes)
  - Boutons navigation vers Google Maps et Waze
- **Service Worker optimisé:**
  - Cache version `v2` pour forcer les mises à jour
  - Stratégie `network-first` pour JS/CSS (évite problèmes de cache)
  - Stratégie `cache-first` pour assets statiques
- **Couleurs uniques par participant** dans les tchats (hash-based)
- Docker: service `terrain`, conteneur `geoclic_terrain`, route `/terrain/`

### Phase 5: Zones géographiques hiérarchiques (TERMINÉ)
- **Structure hiérarchique à 3 niveaux:**
  - Niveau 1: Commune (racine)
  - Niveau 2: Quartier / IRIS
  - Niveau 3: Secteur
- **Migration 014:** Ajoute `parent_id`, `level`, `is_global` à la table `perimetres`
- **Vue récursive `v_zones_hierarchy`** pour la hiérarchie complète
- **Trigger `assign_quartier_to_demande`** mis à jour pour trouver la zone la plus précise
- **Import IRIS:** Crée automatiquement la commune (level=1) + quartiers IRIS (level=2)
- **geoclic_sig:** Affichage arborescent, filtre par niveau, couleurs par hiérarchie
- **geoclic_data:** Édition avec sélection parent, affichage niveau dans la liste
- **geoclic_demandes:** Filtres en cascade (Commune > Quartier > Secteur)

### Phase 6: Améliorations Portail Citoyen (TERMINÉ)
- **PWA Support:**
  - `manifest.json` pour installation sur mobile
  - `sw.js` Service Worker avec stratégies de cache optimisées
  - `offline.html` page hors-ligne
  - Network-first pour HTML/JS/CSS (évite problèmes de cache après déploiement)
  - Cache-first pour images/fonts uniquement
- **Carte plein écran pour localisation:**
  - Mode fullscreen dans MapPicker.vue
  - Barre d'adresse semi-transparente en haut
  - Bouton GPS flottant pour recentrer
  - Bouton "Valider cette position" en bas
  - Marqueur déplaçable préservé
- **Carte des signalements améliorée (CarteView.vue):**
  - Header collapsible (clic pour réduire/agrandir)
  - Légende dans bouton flottant "i"
  - Badge compteur de signalements
  - Photos affichées dans les popups (max 3, cliquables)
  - Conversion Material Icons → Emojis (park→🌳, route→🛣️, etc.)
  - Zones non-interactives (ne bloquent plus les clics sur marqueurs)
- **Page Suivi redesignée:**
  - Header compact horizontal (loupe à gauche du titre)
  - Réduction de ~300px à ~80px de hauteur
- **Mode sombre supprimé** (inutile, prenait de la place)
- **Fix chargement catégories:**
  - Fallback si table `sig_projects` n'existe pas
  - Endpoint `getCategoriesAll()` sans filtre project_id

### Phase 7: Corrections GeoClic Demandes (TERMINÉ)
- **Affichage catégories corrigé:**
  - Problème: affichait "route Pietonnier" (nom icône) au lieu de "Voirie › Pietonnier"
  - Solution: ajout `categorie_parent_nom` via JOIN sur catégorie parente
  - API: nouvelle jointure `LEFT JOIN demandes_categories cp ON c.parent_id = cp.id`
  - Schema: champ `categorie_parent_nom` dans `DemandeResponse`
  - Frontend: affichage "Parent › Enfant" dans la liste

### Phase 8: Système d'authentification unifiée (TERMINÉ)
- **Table `geoclic_users`:** Remplace l'ancienne table `users`
  - Rôles par application: `role_data`, `role_demandes`, `role_sig`, `role_terrain`
  - Super admin unique avec flag `is_super_admin`
  - Liaison service pour agents terrain (`service_id`)
- **Migration 015:** `015_geoclic_users.sql`
  - Fonction `create_super_admin()` pour changement de super admin
  - Triggers de protection (un seul super admin, non supprimable)
- **Router API unifié:** `/api/auth/`
  - Login: `POST /api/auth/login`
  - Info utilisateur: `GET /api/auth/me`
  - Changement mot de passe: `POST /api/auth/change-password`
  - CRUD utilisateurs: `/api/auth/users`
  - Changement super admin: `PUT /api/auth/super-admin`
- **geoclic_data mise à jour:**
  - Store auth: utilise `/api/auth/login`, vérifie `role_data`
  - Store users: CRUD complet avec rôles par application
  - Page utilisateurs: stats par app, création/édition multi-rôles
  - Page profil: affichage rôles, changement mot de passe
  - Bouton "Changer Super Admin" (visible uniquement au super admin)
- **Clés localStorage standardisées:**
  - `data_auth_token` pour GéoClic Data
  - `demandes_auth_token` pour GéoClic Demandes
  - `services_auth_token` pour GéoClic Services
  - `terrain_auth_token` pour Terrain PWA
  - `sig_auth_token` pour GéoClic SIG
- **Valeurs de rôles:**
  - role_data: `aucun`, `lecture`, `admin`
  - role_demandes: `aucun`, `agent`, `admin`
  - role_sig: `aucun`, `lecture`, `edition`
  - role_terrain: `aucun`, `agent`

### Phase 8 bis: Corrections authentification unifiée (TERMINÉ - février 2026)
- **Migration 016:** `016_fix_historique_fk.sql`
  - Corrige la FK `demandes_historique.agent_id` pour référencer `geoclic_users` au lieu de l'ancienne table `users`
- **Migration 017:** `017_sync_agents_to_geoclic_users.sql`
  - Synchronise les agents existants de `demandes_services_agents` vers `geoclic_users`
- **Corrections API services.py:**
  - Fix `get_current_agent`: ajout `role_demandes` dans la requête SQL
  - Fix calcul du rôle: `responsable` si `is_super_admin` OU `role_demandes='admin'`
  - Fix filtre `my_demandes`: recherche l'ID `demandes_services_agents` par email (car l'auth unifiée utilise `geoclic_users.id`)
  - Fix endpoints stats/agents: gestion du cas super_admin sans service_id
- **Corrections API demandes.py:**
  - Fix UUID casting dans `demandes_historique` INSERT
  - Sync création/modification agents vers les deux tables (`demandes_services_agents` ET `geoclic_users`)
- **Corrections Frontend geoclic_services:**
  - Store auth.ts: ajout champ `role` calculé à partir de `is_super_admin` et `role_demandes`
  - Menu "Agents" visible pour `role === 'responsable'` (super_admin ou role_demandes='admin')
- **Corrections Frontend geoclic_demandes:**
  - Fix localStorage key: `demandes_auth_token` au lieu de `auth_token`

### Phase 9: Planification d'interventions (TERMINÉ - février 2026)
- **Fonctionnalité de planification avec date/heure:**
  - Bouton "📅 Planifier intervention" dans geoclic_services (visible quand statut = "en_cours")
  - Modal avec sélecteur de date et heure
  - Pré-remplissage automatique: lendemain à 09:00
- **Modifications API:**
  - Schéma `ServiceDemandeStatutUpdate`: ajout champ `date_planification`
  - Schéma `ServiceDemandeDetail`: ajout champ `date_planification`
  - Endpoint `PUT /demandes/{id}/statut`: enregistre `date_planification` quand statut = "planifie"
  - Requête SQL get_demande: inclut `d.date_planification`
- **Modifications Frontend geoclic_services:**
  - Store demandes.ts: fonction `updateStatut()` accepte `date_planification`
  - DemandeDetailView.vue: modal planification, affichage dans timeline (point orange)
- **Affichage dans geoclic_demandes:** Date d'intervention visible dans le détail demande
- **Workflow des statuts:**
  ```
  Nouveau → (Prendre en charge) → En cours → (Planifier) → Planifié → (Traiter) → Traité
  ```

### Phase 10: Corrections API role checks (TERMINÉ - février 2026)
- **Problème:** Erreur 500 sur POST /api/projects et autres endpoints de geoclic_data
- **Cause:** Les routers API utilisaient `current_user["role"]` mais le nouveau système d'auth unifiée ne retourne plus ce champ (remplacé par `role_data`, `role_demandes`, etc.)
- **Routers corrigés:**
  - `projects.py` - 3 occurrences
  - `champs.py` - 4 occurrences
  - `imports.py` - 1 occurrence
  - `lexique.py` - 4 occurrences
  - `ogs.py` - 2 occurrences
  - `points.py` - 2 occurrences
  - `postgis.py` - 8 occurrences
  - `users.py` - 6 occurrences (router legacy)
- **Pattern de correction:**
  ```python
  # Avant
  if current_user["role"] != "admin":

  # Après
  if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
  ```

### Phase 10 bis: Améliorations UX geoclic_data (TERMINÉ - février 2026)
- **Boutons d'action sur les éléments de structure:**
  - Bouton Modifier (crayon) : visible au hover sur chaque Famille/Type/Sous-type
  - Bouton Supprimer (poubelle) : visible au hover, ouvre la confirmation existante
  - Les boutons remplacent le compteur de champs au survol
- **Dialogue de modification d'élément:**
  - Permet de changer : nom, icône, couleur
  - Le code (identifiant unique) est affiché mais non modifiable
  - Utilise le même sélecteur d'icônes par catégorie que la création
- **Corrections:**
  - Fix null reference error dans `saveEditedElement()` : sauvegarder le code avant de fermer le dialogue

### Phase 10 ter: Corrections back-office demandes et PWA mobile (TERMINÉ - février 2026)
- **Création/édition de demande depuis le back-office:**
  - `CreerDemandeView.vue` et `ModifierDemandeView.vue` : remplacement `<form>` par `<div>` pour empêcher la soumission sur Enter
  - Boutons `type="button"` au lieu de submit
  - Composant `FileDropZone.vue` : ajout `watch` sur `initialFiles` pour le mode édition (fichiers chargés async)
  - Composant `MapPickerBackoffice.vue` : recherche Nominatim async + auto-sélection du 1er résultat sur Enter
- **Historique demande robuste:**
  - API `demandes.py` : `CAST(:demande_id AS uuid)` dans requête historique
  - `COALESCE(commentaire_interne, FALSE)` et `COALESCE(email_envoye, FALSE)` pour colonnes nullable
  - Try/except par ligne avec fallback pour actions enum inconnues
  - Frontend `demandes.ts` store : `Promise.allSettled` au lieu de `Promise.all` (la page ne crash plus si historique échoue)
- **Icône catégorie dans détail demande:**
  - Mapping `iconToEmoji` dans `DemandeDetailView.vue` : convertit les noms Material Icons en emojis
  - Ex: `lightbulb` → `💡`, `park` → `🌳`, `route` → `🛣️`
- **Auth unifiée dans points.py:**
  - `check_user_permissions()` et `delete_point()` : pattern `is_super_admin or role_data == "admin"`
  - Logging détaillé dans `create_point` avec try/except
  - `CAST(:project_id AS uuid)` et `CAST(:created_by AS uuid)` dans INSERT
- **Migration 019:** `019_fix_geoclic_staging_fk.sql`
  - Corrige FK `geoclic_staging` (created_by, updated_by, validated_by) → `geoclic_users` (au lieu de l'ancienne table `users`)
- **PWA geoclic_mobile_pwa - chemins corrigés:**
  - `index.html` : préfixe `/mobile/` sur manifest, icon, apple-touch-icon
  - `main.ts` : suppression enregistrement manuel du SW (VitePWA `registerType: 'autoUpdate'` gère tout)
  - Icônes SVG au lieu de PNG inexistants

### Phase 11: Champs conditionnels et geoclic_mobile_pwa (TERMINÉ - février 2026)
- **Champs conditionnels dans geoclic_data:**
  - Interface pour configurer des champs qui s'affichent selon une condition
  - Options: champ déclencheur, opérateur (=, !=, contains, not_empty), valeur attendue
  - Badge "Conditionnel" visible dans la liste des champs
  - Documentation aide mise à jour (`geoclic_data/src/i18n/help/fr.ts`)
- **Support champs conditionnels dans geoclic_mobile_pwa:**
  - Interface `ChampDynamique` étendue avec `condition_field`, `condition_operator`, `condition_value`
  - Fonction `isFieldVisible()` pour évaluer les conditions
  - Computed `visibleFields` filtre les champs selon leurs conditions
  - Les champs apparaissent/disparaissent dynamiquement lors de la saisie
- **Corrections geoclic_mobile_pwa:**
  - **Endpoint d'authentification:** `/auth/token` → `/auth/login` (système unifié)
  - **Icônes catégories:** Les noms MDI (ex: "mdi-bench") s'affichaient en texte brut
    - Fix: Affichage d'un cercle coloré avec la première lettre du libellé
  - **Icônes PWA:** Manifest mis à jour pour utiliser le SVG existant au lieu des PNG manquants
- **Fichiers modifiés:**
  - `geoclic_mobile_pwa/src/services/api.ts` - Interface ChampDynamique + endpoint login
  - `geoclic_mobile_pwa/src/views/GeometryFormView.vue` - Logique champs conditionnels
  - `geoclic_mobile_pwa/src/components/LexiqueSelector.vue` - Fix affichage icônes
  - `geoclic_mobile_pwa/vite.config.ts` - Manifest PWA corrigé
  - `geoclic_data/src/i18n/help/fr.ts` - Documentation champs conditionnels

### Phase 12 : Sécurisation (TERMINÉ - février 2026)
- Voir section "Métriques de Suivi" pour le détail

### Phase 13 : Industrialisation (TERMINÉ - février 2026)
- Voir section "Métriques de Suivi" pour le détail

### Phase 14 : Produit Commercial (TERMINÉ - février 2026)

#### 14.1 - White-labeling
- **API Branding:** Endpoint public `GET /api/settings/branding` (sans auth) + endpoints admin CRUD
- **Table `system_settings`:** Stockage JSON (nom_collectivite, primary_color, secondary_color, accent_color, sidebar_color, logo_url, favicon_url, contact_email, contact_telephone, site_web)
- **Portail citoyen:** Chargement dynamique branding au démarrage, injection CSS variables, darkenColor/lightenColor helpers
- **geoclic_demandes:** Onglet "Personnalisation" dans Paramètres (color pickers, preview, champs contact)
- **geoclic_data:** Card branding dans la page Paramètres (Vuetify color pickers)
- **Fix auth:** 3 endpoints settings.py corrigés pour le système d'auth unifiée

#### 14.2 - Onboarding wizard
- **OnboardingWizard.vue:** Wizard 5 étapes (Identité → Email → Catégories → Services → Récap)
- **Templates catégories:** Standard (6 catégories + sous-catégories), Minimal (3), Personnalisé (aucune)
- **Services par défaut:** Service Technique, Espaces Verts, Propreté Urbaine
- **Détection automatique:** Vérifie `/api/settings/branding` pour `nom_collectivite`, skip si déjà configuré
- **Intégration App.vue:** Watch sur `authStore.isAuthenticated`, admin-only, localStorage flag

#### 14.3 - Dashboard dirigeant
- **API étendue:** Endpoint `/statistiques/dashboard` enrichi avec :
  - Distribution des statuts (8 statuts via COUNT FILTER)
  - Comparaison mois en cours vs mois précédent (volume, traitées, délai moyen)
  - Évolution 12 mois (agrégation mensuelle reçues/traitées)
  - Taux de résolution, nombre en cours, nombre rejetées
- **Schemas:** `ComparaisonPeriode`, `DistributionStatuts`, `DashboardStats` étendu
- **Frontend:** 2e ligne de KPI (taux résolution color-codé, comparaisons avec variations %), Doughnut statuts, Bar chart 12 mois
- **KPI existants préservés:** 5 cartes originales + section priorités + 4 graphiques originaux

#### 14.4 - Documentation utilisateur
- **4 guides par rôle** ajoutés dans `geoclic_demandes/src/i18n/help/fr.ts` :
  - Guide Administrateur (4 sections)
  - Guide Agent back-office (4 sections)
  - Guide Agent terrain (4 sections)
  - Guide Citoyen (3 sections)
- **FAQ portail citoyen:** 13 questions/réponses en 4 catégories (Signalement, Suivi, Carte, Données personnelles)
- **FaqView.vue:** Accordion avec recherche, filtre par catégorie, section contact dynamique
- **Route `/faq`** ajoutée au portail + lien dans le footer

#### 14.5 - Améliorations UX
- **Toast notifications:** Composable `useToast.ts` + `ToastContainer.vue` (Teleport, TransitionGroup, 4 types color-codés)
- **Breadcrumbs:** `Breadcrumbs.vue` (navigation contextuelle, route-aware, aria-label)
- **Intégration App.vue:** ToastContainer global + Breadcrumbs dans le main content

### Phase 14 bis : Corrections et centralisation paramètres (TERMINÉ - février 2026)

#### Centralisation des paramètres dans geoclic_data
- **geoclic_data** devient le seul module qui **écrit** les paramètres (branding, email, logo)
- **Tous les autres modules** (demandes, services, services_pwa, sig, portail) **lisent** via `GET /api/settings/branding` (public, sans auth)
- **geoclic_demandes ParametresView.vue** : onglets Personnalisation et Email supprimés, info box redirigeant vers GéoClic Admin
- **geoclic_data parametres.vue** : 4 onglets (Général, Personnalisation avec logo/couleurs, Email SMTP, PostGIS)
- **OnboardingWizard déplacé** de geoclic_demandes vers geoclic_data (admin.vue)
- **Branding dynamique** dans tous les modules : nom collectivité, logo, CSS variables (`--primary-color`, `--sidebar-color`)

#### Corrections OnboardingWizard
- **Migration 018** : Corrige FK `system_settings.updated_by` → `geoclic_users` (au lieu de l'ancienne table `users`)
- **API `set_setting()`** : Cast UUID explicite + fallback sans `updated_by` si FK échoue
- **`project_id` manquant** : Le wizard récupère maintenant le projet système via `getSystemProjectId()` avant de créer catégories/services
- **Format couleur** : Conversion hex → entier ARGB via `hexToArgb()` pour les catégories (l'API attend un `int`, pas un `string`)

#### Correction portail citoyen - catégories vides + mauvais nom
- **Problème** : Le portail utilisait `autoDetectProject()` qui appelait `GET /api/sig/projects` (excluant les projets système). Il trouvait un projet SIG ("Mobilier Urbain") et stockait son ID. Les catégories de demandes étant liées au projet système "Signalements Citoyens", le filtre par ce mauvais `project_id` retournait 0 résultats.
- **Symptômes** : "Aucune catégorie disponible" + "Mobilier Urbain" au lieu du nom de la ville
- **Solution** : Remplacé `autoDetectProject()` par `api.getSystemProject()` qui cherche le projet avec `is_system=true`. Le nom de la collectivité vient du branding et n'est plus écrasé.
- **Fichiers modifiés** : `portail_citoyen/src/stores/config.ts`, `portail_citoyen/src/services/api.ts`

### Phase 14 ter : Compatibilité geoclic_data ↔ geoclic_mobile_pwa (TERMINÉ - février 2026)

#### Sync photos + champs hérités
- **Photos.py - CAST UUID manquant:**
  - `WHERE id = :id` → `WHERE id = CAST(:id AS uuid)` pour geoclic_staging
  - JSONB natif: asyncpg retourne des objets Python (list/dict), pas des strings JSON. Ajout `isinstance` checks
  - Rollback + logging sur erreurs
- **Champs.py - InFailedSQLTransactionError:**
  - La colonne `project_id` n'existait pas dans `type_field_configs` sur le serveur
  - Chaque appel API échouait → rollback → fallback. Après 3 appels récursifs (POUB_SIMPLE → PROPRETE → MOBILIER), la session DB devenait instable et les champs hérités ne se chargeaient pas
  - **Migration 022:** Ajoute `project_id UUID` + FK + peuple les champs existants depuis le lexique
  - **champs.py nettoyé:** Suppression de tous les try/except fallback (50 lignes en moins)
  - **sync.py:** Amélioration logging (logger au lieu de print)
- **Upload photos mobile:**
  - `GeometryFormView.vue` et `PointFormView.vue`: implémentation du flux d'upload avec alertes utilisateur
  - Endpoint corrigé: `/photos/upload` avec `point_id` en FormData

#### UX mobile - Vocabulaire agent terrain
- **Problème:** Les statuts "Brouillon" et "En attente" sont des termes admin/data incompréhensibles pour l'agent terrain
- **PointsView.vue:**
  - `draft`/`pending` → **"Envoyé ✓"** (badge bleu)
  - `validated` → **"Validé ✓✓"** (badge vert)
  - `rejected` → **"Rejeté ✗"** (badge rouge)
  - "À sync" → **"À envoyer"**
- **SyncView.vue:**
  - "Points en attente" → **"Points à envoyer"**
  - "Photos en attente" → **"Photos à envoyer"**
  - Résultats: **"Tous vos points sont à jour"** ou **"X point(s) envoyé(s) au serveur"**
  - Ajout: **"Total sur le serveur : X point(s)"**

#### CI Pipeline - package-lock.json manquants
- 4 apps n'avaient pas de `package-lock.json` → `npm ci` échouait en CI
- Généré pour: geoclic_demandes, geoclic_services, geoclic_services_pwa, portail_citoyen

### Phase 15 : Améliorations UX geoclic_data & SIG (EN COURS - février 2026)

#### Corrections auth zones.py
- **Problème:** DELETE /api/zones/ retournait 403 Forbidden
- **Cause:** `zones.py` utilisait l'ancien pattern `current_user.get("role") not in ["admin", "moderator"]`
- **Solution:** 4 occurrences remplacées par `not current_user.get("is_super_admin") and current_user.get("role_data") != "admin"`

#### Carte admin - Données points et visibilité marqueurs
- **Problème 1:** Perte de données entre l'onglet Points (modal édition) et le panneau carte
  - `mapPointFromBackend()` dans `api.ts` ne mappait pas `custom_properties`, `icon_name`, `color_value`
  - Fix: mapping complet `custom_properties→donnees_techniques`, `icon_name→icone`, `color_value (int ARGB)→couleur (hex string)`
- **Problème 2:** Marqueur quasi invisible sur la carte
  - `L.divIcon` sans `iconSize`/`iconAnchor` → Leaflet clip à 12x12 par défaut
  - Fix: `iconSize: [36, 36]`, `iconAnchor: [18, 36]`, bordure blanche, ombre renforcée
- **Ajouts dans le panneau détail carte:**
  - Infos classification : Famille, Catégorie, Type (chip), Projet
  - Couleur réelle des données techniques (swatch `.color-swatch`)
  - Fonction `getPointHierarchy()` remonte la hiérarchie lexique depuis `parent_id`

#### Filtres catégorie - LIKE → IN pour hiérarchie
- **Problème:** Filtrer par "Propreté" (niveau 1) retournait 0 résultats malgré un point "Poubelle simple" (niveau 2)
- **Cause:** Backend utilisait `WHERE lexique_code LIKE 'PROPRETE%'` mais les codes enfants ne sont pas préfixés par le parent
- **Solution backend (points.py):** LIKE remplacé par `=` (single) ou `IN` (comma-separated) dans 4 endpoints
- **Solution frontend (points.ts):** `getDescendantCodes()` résout récursivement tous les codes enfants depuis la hiérarchie lexique
- **Bug supplémentaire (carte.vue):** Envoyait l'UUID (`item-value="id"`) au lieu du code (`item-value="code"`)

#### Filtres cascade dynamiques (remplace single dropdown)
- **Avant:** Un seul dropdown avec tous les niveaux indentés → inutilisable avec beaucoup de catégories
- **Après:** Cascade de N dropdowns qui s'adaptent à la profondeur réelle du lexique
  - Noms des niveaux: `['Famille', 'Type', 'Sous-type', 'Variante', 'Détail', 'Précision']`
  - `activeLevels` computed: détecte les niveaux présents dans les données (Set des `niveau`)
  - `cascadeOptions(level)`: retourne les entrées du niveau N dont le `parent_id` = sélection du niveau N-1
  - `onCascadeChange(level)`: vide tous les niveaux en dessous
  - Le filtre Projet est caché automatiquement quand il n'y a qu'un seul projet (`v-if="projets.length > 1"`)
- **Appliqué sur:** `points.vue`, `carte.vue`, `MapView.vue` (SIG)
- **Fichiers modifiés:** 3 pages frontend + `points.ts` store + `points.py` backend

#### Filtres données techniques contextuels (Option C)
- **Concept:** Quand une catégorie est sélectionnée dans la cascade, charger ses champs dynamiques (`type_field_configs`) et afficher un dropdown par champ de type `select`
- **Backend (points.py):** Nouveau param `custom_filters` (JSON) → filtre JSONB via opérateur `@>` (paramétrisé, pas d'injection SQL)
  ```python
  custom_properties @> CAST(:cf_0 AS jsonb)  -- Ex: '{"Matériau": "Bois"}'
  ```
- **Store (points.ts):** `custom_filters: Record<string, string>` dans les filtres, sérialisé en JSON pour l'API
- **Frontend (points.vue & carte.vue):**
  - `loadedChamps`: chargés via `champsAPI.getByLexique()` pour la catégorie sélectionnée + tous ses parents (héritage)
  - `selectChamps` computed: filtre sur `type === 'select' || type === 'multiselect'`
  - 2e ligne de filtres "Données techniques :" avec `v-autocomplete` par champ
  - `watch(activeFilterCode)` déclenche le chargement des champs quand la cascade change

#### SIG Web - Recherche geocoding + amélioration features
- **Barre de recherche** dans la toolbar : Nominatim (adresses France) + recherche locale dans les features chargées
  - Debounce 300ms, résultats groupés (éléments locaux + adresses)
  - Clic sur résultat → zoom + sélection (feature) ou marqueur temporaire (adresse)
- **Filtres cascade → rendu carte** : les filtres cascade affectent maintenant le rendu Leaflet (pas juste la liste)
  - Watch sur `filteredLayers` déclenche `renderLayers()`
  - `renderLayers()` utilise `filteredLayers` au lieu de `mapStore.layers`
- **custom_properties** affichées dans le détail feature (section "Données techniques")

#### SIG Web - Multi-projets + Tableau de bord cockpit
- **Multi-projets (superposition de couches):**
  - Cases à cocher au lieu de sélection unique dans le panneau Projets
  - `activeProjectIds: Set<string>` dans le store, `toggleProject()`, `isProjectActive()`
  - Layer IDs préfixés `${projectId}_${code}` pour éviter les collisions
  - Lexique fusionne entre projets (merge dans la Map, pas remplacement)
  - Features portent `_project_id` et `_project_name` dans leurs properties
  - `addProjectLayers()` ajoute sans effacer les couches des autres projets
- **Tableau de bord 3 onglets** (panneau droit, remplace l'ancien stats-panel + feature-panel) :
  - **Onglet Stats (Cockpit patrimoine) :**
    - KPI globaux : total éléments, couches, projets actifs
    - Inventaire : points/lignes/zones avec icônes
    - Linéaire total et surface totale via Turf.js (`turf.length()`, `turf.area()`)
    - Donut CSS (`conic-gradient`) pour la distribution `condition_state` (Neuf/Bon/Moyen/À rénover/Critique)
    - Barres horizontales par catégorie (répartition du patrimoine)
    - Répartition par projet (si multi-projets actifs)
  - **Onglet Propriétés :**
    - Carte header avec couleur catégorie + hiérarchie
    - Propriétés standard + données techniques + photos
    - Boutons : Centrer, Modifier, Supprimer
    - S'ouvre automatiquement quand on clique sur un élément (watch sur `selectedFeature`)
  - **Onglet Export :**
    - CSV (Excel-compatible, UTF-8 BOM, colonnes : Nom/Catégorie/Type/État/Statut/Commentaire/Projet/Géométrie/Lat/Lng)
    - GeoJSON standard
    - GeoJSON + métadonnées (source, date, comptage)
    - Résumé du contenu par catégorie
- **Fix cascade filtre** : `filteredLayers` utilisait `layer.id` pour le lookup lexique, mais le nouveau format `${projectId}_${code}` cassait le filtre. Ajout de `getLayerLexiqueCode()` pour extraire le code.
- **Aperçu couleur dans propriétés** : Les valeurs hexadécimales (#RGB, #RRGGBB, #RRGGBBAA) dans les données techniques s'affichent avec un carré coloré au lieu du code brut. Fonction `isColorValue()` + template conditionnel avec `.color-swatch`.
- **Fichiers modifiés :** `geoclic_sig_web/src/stores/map.ts`, `geoclic_sig_web/src/views/MapView.vue`

### Autres tâches en attente
- Merger vers main après validation
- Configurer renouvellement auto certificats SSL
- Phase 15 (Scale) - après premiers clients payants
- Finaliser site commercial marketing (responsive, mentions légales, formulaire contact)
- Ajouter images visuels (sig-patrimoine.png, terrain-sync.png, dashboard.png) dans le repo git

## Technologies

- **Frontend:** Vue 3 + TypeScript + Pinia + Vite
- **Backend:** FastAPI + SQLAlchemy (async)
- **Base de données:** PostgreSQL 15 + PostGIS 3.3
- **Déploiement:** Docker + docker-compose 1.29.2
- **Reverse proxy:** Nginx avec SSL

## Problèmes Connus et Solutions

### Nginx ne démarre pas après un rebuild
**Symptôme:** Site inaccessible (ERR_CONNECTION_REFUSED) après `docker-compose up -d --build`

**Cause:** Quand on rebuild uniquement certains services (api, portail, demandes), nginx et les autres services dépendants ne sont pas démarrés automatiquement.

**Solution:**
```bash
# Vérifier l'état des conteneurs
cd /opt/geoclic/deploy && sudo docker-compose ps

# Si nginx n'apparaît pas, le démarrer
sudo docker-compose up -d nginx

# Ou relancer tous les services
sudo docker-compose up -d
```

**Prévention:** Toujours utiliser `sudo docker-compose up -d` (sans --build pour les services spécifiques) ou démarrer explicitement nginx après un rebuild partiel.

### Erreur KeyError: 'ContainerConfig' lors du rebuild
**Symptôme:** Erreur lors de `docker-compose up -d --build`:
```
KeyError: 'ContainerConfig'
```

**Cause:** Cache Docker corrompu ou conteneurs orphelins avec docker-compose 1.29.2.

**Solution:**
```bash
# Arrêter tous les conteneurs
cd /opt/geoclic/deploy && sudo docker-compose down

# Nettoyer les conteneurs orphelins
sudo docker container prune -f

# Reconstruire proprement
sudo docker-compose up -d --build api portail demandes

# Démarrer tous les services
sudo docker-compose up -d
```

**Alternative si le problème persiste:**
```bash
# Supprimer aussi les images problématiques
sudo docker-compose down --rmi local
sudo docker-compose up -d --build
```

### Commande de déploiement complète recommandée
```bash
cd /opt/geoclic/deploy && sudo docker-compose down && sudo docker container prune -f
cd /opt/geoclic && sudo git pull origin claude/hierarchical-zones-S5XGp
sudo docker exec -i geoclic_db psql -U geoclic -d geoclic_db < /opt/geoclic/database/migrations/NOM_MIGRATION.sql
cd /opt/geoclic/deploy && sudo docker-compose build --no-cache api portail demandes && sudo docker-compose up -d
sudo docker-compose ps
```

### FastAPI route ordering - routes paramétrées
**Symptôme:** Erreur 500 `invalid UUID 'services'` sur `/api/demandes/services`

**Cause:** Dans FastAPI, les routes sont matchées dans l'ordre de définition. Si `/{demande_id}` est défini avant `/services`, alors `/services` est capturé comme un `demande_id`.

**Solution:** Toujours définir les routes statiques (`/services`, `/categories`, `/stats`, etc.) AVANT les routes paramétrées (`/{id}`, `/{demande_id}`).

**Exemple dans demandes.py:**
```python
# ✅ Correct - routes statiques en premier
@router.get("/services")
async def list_services(): ...

@router.get("/services/{service_id}")
async def get_service(): ...

# Après toutes les routes statiques
@router.get("/{demande_id}")
async def get_demande(): ...
```

### PWA Terrain - Cache navigateur persistant
**Symptôme:** Nouvelles fonctionnalités non visibles après déploiement (fonctionne en navigation privée)

**Cause:** Le Service Worker met en cache les fichiers JS/CSS avec stratégie cache-first.

**Solution:**
1. Incrémenter `CACHE_NAME` dans `geoclic_services_pwa/public/sw.js` (ex: `v2` → `v3`)
2. Redéployer le conteneur terrain
3. Utilisateurs: vider le cache navigateur ou DevTools → Application → "Clear site data"

### Portail Citoyen - Erreur 404 sur fichiers JS après déploiement
**Symptôme:** Erreur 404 sur des fichiers comme `SignalerView-CKLhdxye.js` après rebuild

**Cause:** Le Service Worker cache les fichiers JS avec leurs hashes. Après un rebuild, les hashes changent mais le cache garde les anciens noms.

**Solution appliquée (sw.js v2):**
- Network-first pour HTML (toujours le HTML frais avec les bons hashes)
- Network-first pour JS/CSS (mise à jour immédiate)
- Cache-first uniquement pour images/fonts
- Index.html retiré du precache (il référence des fichiers hashés)

**Si le problème persiste:**
1. Incrémenter `CACHE_NAME` dans `portail_citoyen/public/sw.js`
2. Rebuild avec `--no-cache`
3. Côté utilisateur: DevTools → Application → Service Workers → Unregister + Clear site data

### geoclic_services - Super admin voit tous les agents
**Symptôme:** Dans la liste des agents, un super_admin voit les agents de TOUS les services

**Cause:** C'est le comportement prévu. Le super_admin a une vue globale de tous les services.

**Solution:** Pour voir uniquement les agents d'un service spécifique, se connecter avec un compte responsable de ce service (pas le super_admin).

### geoclic_terrain - PWA vide (aucune demande)
**Symptôme:** La PWA terrain n'affiche aucune demande malgré des demandes assignées

**Cause:** Incompatibilité d'IDs entre `geoclic_users.id` (auth unifiée) et `demandes_services_agents.id` (table legacy). Le filtre `my_demandes=true` comparait les mauvais IDs.

**Solution appliquée:**
- Dans `services.py`, le filtre `my_demandes` recherche maintenant l'ID `demandes_services_agents` correspondant par email avant de filtrer
- Code: `SELECT id FROM demandes_services_agents WHERE email = :email`

### geoclic_services - Menu "Agents" invisible
**Symptôme:** Le lien "Agents" n'apparaît pas dans la navigation même pour un responsable de service

**Cause:** La condition `agent?.role === 'responsable'` échouait car le rôle n'était pas correctement calculé avec l'auth unifiée.

**Solution appliquée:**
- API: Calcul du rôle = `'responsable'` si `is_super_admin` OU `role_demandes === 'admin'`
- Frontend: Ajout de la fonction `computeRole()` dans le store auth.ts

### geoclic_demandes - Erreur 500 sur changement de priorité
**Symptôme:** Erreur 500 lors du changement de priorité d'une demande

**Cause:**
1. UUID non casté dans l'INSERT de `demandes_historique`
2. FK `demandes_historique.agent_id` référençait l'ancienne table `users` au lieu de `geoclic_users`

**Solution:**
- Fix UUID casting: `CAST(:agent_id AS uuid)`
- Migration 016: modifie la FK pour référencer `geoclic_users`

### Création d'agent - Agent ne peut pas se connecter à geoclic_services
**Symptôme:** Un agent créé via geoclic_demandes ne peut pas se connecter à geoclic_services (401)

**Cause:** L'agent était créé uniquement dans `demandes_services_agents` mais pas dans `geoclic_users` (table de l'auth unifiée).

**Solution appliquée:**
- Création d'agent (demandes.py et services.py): insère dans les DEUX tables
- Migration 017: synchronise les agents existants vers `geoclic_users`

### geoclic_data - Erreur 500 sur création de projet ou autres actions
**Symptôme:** Erreur 500 sur POST /api/projects, PATCH /api/lexique, etc. dans geoclic_data (admin)

**Cause:** Les routers API (projects.py, lexique.py, champs.py, etc.) utilisaient `current_user["role"]` mais le nouveau système d'authentification unifiée ne retourne plus ce champ. Il retourne maintenant `role_data`, `role_demandes`, `role_sig`, `role_terrain`.

**Solution appliquée:**
- Remplacer toutes les occurrences de `current_user["role"]` par le nouveau pattern :
  ```python
  # Avant
  if current_user["role"] != "admin":

  # Après
  if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
  ```
- Fichiers corrigés: projects.py, champs.py, imports.py, lexique.py, ogs.py, points.py, postgis.py, users.py

### geoclic_mobile_pwa - Erreur 404 sur /api/auth/token
**Symptôme:** Erreur "Not Found" lors de la connexion sur geoclic_mobile_pwa

**Cause:** L'application mobile utilisait l'ancien endpoint `/api/auth/token` mais le système d'authentification unifiée utilise `/api/auth/login`.

**Solution appliquée:**
- Dans `geoclic_mobile_pwa/src/services/api.ts`, changer l'endpoint de login:
  ```typescript
  // Avant
  const response = await this.api.post<LoginResponse>('/auth/token', formData, ...)

  // Après
  const response = await this.api.post<LoginResponse>('/auth/login', formData, ...)
  ```

### geoclic_mobile_pwa - Icônes affichées en texte brut
**Symptôme:** Dans le sélecteur de catégories, les icônes affichent du texte comme "mdi-", "ent", "delete" au lieu d'icônes

**Cause:** Le composant `LexiqueSelector.vue` affichait `item.icon_name` (ex: "mdi-bench") directement, mais la PWA mobile n'a pas la bibliothèque Material Design Icons.

**Solution appliquée:**
- Dans `LexiqueSelector.vue`, remplacer l'affichage de l'icône MDI par un cercle coloré avec la première lettre:
  ```html
  <!-- Avant -->
  <span v-if="item.icon_name" class="item-icon">{{ item.icon_name }}</span>

  <!-- Après -->
  <span class="item-icon" :style="{ background: item.color_value || '#1976D2' }">
    {{ item.label.charAt(0).toUpperCase() }}
  </span>
  ```

### system_settings - Erreur 500 sur sauvegarde paramètres
**Symptôme:** Erreur 500 sur `PUT /api/settings/general` ou lors de l'upload logo

**Cause:** La table `system_settings` avait une FK `updated_by REFERENCES users(id)` pointant vers l'ancienne table `users` au lieu de `geoclic_users`. Quand l'API envoyait un `geoclic_users.id`, la contrainte FK échouait.

**Solution appliquée:**
- Migration 018: Supprime l'ancienne FK et la recrée vers `geoclic_users`
- API `set_setting()`: Fallback qui sauvegarde sans `updated_by` si la FK échoue (résilience)

### Portail citoyen - "Aucune catégorie disponible" + "Mobilier Urbain"
**Symptôme:** Le portail affiche "Aucune catégorie disponible" et le header montre "Mobilier Urbain" au lieu du nom de la ville

**Cause:** `autoDetectProject()` appelait `GET /api/sig/projects` qui exclut les projets système par défaut. Il trouvait un projet SIG (ex: "Mobilier Urbain"), stockait son ID dans `localStorage`, et filtrait les catégories par ce mauvais `project_id`. Les catégories de demandes sont liées au projet système "Signalements Citoyens" → 0 résultats. Le nom du projet écrasait aussi le `collectiviteName` du branding.

**Solution appliquée:**
- `autoDetectProject()` remplacé par `api.getSystemProject()` qui cherche `is_system=true`
- Le nom de la collectivité vient uniquement du branding (plus d'écrasement)
- Si problème persiste côté client: `localStorage.removeItem('portail_project_id')` + F5

### OnboardingWizard - 422 sur création catégories/services
**Symptôme:** Toutes les catégories et services échouent avec erreur 422 lors du wizard d'onboarding

**Cause:**
1. Le `project_id` (query param requis) n'était pas envoyé
2. Le champ `couleur` des catégories était envoyé en hex string (`"#795548"`) alors que l'API attend un entier ARGB

**Solution appliquée:**
- Ajout de `getSystemProjectId()` pour récupérer le projet système avant création
- Ajout de `hexToArgb()` pour convertir les couleurs hex en entier ARGB
- `project_id` passé en `params` dans chaque appel axios

### geoclic_mobile_pwa - Service Worker 404 sur /sw.js
**Symptôme:** Erreur "Failed to register ServiceWorker" avec 404 sur `https://geoclic.fr/sw.js`

**Cause:** Ancien Service Worker en cache qui cherche le fichier à la racine au lieu de `/mobile/sw.js`.

**Solution:**
1. Dans DevTools → Application → Service Workers → Cliquer sur "Annuler l'enregistrement" pour chaque SW
2. Ou DevTools → Application → Stockage → "Effacer les données du site"
3. Rafraîchir la page (F5)

### geoclic_demandes - Formulaire se soumet sur Enter
**Symptôme:** En créant/éditant une demande depuis le back-office, appuyer sur Enter dans n'importe quel champ soumet le formulaire avec des données incomplètes (pas de carte, pas de fichiers)

**Cause:** Utilisation de `<form @submit.prevent>` qui intercepte Enter sur tous les `<input>` à l'intérieur

**Solution appliquée:**
- Remplacer `<form>` par `<div class="form-container">` dans `CreerDemandeView.vue` et `ModifierDemandeView.vue`
- Changer le bouton de soumission en `type="button" @click="confirmSubmit"`

### geoclic_demandes - Fichiers disparaissent en mode édition
**Symptôme:** En éditant une demande, les fichiers existants ne s'affichent pas dans FileDropZone

**Cause:** Les fichiers arrivent de l'API de manière asynchrone après le montage du composant. Sans `watch` sur la prop `initialFiles`, les fichiers ne sont jamais copiés dans l'état local.

**Solution appliquée:**
- Ajout de `watch(() => props.initialFiles, ...)` avec `{ deep: true }` dans `FileDropZone.vue`
- Si les nouveaux fichiers arrivent et que l'état local est vide, copie les fichiers

### geoclic_demandes - Page détail demande blanche
**Symptôme:** La page de détail d'une demande est complètement vide (blanche)

**Cause:** `Promise.all` dans le store `demandes.ts` - si l'appel historique échoue (500), tout le `Promise.all` échoue et `currentDemande` n'est jamais assigné

**Solution appliquée:**
- Remplacer `Promise.all` par `Promise.allSettled` dans `fetchDemande()`
- Traiter chaque résultat individuellement : si historique échoue, afficher un tableau vide mais la demande reste visible

### geoclic_demandes - "lightbulb" ou nom icône au lieu de l'emoji
**Symptôme:** Le détail demande affiche "lightbulb" en texte au lieu d'une icône

**Cause:** Le champ `categorie_icone` contient des noms Material Icons (ex: "lightbulb", "park") mais geoclic_demandes n'inclut pas la bibliothèque MDI

**Solution appliquée:**
- Mapping `iconToEmoji` dans `DemandeDetailView.vue` convertissant ~30 noms courants en emojis
- Fonction `getIconEmoji()` avec fallback `📌` si nom inconnu

### geoclic_mobile_pwa - POST /api/points retourne 500
**Symptôme:** L'enregistrement de points échoue avec erreur 500

**Causes (3 niveaux) :**
1. Auth: `check_user_permissions()` utilisait l'ancien `current_user["role"]` au lieu du système unifié
2. FK: `geoclic_staging.created_by` pointait vers l'ancienne table `users` au lieu de `geoclic_users`
3. UUID: Paramètres `project_id` et `created_by` non castés en UUID dans l'INSERT

**Solutions appliquées:**
- `points.py`: Pattern `is_super_admin or role_data == "admin"` + `CAST(:param AS uuid)`
- Migration 019: Recrée les FK de `geoclic_staging` vers `geoclic_users`
- **Important:** La migration 019 doit être exécutée manuellement sur le serveur

### geoclic_mobile_pwa - Manifest/SW erreurs empêchant installation PWA
**Symptôme:** `manifest.webmanifest` Syntax Error + `sw.js` 404 dans la console

**Cause:** Les chemins dans `index.html` n'avaient pas le préfixe `/mobile/`. Le navigateur cherchait `/manifest.webmanifest` au lieu de `/mobile/manifest.webmanifest`, et nginx retournait du HTML (page d'accueil) au lieu du JSON.

**Solution appliquée:**
- `index.html`: Tous les chemins préfixés avec `/mobile/` (manifest, icon, apple-touch-icon)
- `main.ts`: Suppression de l'enregistrement manuel du SW (VitePWA avec `registerType: 'autoUpdate'` gère tout automatiquement)
- Les erreurs empêchaient l'installation PWA mais n'impactaient pas le fonctionnement de l'app

### zones.py - 403 Forbidden sur suppression de zone
**Symptôme:** DELETE /api/zones/ retourne 403

**Cause:** `zones.py` utilisait l'ancien pattern `current_user.get("role") not in ["admin", "moderator"]` au lieu du système d'auth unifié.

**Solution appliquée:** 4 occurrences remplacées par `not current_user.get("is_super_admin") and current_user.get("role_data") != "admin"`

### geoclic_data Carte - Données manquantes dans le panneau point
**Symptôme:** Le panneau latéral carte affiche "Aucune description", "Aucune donnée technique" malgré des données existantes

**Cause:** `mapPointFromBackend()` dans `api.ts` ne mappait que `name→nom`, `comment→description`, `project_id→projet_id`. Il manquait `custom_properties→donnees_techniques`, `icon_name→icone`, `color_value→couleur`.

**Solution appliquée:** Mapping complet ajouté dans `mapPointFromBackend()` avec conversion `color_value` (int ARGB) → couleur (hex string via `& 0xFFFFFF`).

### geoclic_data - Filtre catégorie retourne 0 résultats
**Symptôme:** Sélectionner "Propreté" dans les filtres retourne 0 points malgré un point "Poubelle simple" existant

**Cause:** Le backend utilisait `LIKE 'PROPRETE%'` mais les codes enfants (POUB_SIMPLE) ne sont pas préfixés par le code parent.

**Solution appliquée:**
- Backend `points.py`: LIKE remplacé par `=` (code unique) ou `IN` (codes multiples séparés par virgule) dans 4 endpoints
- Frontend `points.ts`: `getDescendantCodes()` résout récursivement tous les codes enfants et les envoie séparés par virgule

## Notes Importantes

- Les photos sont stockées dans le volume `geoclic_photos_data`
- Les migrations sont dans `/database/migrations/`
- Toujours utiliser `COALESCE(d.est_doublon, FALSE)` car la colonne peut être NULL
- **UUID casting obligatoire** dans les requêtes SQL avec paramètres: `CAST(:id AS uuid)`
- **Projet système**: Le projet "Signalements Citoyens" (is_system=TRUE) est créé automatiquement par la migration 013. Il ne peut pas être supprimé ou désactivé (protégé par triggers SQL et API). geoclic_demandes l'utilise automatiquement sans afficher de sélecteur de projet.
- **bcrypt/passlib compatibilité**: Utiliser `bcrypt==4.0.1` (fixé dans requirements.txt) pour éviter l'erreur "password cannot be longer than 72 bytes"
- **Table geoclic_users**: Remplace l'ancienne table `users`. Les requêtes doivent utiliser `geoclic_users` et les champs `actif`, `prenom`, `nom` (pas `is_active`, `name`)
- **Double table agents**: Les agents terrain existent dans DEUX tables:
  - `demandes_services_agents`: table legacy utilisée pour les assignations de demandes (`d.agent_service_id`)
  - `geoclic_users`: table unifiée utilisée pour l'authentification
  - La création/modification d'agents doit synchroniser les DEUX tables
  - Le filtre `my_demandes` doit chercher l'ID par email pour faire le lien
- **Colonne date_planification**: Stocke la date/heure d'intervention planifiée dans `demandes_citoyens`
- **Paramètres centralisés dans geoclic_data**: Seul geoclic_data écrit les paramètres (branding, email, logo). Tous les autres modules lisent via `GET /api/settings/branding` (endpoint public sans auth). Ne pas remettre d'écriture de paramètres dans les autres modules.
- **Portail citoyen et projet système**: Le portail doit utiliser `api.getSystemProject()` (avec `include_system=true`) pour trouver le projet "Signalements Citoyens". Ne jamais utiliser `api.getProjects()` (qui exclut les projets système) pour détecter le projet des demandes.
- **Couleur catégories**: L'API `POST /api/demandes/categories` attend `couleur` en **entier ARGB** (ex: `4286265624`), pas en hex string. Utiliser `hexToArgb()` pour convertir.
- **Promise.allSettled obligatoire**: Quand on charge plusieurs données API en parallèle pour une page, toujours utiliser `Promise.allSettled` au lieu de `Promise.all`. Si un appel échoue, la page doit quand même fonctionner avec les données disponibles.
- **Formulaires back-office sans `<form>`**: Ne pas utiliser `<form>` dans les vues de création/édition complexes (avec carte, fichiers). Utiliser `<div>` + `type="button"` pour éviter la soumission accidentelle sur Enter.
- **PWA base path**: Quand une app est servie sous un sous-chemin (ex: `/mobile/`), tous les chemins dans `index.html` (manifest, icons, apple-touch-icon) doivent inclure ce préfixe. VitePWA gère l'enregistrement du SW automatiquement avec `registerType: 'autoUpdate'` — ne pas enregistrer manuellement.
- **FK vers geoclic_users**: Toute table avec des colonnes `created_by`, `updated_by`, `validated_by` doit avoir ses FK pointant vers `geoclic_users` (pas l'ancienne table `users`). Tables déjà migrées: `demandes_historique` (016), `system_settings` (018), `geoclic_staging` (019).
- **type_field_configs.project_id**: La colonne existe depuis la migration 022. Ne plus utiliser de try/except fallback dans `champs.py`. Les requêtes incluent directement `project_id` dans le SELECT/INSERT.
- **Champs hérités (mobile)**: Les champs dynamiques sont hérités via la hiérarchie lexique (`parent_code`). Le mobile charge récursivement les champs de chaque parent. Ex: POUB_SIMPLE (1 champ) hérite de PROPRETE (0) qui hérite de MOBILIER (7) = 8 champs au total.
- **JSONB asyncpg**: PostgreSQL JSONB retourne des objets Python natifs (list/dict) via asyncpg, PAS des strings JSON. Ne jamais utiliser `json.loads()` directement — toujours vérifier `isinstance(value, (list, dict))` avant.
- **Statuts sync_status dans geoclic_mobile_pwa**: L'agent terrain voit "Envoyé ✓" (draft/pending), "Validé ✓✓" (validated), "Rejeté ✗" (rejected). Ne pas afficher les termes internes (draft, brouillon, pending).
- **Cache PWA après déploiement**: Après un rebuild d'une app frontend, les utilisateurs doivent vider le cache (DevTools > Application > Effacer données du site) ou ouvrir en navigation privée pour voir les changements.
- **Lexique codes non hiérarchiques**: Les codes lexique (POUB_SIMPLE, BANC_BOIS) ne sont PAS préfixés par le code parent (PROPRETE, ASSISE). Ne jamais utiliser `LIKE 'PARENT%'` pour filtrer les enfants. Utiliser `getDescendantCodes()` côté frontend (résolution récursive depuis `parent_id`) puis envoyer les codes en `IN (...)` côté backend.
- **mapPointFromBackend() complet**: Le mapping dans `api.ts` doit mapper TOUS les champs : `name→nom`, `comment→description`, `project_id→projet_id`, `lexique_code→lexique_id`, `custom_properties→donnees_techniques`, `icon_name→icone`, `color_value (int ARGB)→couleur (hex '#RRGGBB')`. Oublier un champ = données invisibles dans la carte.
- **Leaflet DivIcon sizing obligatoire**: Toujours spécifier `iconSize` et `iconAnchor` sur `L.divIcon`. Sans ça, Leaflet utilise 12x12 par défaut et clipe les icônes plus grandes.
- **Filtres cascade dynamiques**: Les dropdowns de filtre lexique se génèrent automatiquement selon les niveaux présents dans les données (`activeLevels` = Set des `niveau`). Ne pas coder en dur les niveaux 0/1/2. Le filtre Projet est masqué automatiquement quand il n'y a qu'un seul projet.
- **Filtres données techniques**: Le param API `custom_filters` accepte du JSON (`{"Matériau":"Bois"}`). Le backend utilise l'opérateur JSONB `@>` avec `CAST(:param AS jsonb)` — entièrement paramétrisé, aucune injection possible. Les champs disponibles viennent de `type_field_configs` via `champsAPI.getByLexique()`, avec héritage des parents.
- **Héritage champs dynamiques (filtres)**: Quand une catégorie est sélectionnée, charger ses champs ET ceux de tous ses parents (`parent_id` chain). Ex: POUB_SIMPLE hérite des champs de PROPRETE et MOBILIER.
- **SIG multi-projets (layer IDs)**: Les couches du SIG ont des IDs au format `${projectId}_${code}`. Pour extraire le code lexique d'une couche, utiliser `getLayerLexiqueCode(layer)` qui strip le préfixe projectId. Ne jamais comparer `layer.id` directement avec un code lexique.
- **SIG lexiqueMap merge**: Quand plusieurs projets sont chargés, le `lexiqueMap` fusionne les entrées de tous les projets. `loadLexique()` crée une nouvelle Map à partir de l'existante et y ajoute les nouvelles entrées (pas de remplacement). Cela permet aux filtres cascade de fonctionner avec des données multi-projets.
- **SIG features _project_id/_project_name**: Chaque feature GeoJSON du SIG porte `_project_id` et `_project_name` dans ses properties. Ces champs sont dans `HIDDEN_PROPERTIES` (pas affichés au détail) mais utilisés par les stats (répartition par projet) et l'export CSV.
- **SIG Turf.js**: La dépendance `@turf/turf` est installée dans geoclic_sig_web. Utilisée pour calculer le linéaire total (`turf.length()` en mètres) et la surface totale (`turf.area()` en m²) dans le cockpit Stats.
- **SIG dashboard panel**: Le panneau droit du SIG est un composant unique avec 3 onglets (Stats/Propriétés/Export) géré par `dashboardTab` ref. Le watch sur `selectedFeature` ouvre automatiquement l'onglet Propriétés. Pas de panneaux séparés stats-panel/feature-panel. Le panneau s'ouvre par défaut (`showStatsPanel = ref(true)`).
- **SIG aperçu couleurs**: Les valeurs hex (#RGB, #RRGGBB, #RRGGBBAA) dans les données techniques (custom_properties) sont détectées par `isColorValue()` et affichées avec un carré coloré `.color-swatch` au lieu du code brut. Le type de retour de `getCustomProperties()` inclut un flag `isColor: boolean`.

## Liste des Migrations

| N° | Fichier | Description |
|----|---------|-------------|
| 005 | `005_categories_hierarchiques.sql` | Catégories parent/enfants |
| 006 | `006_doublons_detection.sql` | Détection doublons |
| 007 | `007_services_municipaux.sql` | Services et agents |
| 008 | `008_geoclic_services.sql` | Tchat et auth agents terrain |
| 010 | `010_add_commentaire_interne.sql` | Colonne notes internes |
| 011 | `011_email_settings.sql` | Logs email et rappels planifiés |
| 013 | `013_system_project.sql` | Projet système pour Demandes (non supprimable) |
| 014 | `014_zones_hierarchiques.sql` | Zones hiérarchiques (Commune > Quartier > Secteur) |
| 015 | `015_geoclic_users.sql` | Table utilisateurs unifiée avec rôles par application |
| 016 | `016_fix_historique_fk.sql` | Corrige FK demandes_historique → geoclic_users |
| 017 | `017_sync_agents_to_geoclic_users.sql` | Synchronise agents existants vers geoclic_users |
| 018 | `018_fix_system_settings_fk.sql` | Corrige FK system_settings.updated_by → geoclic_users |
| 019 | `019_fix_geoclic_staging_fk.sql` | Corrige FK geoclic_staging (created_by, updated_by, validated_by) → geoclic_users |
| 022 | `022_apply_project_id_type_field_configs.sql` | Ajoute project_id à type_field_configs + peuple depuis lexique |

---

## Scripts de Production

**Documentation complète:** `docs/GUIDE_PRODUCTION.md`

### Scripts disponibles

| Script | Usage | Fréquence |
|--------|-------|-----------|
| `scripts/backup_db.sh` | Sauvegarde de la base de données | Cron: tous les jours à 2h |
| `scripts/restore_db.sh` | Restauration d'une sauvegarde | Manuel uniquement |
| `scripts/monitor.sh` | Vérification de l'état du système | Cron: toutes les 5 minutes |

### Commandes rapides

```bash
# Vérifier que tout fonctionne
sudo /opt/geoclic/scripts/monitor.sh

# Faire une sauvegarde manuelle
sudo /opt/geoclic/scripts/backup_db.sh

# Voir les sauvegardes disponibles
ls -lh /opt/geoclic/backups/

# Restaurer une sauvegarde (ATTENTION: efface les données actuelles!)
sudo /opt/geoclic/scripts/restore_db.sh geoclic_backup_XXXXXXXX_XXXXXX.sql.gz
```

### Tâches cron configurées

```
# Sauvegarde DB tous les jours à 2h
0 2 * * * /opt/geoclic/scripts/backup_db.sh >> /var/log/geoclic_backup.log 2>&1

# Monitoring toutes les 5 minutes
*/5 * * * * /opt/geoclic/scripts/monitor.sh > /dev/null 2>&1
```

### Certificats SSL

- **Fournisseur:** Let's Encrypt (certbot)
- **Renouvellement:** Automatique (certbot.timer actif)
- **Vérifier:** `sudo certbot certificates`

---

## Tests Automatisés API

### État actuel (février 2026)
- **Tests de santé (test_health.py):** 6 tests PASSENT
- **Tests avec DB (auth, demandes, services):** Non fonctionnels (conflits async, schéma DB différent)
- **Documentation:** Guide utilisateur disponible dans `docs/GUIDE_TESTS_API.md`
- **À corriger plus tard:** Isolation des tests, base de test séparée, noms de colonnes

### Objectif
Les tests automatisés vérifient que l'API fonctionne correctement **avant** de déployer en production. C'est un filet de sécurité qui détecte les erreurs avant qu'elles n'impactent les utilisateurs.

### Structure des tests
```
api/
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Configuration et fixtures partagées
│   ├── test_health.py      # Tests de santé (API opérationnelle)
│   ├── test_auth.py        # Tests d'authentification
│   ├── test_demandes.py    # Tests module demandes
│   └── test_services.py    # Tests module services
├── requirements-test.txt   # Dépendances pour les tests
└── pytest.ini              # Configuration pytest

docs/
└── GUIDE_TESTS_API.md      # Guide utilisateur (non-technique)
```

### Note technique: Connexion DB pour les tests

Le fichier `conftest.py` utilise les identifiants de la base de production:
- Hostname: `db` (réseau Docker interne)
- Mot de passe: `geoclic_secure_password`

Si les tests sont exécutés en dehors de Docker, définir la variable d'environnement:
```bash
export TEST_DATABASE_URL="postgresql+asyncpg://geoclic:geoclic_secure_password@localhost:5432/geoclic_db"
```

### Commandes de test sur le serveur

```bash
# Commande unique (sans entrer dans le conteneur)
cd /opt/geoclic/deploy
sudo docker exec -it geoclic_api pytest -v

# Installer les dépendances (première fois)
sudo docker exec -it geoclic_api pip install -r requirements-test.txt

# Tests de santé uniquement (fonctionnent)
sudo docker exec -it geoclic_api pytest tests/test_health.py -v
```

### Quand lancer les tests ?

| Situation | Commande | Pourquoi |
|-----------|----------|----------|
| Vérification rapide | `pytest tests/test_health.py -v` | Vérifie que l'API répond |
| Avant chaque déploiement | `pytest -v` | Tout tester |
| Debug d'un problème | `pytest -v --tb=long` | Voir les détails des erreurs |

### Interpréter les résultats

```
✅ PASSED  = Le test a réussi (comportement attendu)
❌ FAILED  = Le test a échoué (bug détecté!)
⚠️ SKIPPED = Test ignoré (dépendance manquante)
🔴 ERROR   = Erreur dans le test lui-même
```

→ Si un test échoue, **NE PAS DÉPLOYER**. Corriger d'abord le problème.

### Fichiers de test disponibles

| Fichier | Ce qu'il teste | Nombre de tests |
|---------|----------------|-----------------|
| `test_health.py` | API démarre, endpoints /health | ~6 |
| `test_auth.py` | Login, tokens JWT, protection routes | ~10 |
| `test_demandes.py` | CRUD catégories, demandes, statuts | ~20 |
| `test_services.py` | CRUD services, agents, assignation | ~15 |

### Workaround temporaire: Copier les fichiers de test manuellement

Le Dockerfile ne copie pas automatiquement les fichiers de test. Si les tests ne sont pas trouvés après un rebuild:

```bash
# Copier les fichiers de test dans le conteneur
cd /opt/geoclic
sudo docker cp api/tests/. geoclic_api:/app/tests/
sudo docker cp api/requirements-test.txt geoclic_api:/app/
sudo docker cp api/pytest.ini geoclic_api:/app/

# Vérifier
sudo docker exec geoclic_api ls -la /app/tests/
```

---

## Fleet Manager - Gestion Multi-Serveurs (TERMINÉ - février 2026)

### Description
Outil CLI unifié (`fleet/geoclic-fleet.sh`) pour gérer le déploiement de GéoClic sur plusieurs serveurs clients. Utilise rsync (pas git) pour pousser le code depuis la machine locale vers les serveurs.

### Fichiers principaux
```
fleet/
├── geoclic-fleet.sh       # CLI principal (register, push, deploy, status, ssh, logs)
├── clients.conf           # Registre des serveurs (format pipe-delimited)
└── fleet-config/
    └── docker-compose.tpl # Template docker-compose pour nouveaux clients
```

### Serveurs enregistrés
- **geoclic-prod** : geoclic.fr (51.210.8.158), user: ubuntu, branche: claude/hierarchical-zones-S5XGp
- **Nouveau VPS** : 51.210.8.158, user: ubuntu, Ubuntu 24.10

### Commandes principales
```bash
# Lister les clients
./fleet/geoclic-fleet.sh list

# Pousser le code vers un serveur
./fleet/geoclic-fleet.sh push geoclic-prod

# Déployer (push + rebuild Docker)
./fleet/geoclic-fleet.sh deploy geoclic-prod

# Vérifier l'état
./fleet/geoclic-fleet.sh status geoclic-prod

# Accéder en SSH
./fleet/geoclic-fleet.sh ssh geoclic-prod
```

### Patterns importants
- SSH user: `ubuntu` (pas root) - toujours utiliser sudo
- rsync excludes: `node_modules`, `.git`, `deploy/.env`, `nginx/ssl`, `backups`
- `--rsync-path="sudo rsync"` obligatoire pour écrire dans `/opt/geoclic/`
- Line endings: toujours fixer avec `sed -i 's/\r$//'` après écriture de scripts bash
- Documentation complète: `docs/GUIDE_FLEET.md`

---

## Site Commercial Marketing (EN COURS - février 2026)

### Description
Site vitrine statique pour vendre GéoClic Suite aux collectivités françaises. Servi par nginx sur geoclic.fr. HTML/CSS inline, pas de framework.

### Structure des fichiers
```
marketing/                    # Sources (développement)
├── index.html               # Page d'accueil (landing page)
├── fonctionnalites.html     # Détail des 7 applications
├── comparatif.html          # Comparatif concurrence
└── tarifs.html              # Grille tarifaire

deploy/www/                   # Copie de production (montée par nginx)
├── index.html               # Copie synchro de marketing/
├── fonctionnalites.html
├── comparatif.html
├── tarifs.html
├── style.css
├── screenshots/             # Images du site
│   ├── logo.png             # Logo GéoClic
│   ├── logo_redim.png       # Logo redimensionné (nav)
│   ├── sig-web.png          # Screenshot SIG Web (385K)
│   ├── geoclic-data.png     # Screenshot GéoClic Data (153K)
│   ├── portail.png          # Screenshot portail citoyen (118K)
│   ├── mobile-pwa.png       # Screenshot mobile terrain (42K)
│   ├── demandes.png         # Screenshot back-office demandes (115K)
│   ├── dashboard.png        # Screenshot dashboard KPI (190K) - NOUVEAU
│   ├── sig-patrimoine.png   # Visuel bureau ancien vs GéoClic (109K) - NOUVEAU
│   └── terrain-sync.png     # Visuel sync terrain→bureau (83K) - NOUVEAU
│   └── README.md
└── assets/
    └── README.md
```

### Pages terminées

#### index.html (Landing page)
- **Hero 1** : Texte gauche + mockup CSS laptop (dashboard.png) + phone (portail.png) droite
  - Background: gradient gris `#EDF2F7 → #FAFAFA`
  - Titre: "Une ville mieux gérée, des citoyens écoutés."
- **Hero 2 (SIG)** : Texte gauche + mockup CSS desktop iMac (sig-web.png) + tablet (mobile-pwa.png) droite
  - Titre: "Maîtrisez votre patrimoine communal, du bureau au terrain."
- **Boutons CTA** : "Demander une démo" + "Voir les tarifs" (entre les 2 heros et la barre stats)
- **Barre stats + ancres** : 4 stats clés + liens ancre vers sections
- **3 Piliers** : Participation citoyenne, Gestion technique, Pilotage dirigeant
- **Section coûts** : Argument prix vs solutions séparées
- **Section avantages** : 6 cartes (Souveraineté, PWA, Illimité, etc.)
- **Grille tarifs** : 5 formules de 199 à 799/mois
- **CTA final** + Footer

#### fonctionnalites.html (Détail fonctionnalités)
- Header "7 applications intégrées"
- Bloc visuel sig-patrimoine.png (bureau ancien vs GéoClic)
- **7 blocs fonctionnalités** en grille alternée (texte/image) :
  1. SIG Web - screenshot dans mockup laptop
  2. GéoClic Data - screenshot dans mockup laptop
  3. Bloc visuel terrain-sync.png (sync terrain→bureau)
  4. Relevé Terrain Mobile - screenshot dans mockup phone (180px)
  5. Portail Citoyen - screenshot dans mockup phone (180px)
  6. Gestion des Demandes - screenshot dans mockup laptop
  7. Services Terrain & PWA Agent - screenshot dans mockup laptop
- Templates métiers (7 cartes : Éclairage, Mobilier, Espaces verts, etc.)
- Table comparatif (GéoClic vs solutions traditionnelles + GeoContrib)
- CTA + Footer

#### comparatif.html
- Comparaison détaillée GéoClic vs concurrents (Neocity, GeoContrib, etc.)
- Tableau fonctionnalités côte à côte

#### tarifs.html
- 5 formules : Essentiel (199), Confort (299), Premium (399), Intégral (549), Excellence (799)
- Positionnement premium vs Neocity (SIG inclus, users illimités)

### Patterns techniques
- **CSS device mockups** : laptop (border + base grise), phone (border-radius 24px), desktop iMac (stand + base), tablet
- **Workflow de déploiement** : Éditer `marketing/*.html` → copier dans `deploy/www/` → commit → push → `git pull` sur serveur
- **Images** : Toujours `max-width` contraint (850px pour visuels pleine largeur, 480px pour laptops, 180px pour phones)
- **Nginx** : `deploy/www/` monté en lecture seule (`/var/www:ro`) dans le conteneur nginx
- **Nav fixe** avec liens : Fonctionnalités, Comparatif, Tarifs, Demander une démo

### À faire
- [ ] Intégrer les 2 images visuels (sig-patrimoine, terrain-sync) dans le repo git (actuellement sur serveur seulement)
- [ ] Page de mentions légales / CGU
- [ ] Formulaire de contact (actuellement mailto:)
- [ ] Responsive mobile amélioré
- [ ] Favicon

---

### Scoring Global du Projet

| Critère | Note initiale | Note actuelle | Commentaire |
|---|---|---|---|
| Richesse fonctionnelle | 9/10 | 9.5/10 | +Dashboard dirigeant, onboarding, FAQ, guides, toast, breadcrumbs, SIG multi-projets + cockpit |
| Architecture technique | 7/10 | 7.5/10 | +Multi-workers, logging structuré, CI/CD, health endpoint |
| Sécurité | 4/10 | 8/10 | Injections SQL corrigées, secrets externalisés, rate limiting, uploads validés |
| Qualité du code | 6/10 | 7/10 | +CI/CD, tests corrigés, linting pipeline |
| Scalabilité | 4/10 | 6/10 | +4 workers (~200 req), backup amélioré (manque Redis, S3) |
| UX/Design | 5/10 | 7.5/10 | +White-labeling, toast, breadcrumbs, onboarding, SIG cockpit 3 onglets, aperçu couleurs |
| Documentation | 8/10 | 9/10 | +Guides par rôle, FAQ citoyen, doc production, doc tests |
| Prêt pour la production | 5/10 | 7.5/10 | White-label, onboarding, sécurisé, backups (manque multi-tenant) |
| **Note globale** | **5.7/10** | **7.8/10** | **Produit commercial viable pour déploiement mono-client** |

### Qualité Code par Application Frontend

| Application | Rôle | Framework UI | Score |
|---|---|---|---|
| geoclic_data | Admin Dashboard | Vuetify 3 | 9/10 |
| geoclic_demandes | Back-office demandes | CSS custom | 7/10 |
| geoclic_services | Desktop terrain | CSS custom | 7/10 |
| geoclic_services_pwa | PWA mobile terrain | CSS custom | 6/10 |
| geoclic_mobile_pwa | Relevé terrain offline | CSS custom | 8/10 |
| geoclic_sig_web | SIG cartographie | CSS custom + Turf.js | 8/10 |
| portail_citoyen | Portail citoyen public | CSS custom | 8/10 |

---

### Audit Sécurité - Vulnérabilités Détectées

#### CRITIQUE - Injections SQL

| Fichier | Lignes | Problème | Détail |
|---|---|---|---|
| `api/routers/postgis.py` | 397-405 | SQL Injection table/schema | `f'SELECT * FROM "{schema_name}"."{table_name}"'` - asyncpg exécution directe avec f-strings |
| `api/routers/postgis.py` | 483-487 | SQL Injection WHERE clause | `query += f" WHERE {request.where_clause}"` - commentaire dev reconnaît le problème |
| `api/config.py` | 18 | Clé secrète en dur | `secret_key: str = "dev_secret_key_change_in_production"` |
| `deploy/docker-compose.yml` | 33 | Mot de passe DB par défaut | `POSTGRES_PASSWORD: ${DB_PASSWORD:-geoclic_secure_password}` |
| `deploy/docker-compose.yml` | 64 | Clé JWT par défaut | `JWT_SECRET_KEY: ${JWT_SECRET_KEY:-change_this_secret_key_in_production}` |

#### HAUTE - Risques importants

| Fichier | Lignes | Problème |
|---|---|---|
| `api/routers/ogs.py` | 143, 313, 455 | Table name dans f-string (sanitize_table_name atténue mais anti-pattern) |
| `api/config.py` | 66 | `debug: bool = True` en production - expose les stack traces |
| `deploy/docker-compose.yml` | 41 | Port PostgreSQL 5432 exposé à l'extérieur |

#### MOYENNE-HAUTE - Patterns à risque

| Fichier | Lignes | Problème |
|---|---|---|
| `api/routers/zones.py` | 68, 152, 451, 827 | WHERE/UPDATE dynamiques en f-string (valeurs paramétrées mais structure variable) |
| `api/routers/demandes.py` | 160, 2278 | WHERE/UPDATE dynamiques en f-string |
| `api/routers/points.py` | 197-213 | WHERE dynamique en f-string |
| `api/routers/services.py` | 688, 1291, 1298 | UPDATE dynamiques en f-string |

### Problèmes Structurels Identifiés

#### Code dupliqué entre applications
- **MiniMap.vue** copié-collé entre geoclic_demandes et geoclic_services (seule la hauteur diffère)
- **useTheme.ts** dupliqué dans services, services_pwa, portail_citoyen
- **Store auth.ts** réécrit 5 fois (un par app) avec logique similaire
- **Fix icônes Leaflet** copié dans chaque composant map

#### Double table agents (dette technique)
- `demandes_services_agents` (legacy) + `geoclic_users` (auth unifiée) = synchronisation manuelle
- Chaque création/modification d'agent doit écrire dans les DEUX tables
- Source de bugs réguliers (IDs incompatibles)

#### Versions incohérentes entre apps
- Vue : mix 3.4.0 et 3.5.21
- Vite : mix 5.x et 7.x
- Pinia : mix 2.x et 3.x

#### Manques pour la commercialisation
- Pas de multi-tenancy (1 instance Docker = 1 client)
- Pas de white-labeling (logo, couleurs, nom configurables)
- Pas de CI/CD (pas de GitHub Actions)
- Pas de monitoring applicatif (Sentry, Prometheus)
- Pas de documentation utilisateur (guides par rôle)
- Pas d'onboarding wizard pour nouveaux clients
- Pas de tableau de bord dirigeant avec KPI visuels
- Email synchrone (smtplib bloque le thread)
- Uvicorn mono-worker (~50 requêtes concurrentes max)
- Pas de cache Redis
- Photos stockées localement (pas de S3/CDN)

---

## Plan de Commercialisation - Feuille de Route

### Vue d'ensemble des phases

```
Phase 12 : Sécurisation ................. BLOQUANT - à faire en premier
Phase 13 : Industrialisation ............ Infrastructure et qualité
Phase 14 : Produit commercial ........... White-label et UX
Phase 15 : Scale ........................ Multi-tenant et performance
```

---

### Phase 12 : Sécurisation (BLOQUANT)

**Objectif :** Corriger toutes les vulnérabilités de sécurité avant toute mise en production client.

#### 12.1 - Corriger les injections SQL

| Tâche | Fichier | Priorité |
|---|---|---|
| Remplacer f-strings par requêtes paramétrées dans postgis.py | `api/routers/postgis.py` | P0 |
| Supprimer `where_clause` brut ou implémenter whitelist | `api/routers/postgis.py:483` | P0 |
| Corriger table names dynamiques dans ogs.py | `api/routers/ogs.py` | P0 |
| Sécuriser les WHERE dynamiques dans zones.py | `api/routers/zones.py` | P1 |
| Sécuriser les WHERE dynamiques dans demandes.py | `api/routers/demandes.py` | P1 |
| Sécuriser les WHERE dynamiques dans points.py | `api/routers/points.py` | P1 |
| Sécuriser les UPDATE dynamiques dans services.py | `api/routers/services.py` | P1 |
| Sécuriser les placeholders dans qrcodes.py | `api/routers/qrcodes.py` | P2 |

**Pattern de correction :**
```python
# AVANT (vulnérable)
query = f'SELECT * FROM "{schema_name}"."{table_name}" WHERE {where_clause}'

# APRÈS (sécurisé) - pour table/schema names
import re
def validate_identifier(name: str) -> str:
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise HTTPException(400, f"Identifiant invalide: {name}")
    return name

schema = validate_identifier(schema_name)
table = validate_identifier(table_name)
query = f'SELECT * FROM "{schema}"."{table}" WHERE column = :value'

# APRÈS (sécurisé) - pour WHERE/UPDATE dynamiques
# Utiliser une whitelist de colonnes autorisées
ALLOWED_COLUMNS = {"statut", "priorite", "description", "agent_service_id"}
for col in requested_columns:
    if col not in ALLOWED_COLUMNS:
        raise HTTPException(400, f"Colonne non autorisée: {col}")
```

#### 12.2 - Sécuriser la configuration

| Tâche | Fichier |
|---|---|
| Forcer `debug: bool = False` en production | `api/config.py:66` |
| Clé secrète via variable d'environnement obligatoire (pas de défaut) | `api/config.py:18` |
| Supprimer les IPs publiques des CORS origins | `api/config.py:50-56` |
| Rendre JWT_SECRET_KEY obligatoire (pas de valeur par défaut) | `deploy/docker-compose.yml:64` |
| Créer fichier `.env.example` avec toutes les variables requises | `deploy/.env.example` (nouveau) |
| Ne plus exposer le port 5432 (supprimer la directive ports pour db) | `deploy/docker-compose.yml:41` |

#### 12.3 - Sécuriser les uploads

| Tâche | Fichier |
|---|---|
| Ajouter validation MIME type réelle (python-magic) | `api/routers/demandes.py` |
| Limiter la taille max des fichiers (10 MB) | `api/routers/demandes.py` |
| Renommer les fichiers uploadés (UUID au lieu du nom original) | `api/routers/demandes.py` |
| Ajouter validation d'extension (.jpg, .jpeg, .png, .pdf uniquement) | `api/routers/demandes.py` |

#### 12.4 - Sécuriser l'authentification

| Tâche | Fichier |
|---|---|
| Ajouter rate limiting sur `/api/auth/login` (max 5 tentatives/min) | `api/routers/auth.py` |
| Ajouter mécanisme de blacklist JWT (Redis ou table DB) | `api/routers/auth.py` |
| Réduire durée de vie JWT (24h -> 8h) | `api/config.py` |
| Ajouter refresh token pour renouvellement transparent | `api/routers/auth.py` |

---

### Phase 13 : Industrialisation

**Objectif :** Rendre le projet maintenable, testable et déployable de manière fiable.

#### 13.1 - Performance API

| Tâche | Fichier |
|---|---|
| Configurer Uvicorn multi-workers (--workers 4) | `deploy/docker-compose.yml` |
| Ajouter Redis pour cache des requêtes fréquentes | `deploy/docker-compose.yml` + `api/` |
| Implémenter cache sur les endpoints lourds (stats, listes, catégories) | `api/routers/*.py` |
| Remplacer smtplib par aiosmtplib (email asynchrone) | `api/notifications.py` |
| Ajouter pagination systématique sur tous les endpoints de liste | `api/routers/*.py` |

#### 13.2 - CI/CD Pipeline

| Tâche | Fichier |
|---|---|
| Créer GitHub Actions workflow : lint + type check | `.github/workflows/ci.yml` (nouveau) |
| Ajouter job tests automatisés dans le pipeline | `.github/workflows/ci.yml` |
| Ajouter job build Docker dans le pipeline | `.github/workflows/ci.yml` |
| Créer script de déploiement automatique (SSH + pull + rebuild) | `scripts/deploy.sh` (nouveau) |
| Ajouter ESLint à toutes les apps frontend | `*/eslint.config.js` (nouveau) |

#### 13.3 - Tests automatisés

| Tâche | Fichier |
|---|---|
| Réparer conftest.py (base de test séparée, isolation) | `api/tests/conftest.py` |
| Faire passer test_auth.py (corriger noms de colonnes) | `api/tests/test_auth.py` |
| Faire passer test_demandes.py | `api/tests/test_demandes.py` |
| Faire passer test_services.py | `api/tests/test_services.py` |
| Ajouter tests de sécurité (injection SQL, auth bypass) | `api/tests/test_security.py` (nouveau) |
| Objectif: 80%+ des tests passent avant chaque déploiement | - |

#### 13.4 - Monitoring et observabilité

| Tâche | Fichier |
|---|---|
| Intégrer Sentry pour tracking des erreurs | `api/main.py` |
| Ajouter endpoint `/api/health` détaillé (DB, Redis, disk) | `api/routers/health.py` |
| Ajouter logging structuré (JSON) | `api/main.py` |
| Configurer alertes email sur erreurs 500 | Sentry dashboard |

#### 13.5 - Unification du code frontend

| Tâche | Fichier |
|---|---|
| Aligner toutes les apps sur Vue 3.5.x + Vite 7.x + Pinia 3.x | `*/package.json` |
| Extraire MiniMap.vue partagé (avec prop `height`) | `shared/components/MiniMap.vue` (nouveau) |
| Extraire composable useAuth.ts partagé | `shared/composables/useAuth.ts` (nouveau) |
| Extraire composable useTheme.ts partagé | `shared/composables/useTheme.ts` (nouveau) |
| Standardiser les clés localStorage (même pattern partout) | `*/stores/auth.ts` |
| Fusionner la table `demandes_services_agents` dans `geoclic_users` | Migration 018 (nouveau) |

#### 13.6 - Backup et résilience

| Tâche | Fichier |
|---|---|
| Ajouter backup des photos (volume geoclic_photos_data) | `scripts/backup_db.sh` |
| Configurer backup offsite (S3 ou autre stockage distant) | `scripts/backup_offsite.sh` (nouveau) |
| Documenter procédure de restauration complète (DB + photos) | `docs/GUIDE_PRODUCTION.md` |
| Ajouter vérification intégrité des backups | `scripts/backup_db.sh` |

---

### Phase 14 : Produit Commercial

**Objectif :** Transformer le prototype en produit vendable avec personnalisation client.

#### 14.1 - White-labeling (personnalisation par client)

| Tâche | Description |
|---|---|
| Table `tenant_config` en base | Logo, couleurs, nom, domaine, SMTP par client |
| Endpoint API `/api/config/tenant` | Retourne la config du tenant actuel |
| Chargement dynamique logo/couleurs dans chaque app | CSS variables injectées au chargement |
| Page d'administration du tenant dans geoclic_data | CRUD logo, couleurs, nom de la collectivité |
| Personnalisation des emails (logo + couleurs dans les templates) | `api/notifications.py` |

#### 14.2 - Onboarding et configuration initiale

| Tâche | Description |
|---|---|
| Wizard de première configuration | 5 étapes : collectivité, admin, SMTP, zones, catégories |
| Import automatique des données IRIS par code commune | Appel API INSEE + import géo |
| Catégories par défaut pré-configurées | Voirie, Propreté, Espaces verts, Éclairage, etc. |
| Jeu de données de démonstration | Script SQL pour données fictives réalistes |

#### 14.3 - Tableau de bord dirigeant

| Tâche | Description |
|---|---|
| Dashboard KPI avec graphiques (Chart.js ou D3) | Tendances, délais moyens, volume par catégorie |
| Export PDF du rapport mensuel | Résumé automatique pour les élus |
| Comparaison inter-périodes | Ce mois vs mois précédent, année N vs N-1 |
| Carte thermique des signalements | Heatmap Leaflet des zones à problèmes |

#### 14.4 - Documentation utilisateur

| Tâche | Description |
|---|---|
| Guide utilisateur Administrateur (PDF) | Config, utilisateurs, catégories, services |
| Guide utilisateur Agent back-office (PDF) | Traitement demandes, tchat, statistiques |
| Guide utilisateur Agent terrain (PDF) | PWA mobile, interventions, navigation GPS |
| Guide citoyen (intégré au portail) | FAQ, comment signaler, suivi |
| Vidéos de démonstration (5 min par module) | Screencast commenté de chaque app |
| Conditions Générales d'Utilisation / Mentions légales | Page juridique configurable |

#### 14.5 - Améliorations UX

| Tâche | Description |
|---|---|
| Design system unifié (CSS variables partagées) | Couleurs, typographie, espacements, ombres |
| Notifications in-app (toast notifications) | Feedback visuel sur actions (sauvegarde, erreur) |
| Breadcrumbs navigation dans chaque app | Orientation utilisateur |
| Responsive amélioré sur geoclic_demandes | Actuellement desktop-first, doit être mobile-friendly |
| Animations de transition entre pages | Vue transition API pour fluidité |

---

### Phase 15 : Scale (après premiers clients)

**Objectif :** Supporter des dizaines de clients avec performance et coût maîtrisés.

#### 15.1 - Multi-tenancy

| Option | Avantages | Inconvénients |
|---|---|---|
| **A. Schema par tenant** (PostgreSQL schemas) | Isolation données, même instance | Migrations complexes |
| **B. Colonne tenant_id** partout | Simple, une seule base | Pas d'isolation forte |
| **C. Instance par client** (actuel + provisioning) | Isolation totale | Coût infra élevé |

**Recommandation :** Option A (schema par tenant) pour le meilleur compromis isolation/coût.

#### 15.2 - Performance et infrastructure

| Tâche | Description |
|---|---|
| Réplication PostgreSQL (read replicas) | Séparer lectures/écritures |
| Migration photos vers S3 (MinIO ou AWS) | Scalabilité stockage + CDN |
| CDN pour assets frontend (CloudFlare) | Réduire latence + charge serveur |
| WebSocket pour le tchat (remplacer polling 30s) | Temps réel, moins de requêtes |
| API versioning (/api/v1/, /api/v2/) | Évolution sans casser les clients existants |
| Load balancer (Traefik ou HAProxy) | Distribution de charge multi-instance |

#### 15.3 - Fonctionnalités avancées (post-lancement)

| Tâche | Description |
|---|---|
| Application mobile native (Flutter) | Meilleure UX que PWA pour le terrain |
| Intégration OpenData | Publication automatique des signalements anonymisés |
| API publique documentée (OpenAPI/Swagger) | Permettre intégrations tierces |
| Webhooks pour événements | Intégration avec outils tiers (Slack, Teams) |
| Module facturation intégré | Gestion abonnements et paiements |

---

### Ordre d'Exécution Recommandé

```
ÉTAPE 1 - Phase 12 (Sécurisation) .......... ✅ TERMINÉE (février 2026)
ÉTAPE 2 - Phase 13 (Industrialisation) ..... ✅ TERMINÉE (février 2026)
ÉTAPE 3 - Phase 14 (Produit Commercial) .... ✅ TERMINÉE (février 2026)
ÉTAPE 4 - Phase 15 (Scale) ................ À faire après premiers clients payants
```

---

### Métriques de Suivi

Pour chaque phase, vérifier avant de passer à la suivante :

**Phase 12 (Sécurisation) - TERMINÉE (février 2026) :**
- [x] Injections SQL corrigées (postgis.py: validate_sql_identifier + filtres structurés, ogs.py: validate_ogs_table_name, zones/demandes/services: ALLOWED_UPDATE_COLS whitelists)
- [x] Aucun secret en dur (config.py: secret_key via env, debug=False par défaut)
- [x] Port DB non exposé (docker-compose: ports commentés)
- [x] JWT_SECRET_KEY obligatoire (docker-compose: ${JWT_SECRET_KEY:?ERREUR})
- [x] Rate limiting sur login (5 tentatives/min/email, HTTP 429)
- [x] Uploads validés (PIL image verify, extension whitelist .jpg/.jpeg/.png/.gif/.webp, path traversal protection)
- [x] ZIP path traversal protection (imports.py, sig.py)
- [x] Frontend PostGIS mis à jour (imports.vue: filtres structurés au lieu de where_clause brut)
- **Note:** Rate limiting en mémoire (distribué sur 4 workers). Pour production haute charge, migrer vers Redis.

**Phase 13 (Industrialisation) - TERMINÉE (février 2026) :**
- [x] Uvicorn 4 workers (Dockerfile.api: --workers 4, ~200 req concurrentes)
- [x] Health endpoint détaillé (vérifie DB + storage, retourne status degraded si problème)
- [x] Logging structuré (JSON en production, format lisible en dev, print() remplacés par logger)
- [x] Pipeline CI/CD GitHub Actions (.github/workflows/ci.yml: tests API, builds frontend, build Docker)
- [x] Tests corrigés (conftest.py: geoclic_users + /api/auth/login, test_auth.py idem)
- [x] Backup amélioré (DB format custom + SQL, photos via tar, vérification intégrité pg_restore --list, rotation hebdo 28j)
- [ ] Sentry (à configurer sur l'instance de production)
- [ ] Table agents unifiée (reporté: risque de régression élevé, nécessite migration complexe)
- [ ] Unification frontend versions (reporté: nécessite tests manuels sur chaque app, Pinia 2→3 breaking changes)
- **Duplication documentée:** MiniMap.vue (2 copies, diff=height), useTheme.ts (4 copies identiques), fix icônes Leaflet (3 copies)

**Phase 14 (Produit Commercial) - TERMINÉE (février 2026) :**
- [x] White-labeling: Endpoint branding public + admin CRUD, CSS variables dynamiques, color pickers dans Paramètres (demandes + data)
- [x] Onboarding wizard: 5 étapes (Identité, Email, Catégories, Services, Récap), détection auto, templates catégories
- [x] Dashboard dirigeant: 10+ KPI, Doughnut statuts, Bar chart 12 mois, comparaisons inter-périodes avec variations %
- [x] Documentation: 4 guides par rôle dans le système d'aide, FAQ portail citoyen (13 questions, 4 catégories)
- [x] Toast notifications + Breadcrumbs intégrés dans geoclic_demandes
- [ ] Export PDF du rapport mensuel (reporté: nécessite librairie PDF côté serveur)
- [ ] Carte thermique heatmap (reporté: fonctionnalité avancée Phase 15)
- [ ] Responsive mobile geoclic_demandes (reporté: desktop-first suffisant pour le lancement)

**Phase 15 (Scale) - Critères de validation :**
- [ ] Multi-tenant fonctionnel (2+ clients sur même instance)
- [ ] Photos sur stockage distant (S3)
- [ ] Tchat en WebSocket
- [ ] API versionnée

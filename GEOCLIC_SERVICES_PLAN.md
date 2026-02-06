# GeoClic Services - Plan de développement

## Vue d'ensemble

**GeoClic Services** est le nouveau module destiné aux équipes des services municipaux pour gérer les demandes qui leur sont assignées depuis GeoClic Demandes.

### Architecture globale

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Portail Citoyen   │────▶│  GeoClic Demandes   │────▶│  GeoClic Services   │
│   (signalement)     │     │  (back-office)      │     │  (services terrain) │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                                     │                           │
                                     │    Assigne au service     │
                                     └───────────────────────────┘
```

### Séparation des responsabilités

| Module | Responsabilité |
|--------|----------------|
| **GeoClic Demandes** | Réception, modération, assignation aux services, création des comptes service |
| **GeoClic Services** | Traitement des demandes, intervention terrain, tchat avec demandes |

---

## Base de données

### Nouvelles tables

```sql
-- Table messages tchat
CREATE TABLE demandes_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demande_id UUID NOT NULL REFERENCES demandes_citoyens(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL,  -- 'service' ou 'demandes'
    sender_id UUID,                     -- agent service ou user demandes
    sender_nom VARCHAR(100),
    message TEXT NOT NULL,
    lu_par_service BOOLEAN DEFAULT FALSE,
    lu_par_demandes BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_demande ON demandes_messages(demande_id);
CREATE INDEX idx_messages_created ON demandes_messages(created_at DESC);
```

### Extension table existante

```sql
-- Ajouter colonnes auth à demandes_services_agents
ALTER TABLE demandes_services_agents
ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'agent',  -- 'responsable' ou 'agent'
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP,
ADD COLUMN IF NOT EXISTS actif BOOLEAN DEFAULT TRUE;

-- Index pour login
CREATE UNIQUE INDEX IF NOT EXISTS idx_agents_email ON demandes_services_agents(email) WHERE email IS NOT NULL;
```

---

## Authentification

### Principes

- **Système JWT séparé** de GeoClic Demandes
- **Comptes créés depuis GeoClic Demandes** par les administrateurs
- **Filtre automatique** : chaque user ne voit que les demandes de son service
- **Deux rôles** : `responsable` (gère les agents) et `agent` (terrain)

### Endpoints API

```
POST /api/services/auth/login          # Connexion
POST /api/services/auth/logout         # Déconnexion
GET  /api/services/auth/me             # Profil utilisateur
PUT  /api/services/auth/password       # Changer mot de passe
```

### Token JWT

```json
{
  "sub": "agent_uuid",
  "type": "service",
  "service_id": "service_uuid",
  "role": "agent|responsable",
  "exp": 1234567890
}
```

---

## Fonctionnalités

### 1. Dashboard

- Statistiques du service :
  - Demandes en attente
  - Demandes en cours
  - Demandes résolues (jour/semaine/mois)
  - Délai moyen de traitement
- Alertes :
  - Demandes urgentes
  - Demandes en retard (> X jours)

### 2. Liste des demandes

- **Filtrée automatiquement** par service de l'utilisateur connecté
- Colonnes : Numéro, Catégorie, Description, Statut, Priorité, Date, Agent
- **Indicateur messages non lus** (pastille rouge avec compteur)
- Filtres : statut, priorité, agent assigné, période
- Recherche texte

### 3. Détail demande

- Informations complètes de la demande
- Photos du signalement
- **Tchat intégré** (section en bas de page)
- Actions :
  - Prendre en charge
  - Assigner à un agent (responsable uniquement)
  - Changer statut
  - Ajouter photos d'intervention
  - Résoudre/Clôturer

### 4. Tchat par demande

- **Implémentation simple** : polling toutes les 30 secondes
- Messages visibles par : service + back-office demandes
- Indicateur de messages non lus dans la liste
- Historique complet des échanges

### 5. Gestion des agents (responsable uniquement)

- Liste des agents du service
- Créer/modifier/désactiver agents
- Voir les demandes par agent

### 6. Notifications intelligentes

- Email automatique si demande non traitée après X jours
- Configurable par service (délai, destinataires)

---

## Structure du projet

```
geoclic_services/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── ChatSection.vue
│   │   ├── DemandeCard.vue
│   │   └── StatsCard.vue
│   ├── stores/
│   │   ├── auth.ts
│   │   ├── demandes.ts
│   │   └── messages.ts
│   ├── views/
│   │   ├── LoginView.vue
│   │   ├── DashboardView.vue
│   │   ├── DemandesListView.vue
│   │   ├── DemandeDetailView.vue
│   │   └── AgentsView.vue
│   ├── router.ts
│   ├── App.vue
│   └── main.ts
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── Dockerfile
```

---

## API Endpoints (nouveau router)

### Authentification
```
POST   /api/services/auth/login
POST   /api/services/auth/logout
GET    /api/services/auth/me
PUT    /api/services/auth/password
```

### Demandes (filtrées par service)
```
GET    /api/services/demandes                    # Liste demandes du service
GET    /api/services/demandes/{id}               # Détail demande
PUT    /api/services/demandes/{id}/statut        # Changer statut
PUT    /api/services/demandes/{id}/agent         # Assigner agent
POST   /api/services/demandes/{id}/photos        # Ajouter photos intervention
```

### Messages (tchat)
```
GET    /api/services/demandes/{id}/messages      # Liste messages
POST   /api/services/demandes/{id}/messages      # Envoyer message
PUT    /api/services/demandes/{id}/messages/read # Marquer comme lus
GET    /api/services/demandes/unread-count       # Compteur non lus par demande
```

### Agents (responsable uniquement)
```
GET    /api/services/agents                      # Liste agents du service
POST   /api/services/agents                      # Créer agent
PUT    /api/services/agents/{id}                 # Modifier agent
DELETE /api/services/agents/{id}                 # Désactiver agent
```

### Stats
```
GET    /api/services/stats                       # Stats du service
```

---

## Plan de développement

### Phase 1 : Fondations
1. Migration BDD (`008_geoclic_services.sql`)
2. Router API services (`api/routers/services.py`)
3. Authentification service
4. CRUD agents depuis GeoClic Demandes
5. Tests API

### Phase 2 : Frontend Desktop
1. Setup projet Vue 3 + TypeScript + Vite
2. Écran login
3. Dashboard avec stats
4. Liste demandes avec filtres
5. Détail demande + actions
6. Section tchat intégrée
7. Indicateur messages non lus

### Phase 3 : Intégration tchat dans Demandes
1. Ajouter section tchat dans DemandeDetailView.vue (côté demandes)
2. Indicateur messages non lus dans liste demandes

### Phase 4 : Notifications
1. Job périodique pour vérifier demandes en retard
2. Envoi emails de rappel
3. Configuration par service

### Phase 5 (futur) : PWA Mobile
1. Responsive design
2. Manifest PWA
3. Service worker pour cache basique

---

## Configuration Docker

### docker-compose.yml (ajout)

```yaml
  services:
    build:
      context: ../geoclic_services
      dockerfile: Dockerfile
    container_name: geoclic_services
    restart: unless-stopped
    ports:
      - "5178:80"
    depends_on:
      - api
    networks:
      - geoclic_network
```

### Nginx (ajout location)

```nginx
location /services/ {
    proxy_pass http://geoclic_services:80/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## Décisions techniques

| Sujet | Décision | Raison |
|-------|----------|--------|
| BDD | Extension tables existantes | Plus simple, moins de duplication |
| Auth | JWT séparé, créé depuis Demandes | Séparation claire des responsabilités |
| Tchat | Polling 30s | Plus fiable que WebSocket, suffisant pour le cas d'usage |
| Desktop/Mobile | Desktop d'abord | Priorité utilisateurs bureau |
| Notifications | Oui, après X jours | Rappels automatiques utiles |

---

## Fonctionnalités exclues (pour l'instant)

- Historique d'intervention détaillé
- Signature électronique
- Chronomètre temps de travail
- Rapports avancés (peut-être plus tard)

---

## URLs de production

- **GeoClic Services Desktop** : `https://geoclic.fr/services/`
- **API Services** : `https://geoclic.fr/api/services/`

---

## Notes importantes

1. **Sécurité** : Toujours vérifier que l'utilisateur connecté appartient au service de la demande
2. **Performance** : Indexer les colonnes fréquemment filtrées
3. **UX** : Garder l'interface simple et rapide pour les agents terrain
4. **Tchat** : Les messages sont visibles par service ET demandes, pas par le citoyen

# Plan de Développement GeoClic Demandes V2

> Document de planification phasée pour l'implémentation des nouvelles fonctionnalités.
> Date : 31/01/2026

---

## Vue d'ensemble

### Durée estimée totale
Le développement est découpé en **7 phases** progressives.

### Dépendances entre phases
```
Phase 1 (Backend + Catégories)
    ↓
Phase 2 (Doublons) ←→ Phase 3 (Services) [parallélisables]
    ↓
Phase 4 (geoclic_services Desktop)
    ↓
Phase 5 (Timeline Citoyen) ←→ Phase 6 (PWA Mobile) [parallélisables]
    ↓
Phase 7 (SLA + Calendrier)
```

---

## Phase 1 : Backend + Catégories hiérarchiques

### Objectif
Mettre en place les fondations : nouvelles tables, API et interface de gestion des catégories.

### 1.1 Backend (API FastAPI)

#### Nouvelles tables PostgreSQL

```sql
-- Catégories principales
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    icone VARCHAR(50),
    couleur VARCHAR(7), -- #RRGGBB
    ordre INTEGER DEFAULT 0,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sous-catégories
CREATE TABLE sous_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    categorie_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    icone VARCHAR(50),
    delai_traitement_heures INTEGER, -- SLA en heures
    priorite VARCHAR(20) DEFAULT 'normale', -- urgente, haute, normale, basse
    champs_supplementaires JSONB, -- formulaires dynamiques
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Mise à jour table demandes
ALTER TABLE demandes ADD COLUMN sous_categorie_id UUID REFERENCES sous_categories(id);
ALTER TABLE demandes ADD COLUMN statut VARCHAR(30) DEFAULT 'nouveau';
-- Statuts: nouveau, en_moderation, accepte, rejete, assigne, en_cours, termine_service, cloture
```

#### Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/v2/categories` | Liste catégories avec sous-catégories |
| POST | `/api/v2/categories` | Créer une catégorie |
| PUT | `/api/v2/categories/{id}` | Modifier une catégorie |
| DELETE | `/api/v2/categories/{id}` | Supprimer (si pas de demandes liées) |
| GET | `/api/v2/sous-categories` | Liste sous-catégories |
| POST | `/api/v2/sous-categories` | Créer une sous-catégorie |
| PUT | `/api/v2/sous-categories/{id}` | Modifier |
| DELETE | `/api/v2/sous-categories/{id}` | Supprimer |
| POST | `/api/v2/categories/import-lexique` | Importer depuis geoclic_data |

#### Fichiers à créer/modifier

```
api/
├── app/
│   ├── models/
│   │   ├── category.py         # Nouveau
│   │   └── demande.py          # Modifier (ajouter sous_categorie_id, statut)
│   ├── schemas/
│   │   ├── category.py         # Nouveau
│   │   └── demande.py          # Modifier
│   ├── crud/
│   │   ├── category.py         # Nouveau
│   │   └── demande.py          # Modifier
│   └── routers/
│       ├── categories.py       # Nouveau
│       └── demandes.py         # Modifier
└── alembic/
    └── versions/
        └── xxx_add_categories.py  # Migration
```

### 1.2 Frontend geoclic_demandes

#### Nouvelle page : Gestion des catégories

```
geoclic_demandes/src/
├── views/
│   └── CategoriesView.vue      # Nouveau
├── components/
│   └── categories/
│       ├── CategoryList.vue    # Liste des catégories
│       ├── CategoryForm.vue    # Formulaire création/édition
│       ├── SubCategoryList.vue # Sous-catégories d'une catégorie
│       ├── SubCategoryForm.vue # Formulaire sous-catégorie
│       └── IconPicker.vue      # Sélecteur d'icônes
├── stores/
│   └── categories.ts           # Pinia store
└── types/
    └── category.ts             # Types TypeScript
```

#### Interface visuelle

- Liste des catégories avec drag & drop pour réordonner
- Tuiles colorées avec aperçu de l'icône
- Modal pour ajouter/éditer
- Expansion pour voir les sous-catégories

### 1.3 Frontend portail_citoyen + app_citoyen

#### Sélection catégorie en tuiles

```vue
<!-- components/categories/CategorySelector.vue -->
<template>
  <div class="category-grid">
    <div
      v-for="cat in categories"
      :key="cat.id"
      class="category-tile"
      :style="{ backgroundColor: cat.couleur }"
      @click="selectCategory(cat)"
    >
      <v-icon :icon="cat.icone" size="48" />
      <span>{{ cat.nom }}</span>
    </div>
  </div>
</template>
```

### Livrables Phase 1

- [ ] Migration Alembic pour nouvelles tables
- [ ] Endpoints API catégories/sous-catégories
- [ ] Interface gestion catégories (geoclic_demandes)
- [ ] Sélecteur tuiles (portail_citoyen)
- [ ] Sélecteur tuiles (app_citoyen)
- [ ] Tests unitaires API
- [ ] Documentation API (Swagger)

---

## Phase 2 : Détection des doublons

### Objectif
Alerter le citoyen avant soumission si un signalement similaire existe à proximité.

### 2.1 Backend

#### Endpoint de détection

```python
# POST /api/v2/demandes/check-doublons
# Body: { latitude, longitude, sous_categorie_id }
# Response: { doublons: [...], count: N }

@router.post("/check-doublons")
async def check_doublons(
    latitude: float,
    longitude: float,
    sous_categorie_id: UUID,
    rayon_metres: int = 10,
    db: AsyncSession = Depends(get_db)
):
    # Requête PostGIS
    query = """
        SELECT d.*, ST_Distance(
            ST_MakePoint(:lon, :lat)::geography,
            ST_MakePoint(d.longitude, d.latitude)::geography
        ) as distance
        FROM demandes d
        WHERE d.sous_categorie_id = :cat_id
        AND d.statut NOT IN ('cloture', 'rejete')
        AND ST_DWithin(
            ST_MakePoint(:lon, :lat)::geography,
            ST_MakePoint(d.longitude, d.latitude)::geography,
            :rayon
        )
        ORDER BY distance
        LIMIT 5
    """
    return await db.execute(query, {...})
```

### 2.2 Frontend

#### Composant DuplicateWarning

```vue
<!-- components/DuplicateWarning.vue -->
<template>
  <v-dialog v-model="show" max-width="500">
    <v-card>
      <v-card-title class="warning">
        <v-icon>mdi-alert</v-icon>
        Un signalement similaire existe
      </v-card-title>
      <v-card-text>
        <DemandeMiniCard :demande="duplicate" />
        <p>Est-ce le même problème ?</p>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="cancel">Annuler mon signalement</v-btn>
        <v-btn color="primary" @click="continueAnyway">
          C'est différent, continuer
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
```

### Livrables Phase 2

- [ ] Extension PostGIS (si pas déjà)
- [ ] Endpoint `/check-doublons`
- [ ] Composant DuplicateWarning
- [ ] Intégration dans formulaire création (portail + mobile)
- [ ] Tests avec données de test géolocalisées

---

## Phase 3 : Services et affectation

### Objectif
Créer les services internes et permettre l'affectation des demandes.

### 3.1 Backend

#### Nouvelles tables

```sql
-- Services
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    couleur VARCHAR(7),
    responsable_id UUID REFERENCES utilisateurs(id),
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Membres des services (relation N-N)
CREATE TABLE service_membres (
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    utilisateur_id UUID REFERENCES utilisateurs(id) ON DELETE CASCADE,
    role VARCHAR(30) DEFAULT 'agent', -- responsable, agent
    PRIMARY KEY (service_id, utilisateur_id)
);

-- Liaison sous-catégorie → service par défaut
ALTER TABLE sous_categories ADD COLUMN service_defaut_id UUID REFERENCES services(id);

-- Affectation demande
ALTER TABLE demandes ADD COLUMN service_id UUID REFERENCES services(id);
ALTER TABLE demandes ADD COLUMN date_affectation TIMESTAMP;
ALTER TABLE demandes ADD COLUMN date_planification_prevue DATE;
ALTER TABLE demandes ADD COLUMN affecte_par_id UUID REFERENCES utilisateurs(id);
```

#### Endpoints API Services

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/v2/services` | Liste des services |
| POST | `/api/v2/services` | Créer un service |
| PUT | `/api/v2/services/{id}` | Modifier |
| DELETE | `/api/v2/services/{id}` | Supprimer |
| POST | `/api/v2/services/{id}/membres` | Ajouter un membre |
| DELETE | `/api/v2/services/{id}/membres/{user_id}` | Retirer |
| POST | `/api/v2/demandes/{id}/affecter` | Affecter à un service |

### 3.2 Frontend geoclic_demandes

#### Nouvelle page : Gestion des services

```
geoclic_demandes/src/
├── views/
│   └── ServicesView.vue        # Nouveau
├── components/
│   └── services/
│       ├── ServiceList.vue
│       ├── ServiceForm.vue
│       └── MembresManager.vue
```

#### Affectation dans la fiche demande

- Dropdown sélection service
- Date picker pour planification
- Historique des affectations

### Livrables Phase 3

- [ ] Migration tables services
- [ ] Endpoints API services
- [ ] Interface gestion services
- [ ] Modal affectation dans fiche demande
- [ ] Attribution automatique selon sous-catégorie (optionnel)

---

## Phase 4 : geoclic_services Desktop

### Objectif
Créer le nouveau module pour les services terrain.

### 4.1 Structure du projet

```bash
# Création du projet
npm create vue@latest geoclic_services -- --typescript

# Structure
geoclic_services/
├── src/
│   ├── views/
│   │   ├── DashboardView.vue   # Vue d'ensemble
│   │   ├── KanbanView.vue      # Vue Kanban
│   │   ├── CalendarView.vue    # Calendrier
│   │   └── DemandeDetailView.vue
│   ├── components/
│   │   ├── kanban/
│   │   │   ├── KanbanBoard.vue
│   │   │   ├── KanbanColumn.vue
│   │   │   └── KanbanCard.vue
│   │   ├── chat/
│   │   │   ├── ChatWindow.vue
│   │   │   └── ChatMessage.vue
│   │   └── photos/
│   │       └── PhotoUploader.vue
│   ├── stores/
│   │   ├── auth.ts
│   │   ├── demandes.ts
│   │   └── chat.ts
│   └── router/
│       └── index.ts
├── package.json
└── vite.config.ts
```

### 4.2 Fonctionnalités principales

#### Vue Kanban

- 3 colonnes : À faire | En cours | Terminé
- Drag & drop entre colonnes (met à jour le statut)
- Filtres : date, urgence
- Compteurs par colonne

#### Chat avec coordination

```typescript
// WebSocket ou polling pour messages temps réel
interface ChatMessage {
  id: string
  demande_id: string
  auteur_id: string
  auteur_nom: string
  contenu: string
  created_at: Date
  lu: boolean
}
```

#### Photo intervention

- Upload depuis appareil
- Compression automatique
- Association à la demande comme "photo_apres"

### Livrables Phase 4

- [ ] Projet Vue 3 geoclic_services
- [ ] Authentification (même système que geoclic_demandes)
- [ ] Vue Kanban fonctionnelle
- [ ] Fiche demande détaillée
- [ ] Système de chat (backend + frontend)
- [ ] Upload photo intervention
- [ ] Changement de statut
- [ ] Déploiement serveur

---

## Phase 5 : Timeline citoyen + Photos avant/après

### Objectif
Enrichir le suivi côté citoyen.

### 5.1 Backend

#### Table historique

```sql
CREATE TABLE demande_historique (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    demande_id UUID REFERENCES demandes(id) ON DELETE CASCADE,
    statut VARCHAR(30) NOT NULL,
    commentaire TEXT,
    auteur_id UUID REFERENCES utilisateurs(id),
    visible_citoyen BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index pour performance
CREATE INDEX idx_historique_demande ON demande_historique(demande_id);
```

#### Endpoint timeline

```python
@router.get("/demandes/{id}/timeline")
async def get_timeline(demande_id: UUID):
    # Retourne l'historique visible au citoyen
    return await crud.get_demande_timeline(demande_id, visible_citoyen_only=True)
```

### 5.2 Frontend portail_citoyen

#### Composant Timeline

```vue
<!-- components/DemandeTimeline.vue -->
<template>
  <v-timeline side="end">
    <v-timeline-item
      v-for="event in events"
      :key="event.id"
      :dot-color="getStatusColor(event.statut)"
      :icon="getStatusIcon(event.statut)"
    >
      <template #opposite>
        {{ formatDate(event.created_at) }}
      </template>
      <v-card>
        <v-card-title>{{ getStatusLabel(event.statut) }}</v-card-title>
        <v-card-text v-if="event.commentaire">
          {{ event.commentaire }}
        </v-card-text>
      </v-card>
    </v-timeline-item>
  </v-timeline>
</template>
```

#### Composant Photos avant/après

```vue
<!-- components/PhotosComparison.vue -->
<template>
  <v-row>
    <v-col cols="6">
      <v-card>
        <v-card-title>Avant</v-card-title>
        <v-img :src="photoAvant" aspect-ratio="1" />
        <v-card-subtitle>{{ dateSignalement }}</v-card-subtitle>
      </v-card>
    </v-col>
    <v-col cols="6">
      <v-card>
        <v-card-title>Après</v-card-title>
        <v-img :src="photoApres" aspect-ratio="1" />
        <v-card-subtitle>{{ dateIntervention }}</v-card-subtitle>
      </v-card>
    </v-col>
  </v-row>
</template>
```

### Livrables Phase 5

- [ ] Table demande_historique + migration
- [ ] Endpoint timeline
- [ ] Composant Timeline (portail + mobile)
- [ ] Composant Photos avant/après
- [ ] Page de suivi enrichie

---

## Phase 6 : geoclic_services PWA Mobile

### Objectif
Application mobile légère pour les agents terrain.

### 6.1 Configuration PWA

```typescript
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'GeoClic Services',
        short_name: 'GeoClic',
        theme_color: '#1976d2',
        icons: [...]
      },
      workbox: {
        // Cache pour mode hors-ligne
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.geoclic\.fr\/v2\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              networkTimeoutSeconds: 10
            }
          }
        ]
      }
    })
  ]
})
```

### 6.2 Fonctionnalités

| Fonctionnalité | Priorité |
|----------------|----------|
| Liste mes demandes du jour | Haute |
| Changement statut | Haute |
| Photo intervention | Haute |
| Chat | Moyenne |
| Mode hors-ligne | Moyenne |
| Scanner QR | Basse |

### 6.3 Mode hors-ligne

```typescript
// stores/offline.ts
export const useOfflineStore = defineStore('offline', {
  state: () => ({
    pendingActions: [] as OfflineAction[],
    lastSync: null as Date | null
  }),

  actions: {
    async sync() {
      if (!navigator.onLine) return

      for (const action of this.pendingActions) {
        await this.executeAction(action)
      }
      this.pendingActions = []
      this.lastSync = new Date()
    },

    queueAction(action: OfflineAction) {
      this.pendingActions.push(action)
      // Sauvegarde dans IndexedDB
    }
  }
})
```

### Livrables Phase 6

- [ ] Configuration PWA
- [ ] Interface mobile responsive
- [ ] Liste demandes simplifiée
- [ ] Changement statut
- [ ] Photo intervention (caméra)
- [ ] Mode hors-ligne basique
- [ ] Tests sur mobile réel

---

## Phase 7 : SLA + Intégration calendrier

### Objectif
Finaliser avec le suivi des délais et les intégrations.

### 7.1 SLA / Délais

#### Backend

```python
# Calcul du délai restant
def calculer_delai_restant(demande: Demande) -> timedelta:
    sous_cat = demande.sous_categorie
    if not sous_cat.delai_traitement_heures:
        return None

    deadline = demande.date_creation + timedelta(hours=sous_cat.delai_traitement_heures)
    return deadline - datetime.now()

# Alertes automatiques (tâche Celery ou cron)
@celery.task
def verifier_depassements_sla():
    demandes_en_retard = get_demandes_depassant_sla()
    for demande in demandes_en_retard:
        envoyer_alerte_admin(demande)
```

#### Dashboard SLA (geoclic_demandes)

- Graphique respect des délais
- Liste des demandes en retard
- Alertes visuelles (rouge/orange/vert)

### 7.2 Intégration calendrier

#### Export ICS

```python
@router.get("/demandes/export-ics")
async def export_ics(service_id: UUID = None):
    demandes = await get_demandes_planifiees(service_id)

    cal = Calendar()
    for d in demandes:
        event = Event()
        event.name = f"Intervention: {d.titre}"
        event.begin = d.date_planification_prevue
        event.location = d.adresse
        event.description = d.description
        cal.events.add(event)

    return Response(
        content=str(cal),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=planning.ics"}
    )
```

### Livrables Phase 7

- [ ] Calcul automatique des délais
- [ ] Alertes dépassement SLA
- [ ] Dashboard statistiques SLA
- [ ] Export ICS
- [ ] Intégration Google Calendar (optionnel)
- [ ] Documentation utilisateur finale

---

## Commandes de déploiement serveur OVH

### Prérequis
Votre serveur OVH doit avoir :
- Git installé
- Les dossiers dans `/opt/`

### Commandes pour mettre à jour depuis ma branche

```bash
# 1. Se connecter au serveur (depuis votre PC)
ssh utilisateur@votre-ip-ovh

# 2. Aller dans le dossier GeoClic_Suite
cd /opt/GeoClic_Suite

# 3. Récupérer ma branche de travail
git fetch origin claude/setup-geoclic-suite-JpjDO

# 4. Basculer sur la branche
git checkout claude/setup-geoclic-suite-JpjDO

# 5. Récupérer les modifications
git pull origin claude/setup-geoclic-suite-JpjDO

# OU si vous voulez rester sur main et juste récupérer mes modifications :
git fetch origin
git merge origin/claude/setup-geoclic-suite-JpjDO

# 6. Reconstruire les applications si nécessaire
cd /opt/GeoClic_Suite/geoclic_demandes
npm install
npm run build

# 7. Redémarrer les services
sudo systemctl restart nginx
```

---

## Résumé des priorités

| Phase | Priorité | Dépendances |
|-------|----------|-------------|
| Phase 1 | **CRITIQUE** | Aucune |
| Phase 2 | Haute | Phase 1 |
| Phase 3 | Haute | Phase 1 |
| Phase 4 | Haute | Phase 3 |
| Phase 5 | Moyenne | Phase 1 |
| Phase 6 | Moyenne | Phase 4 |
| Phase 7 | Basse | Phase 4 |

---

## Prochaine étape recommandée

**Commencer par la Phase 1** :
1. Créer les migrations Alembic pour les tables categories/sous_categories
2. Implémenter les endpoints API
3. Créer l'interface de gestion dans geoclic_demandes

Voulez-vous que je commence l'implémentation de la Phase 1 ?

# GéoClic Demandes - Back-office

Interface d'administration pour la gestion des demandes citoyennes (signalements).

## Fonctionnalités

### Tableau de bord
- Vue d'ensemble des demandes en cours
- Statistiques temps réel
- Accès rapide aux nouvelles demandes

### Gestion des demandes
- Liste filtrable et triable
- Détail complet de chaque demande
- Changement de statut avec workflow
- Assignation aux agents
- Planification des interventions
- Historique complet

### Carte interactive
- Visualisation géographique des demandes
- Filtrage par statut
- Accès rapide aux détails

### Catégories
- CRUD complet des catégories
- Icônes et couleurs personnalisables
- Activation/désactivation

### Templates de notification
- Personnalisation des emails/SMS
- Variables dynamiques
- Déclencheurs automatiques

### Statistiques
- Évolution temporelle
- Répartition par statut/catégorie/quartier
- Export des données

### Paramètres
- Configuration générale
- Paramètres SMTP
- Gestion des utilisateurs (admin)
- Profil personnel

## Installation

```bash
# Installation des dépendances
npm install

# Démarrage en développement
npm run dev

# Build de production
npm run build
```

## Configuration

Le back-office communique avec l'API GéoClic via le proxy Vite configuré.

En développement, l'API est attendue sur `http://localhost:8000`.

## Rôles utilisateurs

- **admin** : Accès complet (paramètres, utilisateurs, etc.)
- **moderateur** : Gestion des demandes, modération
- **agent** : Traitement des demandes assignées

## Workflow des demandes

```
nouveau → en_moderation → accepte → en_cours → planifie → traite → cloture
                       ↘ rejete
```

## Technologies

- Vue 3 + TypeScript
- Pinia (state management)
- Vue Router
- Chart.js (graphiques)
- Leaflet (cartes)
- Axios (HTTP)
- date-fns (dates)

## Structure du projet

```
geoclic_demandes/
├── src/
│   ├── assets/
│   │   └── styles.css
│   ├── stores/
│   │   ├── auth.ts
│   │   └── demandes.ts
│   ├── views/
│   │   ├── LoginView.vue
│   │   ├── DashboardView.vue
│   │   ├── DemandesListView.vue
│   │   ├── DemandeDetailView.vue
│   │   ├── CarteView.vue
│   │   ├── CategoriesView.vue
│   │   ├── TemplatesView.vue
│   │   ├── StatistiquesView.vue
│   │   └── ParametresView.vue
│   ├── App.vue
│   ├── main.ts
│   └── router.ts
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

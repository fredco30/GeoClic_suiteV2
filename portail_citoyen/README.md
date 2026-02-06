# Portail Citoyen GéoClic

Interface web publique permettant aux citoyens de signaler des problèmes et de suivre leurs demandes.

## Fonctionnalités

- **Signalement libre** : Créer un signalement avec localisation GPS ou sur carte
- **Signalement via QR code** : Scanner un QR code sur un équipement pour signaler un problème spécifique
- **Suivi des demandes** : Consulter l'avancement avec le numéro de suivi
- **Carte publique** : Visualiser les signalements en cours
- **Multi-langue** : Support FR/EN
- **Responsive** : Optimisé mobile

## Stack technique

- **Vue 3** avec Composition API
- **TypeScript**
- **Pinia** pour le state management
- **Vue Router** pour la navigation
- **Leaflet** pour la cartographie
- **Vite** pour le build

## Installation

```bash
# Installation des dépendances
npm install

# Démarrage en développement
npm run dev

# Build production
npm run build
```

## Configuration

Le portail nécessite :
1. Un `project_id` (UUID du projet/collectivité)
2. L'API GéoClic accessible sur `/api`

### Variables d'environnement

Créer un fichier `.env.local` :

```env
VITE_API_URL=http://localhost:8000
VITE_DEFAULT_PROJECT_ID=votre-uuid-projet
```

## Structure

```
src/
├── assets/          # CSS, images
├── components/      # Composants réutilisables
│   ├── MapPicker.vue
│   └── PhotoUploader.vue
├── services/        # API client
│   └── api.ts
├── stores/          # Pinia stores
│   └── config.ts
├── views/           # Pages
│   ├── HomeView.vue
│   ├── SignalerView.vue
│   ├── SignalerQRView.vue
│   ├── SuiviView.vue
│   ├── SuiviDetailView.vue
│   └── CarteView.vue
├── App.vue
├── main.ts
└── router.ts
```

## Endpoints API utilisés

- `GET /api/demandes/categories` - Liste des catégories
- `POST /api/demandes/public/demandes` - Créer un signalement
- `GET /api/demandes/public/demandes/{numero}` - Détail d'un signalement
- `GET /api/public/equipements/{id}` - Info équipement (QR code)

## Personnalisation

Le thème (couleurs, logo) est configurable par projet via l'API.

```javascript
// Dans config store
theme: {
  primaryColor: '#2563eb',
  logo: '/logo.png',
  bannerImage: '/banner.jpg'
}
```

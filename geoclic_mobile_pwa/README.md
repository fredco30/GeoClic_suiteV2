# Geoclic Mobile PWA

Application web progressive (PWA) pour la collecte de données terrain géolocalisées.

## Fonctionnalités

- **GPS natif** : Utilise l'API Geolocation du navigateur (HTTPS requis)
- **Mode hors-ligne** : Fonctionne sans connexion grâce à IndexedDB
- **Installable** : S'installe sur l'écran d'accueil (iOS/Android)
- **Synchronisation** : Upload/download des points avec le serveur
- **Photos** : Capture et géolocalisation des photos
- **Cartographie** : Visualisation des points sur carte OpenStreetMap

## Prérequis

- Node.js 18+ ou 20+
- Serveur API Geoclic (port 8000)
- **HTTPS obligatoire** pour le GPS (voir [DEPLOIEMENT_HTTPS_SAAS.md](../DEPLOIEMENT_HTTPS_SAAS.md))

## Installation

```bash
# Aller dans le dossier
cd geoclic_mobile_pwa

# Installer les dépendances
npm install
```

## Développement

```bash
# Démarrer le serveur de développement
npm run dev

# Accessible sur http://localhost:3001
# Note: le GPS ne fonctionnera qu'en HTTPS ou localhost
```

### Avec accès réseau externe

```bash
# Pour tester sur mobile via IP locale
npm run dev:host

# Accessible sur http://VOTRE_IP:3001
```

## Build de production

```bash
# Builder l'application
npm run build

# Preview du build
npm run preview

# Ou avec accès réseau
npm run preview:host
```

## Structure du projet

```
geoclic_mobile_pwa/
├── public/
│   ├── icons/              # Icônes PWA
│   ├── favicon.ico
│   └── robots.txt
├── src/
│   ├── components/         # Composants Vue réutilisables
│   │   ├── BottomNav.vue   # Navigation bas de page
│   │   ├── GpsStatus.vue   # Affichage statut GPS
│   │   └── LexiqueSelector.vue  # Sélecteur catégories
│   ├── views/              # Pages de l'application
│   │   ├── LoginView.vue   # Connexion + config serveur
│   │   ├── HomeView.vue    # Accueil avec stats
│   │   ├── PointsView.vue  # Liste des points
│   │   ├── PointFormView.vue  # Création/édition point
│   │   ├── MapView.vue     # Carte Leaflet
│   │   ├── SyncView.vue    # Synchronisation
│   │   └── SettingsView.vue # Paramètres
│   ├── services/           # Services métier
│   │   ├── api.ts          # Client API HTTP
│   │   ├── gps.ts          # Service géolocalisation
│   │   └── offline.ts      # Cache IndexedDB
│   ├── stores/             # État global (Pinia)
│   │   ├── auth.ts         # Authentification
│   │   └── points.ts       # Gestion des points
│   ├── styles/
│   │   └── main.css        # Styles globaux
│   ├── App.vue             # Composant racine
│   ├── main.ts             # Point d'entrée
│   └── router.ts           # Configuration routes
├── index.html
├── vite.config.ts          # Configuration Vite + PWA
├── tsconfig.json
└── package.json
```

## Configuration du serveur API

L'URL du serveur est configurable dans l'écran de connexion :

1. Cliquer sur "⚙️ Configurer le serveur"
2. Entrer l'URL complète : `https://votre-serveur.com:8443`
3. Tester la connexion
4. Enregistrer

L'URL est stockée dans le localStorage.

## Utilisation du GPS

### Pourquoi HTTPS ?

Les navigateurs modernes bloquent l'accès au GPS sur les connexions HTTP non sécurisées pour protéger la vie privée des utilisateurs.

| Contexte | GPS |
|----------|-----|
| `https://` avec certificat valide | ✅ Fonctionne |
| `http://localhost` | ✅ Exception dev |
| `http://` autre | ❌ Bloqué |

### Permissions

Au premier accès GPS, le navigateur demande la permission :

- **iOS Safari** : "Autoriser" ou "Autoriser pendant l'utilisation"
- **Android Chrome** : "Autoriser" avec persistance

### Précision

Le GPS utilise plusieurs sources :
- GPS hardware (meilleure précision : 1-5m)
- Wi-Fi positioning (~15m)
- Cell towers (~100m+)

La précision est affichée en temps réel dans l'application.

## Mode hors-ligne

L'application fonctionne sans connexion :

1. **Au premier lancement** : Télécharger les données de référence (Sync → Package hors-ligne)
2. **Créer des points** : Sauvegardés localement dans IndexedDB
3. **Prendre des photos** : Stockées en blob
4. **Retour en ligne** : Synchroniser pour envoyer les données

### Données en cache

- Points téléchargés
- Lexique (catégories)
- Projets
- Points en attente de sync
- Photos en attente

## Installation sur l'écran d'accueil

### iOS Safari

1. Ouvrir la PWA en Safari
2. Appuyer sur l'icône Partager (carré avec flèche)
3. Sélectionner "Sur l'écran d'accueil"
4. Nommer l'application et confirmer

### Android Chrome

1. Ouvrir la PWA en Chrome
2. Chrome affiche une bannière "Installer"
3. Ou : Menu (⋮) → "Installer l'application"
4. Confirmer l'installation

## Technologies utilisées

- **Vue.js 3** - Framework frontend
- **TypeScript** - Typage statique
- **Pinia** - Gestion d'état
- **Vue Router** - Navigation
- **Vite** - Build tool
- **vite-plugin-pwa** - Support PWA
- **Leaflet** - Cartographie
- **IndexedDB (idb)** - Stockage local
- **Axios** - Client HTTP

## Compatibilité

| Navigateur | Support |
|------------|---------|
| Chrome (Android) | ✅ Complet |
| Safari (iOS 11.3+) | ✅ Complet |
| Firefox (Android) | ✅ Complet |
| Edge | ✅ Complet |
| Samsung Internet | ✅ Complet |

## Développement

### Ajouter une nouvelle page

1. Créer le fichier dans `src/views/`
2. Ajouter la route dans `src/router.ts`
3. Optionnel : ajouter dans la navigation

### Ajouter un service

1. Créer le fichier dans `src/services/`
2. Exporter les fonctions/classes
3. Importer dans les composants

### Modifier le manifest PWA

Éditer la section `manifest` dans `vite.config.ts`.

## Licence

Propriétaire - Geoclic V12 Pro

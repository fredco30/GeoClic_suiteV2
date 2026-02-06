# Spécifications GéoClic Demandes V2

> Document de spécifications pour l'évolution du module de gestion des demandes citoyennes.
> Date : 31/01/2026

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture](#2-architecture)
3. [Catégories](#3-catégories)
4. [Services](#4-services)
5. [Flux de travail](#5-flux-de-travail)
6. [Détection des doublons](#6-détection-des-doublons)
7. [Modération](#7-modération)
8. [Délais et SLA](#8-délais-et-sla)
9. [Notifications](#9-notifications)
10. [geoclic_services (nouveau module)](#10-geoclic_services-nouveau-module)
11. [Portail citoyen enrichi](#11-portail-citoyen-enrichi)
12. [Intégrations](#12-intégrations)

---

## 1. Vue d'ensemble

### Objectif

Améliorer la gestion des demandes citoyennes avec :
- Une meilleure organisation par catégories visuelles
- Un nouveau module dédié aux services terrain
- Une communication fluide entre coordination et services
- Un suivi transparent pour les citoyens

### Modules concernés

| Module | Rôle | Utilisateurs |
|--------|------|--------------|
| **portail_citoyen** | Création et suivi des signalements | Citoyens |
| **app_citoyen** | Version mobile du portail | Citoyens |
| **geoclic_demandes** | Coordination et gestion | Administrateurs, modérateurs |
| **geoclic_services** (nouveau) | Traitement terrain | Agents des services techniques |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CITOYENS                                  │
├─────────────────────────────────────────────────────────────────┤
│  portail_citoyen (web)     │     app_citoyen (Flutter)          │
│  - Catégories visuelles    │     - Même fonctionnalités         │
│  - Timeline suivi          │     - Notifications push           │
│  - Photo avant/après       │                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    COORDINATION                                  │
├─────────────────────────────────────────────────────────────────┤
│                    geoclic_demandes                              │
│  - Réception demandes                                           │
│  - Modération (toutes catégories)                               │
│  - Affectation aux services                                     │
│  - Calendrier planification                                     │
│  - Chat avec services                                           │
│  - Validation / Clôture                                         │
│  - Statistiques & SLA                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICES TERRAIN                            │
├─────────────────────────────────────────────────────────────────┤
│  geoclic_services (desktop)  │  geoclic_services (PWA mobile)   │
│  - Vue Kanban                │  - Version allégée               │
│  - Mes demandes assignées    │  - Scanner QR équipement         │
│  - Chat avec coordination    │  - Mode hors-ligne               │
│  - Photo intervention        │  - Photo intervention            │
│  - Sync calendrier           │                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Catégories

### Structure

- **2 niveaux maximum** : Catégorie principale → Sous-catégories
- Exemple :
  ```
  📦 Réseaux humides
  ├── 🚽 Eaux usées
  ├── 🚰 Eau potable
  ├── 🌧️ Pluvial
  ├── 🌿 Irrigation espaces verts
  └── ⛲ Fontaines
  ```

### Affichage citoyen

- **Tuiles colorées** avec icône et nom
- Style visuel inspiré de l'application Flutter existante
- Navigation intuitive : clic sur catégorie → affiche sous-catégories

### Gestion (geoclic_demandes)

| Fonctionnalité | Description |
|----------------|-------------|
| Création | Interface dédiée dans geoclic_demandes |
| Import | Bouton "S'inspirer du lexique" (depuis geoclic_data) |
| Personnalisation | Icône, couleur, nom, description |
| Formulaires dynamiques | Champs spécifiques par catégorie (optionnel) |
| Activation | Possibilité d'activer/désactiver une catégorie |

### Formulaires dynamiques (optionnel)

Certaines catégories peuvent avoir des champs supplémentaires :

| Catégorie | Champs spécifiques |
|-----------|-------------------|
| Éclairage public | N° du lampadaire |
| Voirie | Taille approximative du défaut |
| Propreté | Type de déchet |

---

## 4. Services

### Définition

Les services représentent les équipes terrain qui traitent les demandes.

### Exemples

- Voirie
- Espaces verts
- Propreté
- Éclairage public
- Réseaux humides
- Bâtiments

### Gestion

| Élément | Description |
|---------|-------------|
| Création | Dans geoclic_demandes uniquement |
| Droits | L'admin geoclic_demandes définit qui accède à quoi |
| Visibilité | Chaque service ne voit QUE ses demandes assignées |

### Structure d'un service

```typescript
interface Service {
  id: string
  nom: string
  description?: string
  couleur?: string
  responsable_id?: string
  membres: string[] // IDs des utilisateurs
  actif: boolean
  created_at: Date
}
```

---

## 5. Flux de travail

### Diagramme complet

```
┌─────────────────────────────────────────────────────────────────┐
│  1. CITOYEN SIGNALE                                              │
│     - Choisit catégorie → sous-catégorie                        │
│     - Localise sur carte (GPS ou clic)                          │
│     - Description + photos                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. VÉRIFICATION DOUBLON (automatique)                          │
│     Critères : même catégorie + rayon 10m                       │
│     → Si doublon trouvé : afficher au citoyen                   │
│     → Choix : Annuler / Créer quand même                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. DEMANDE CRÉÉE                                                │
│     → Numéro de suivi généré (ex: SIG-2026-00042)               │
│     → Statut : "Nouveau"                                        │
│     → Email confirmation citoyen                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. MODÉRATION (geoclic_demandes)                                │
│     → Toutes les demandes passent par la modération             │
│     → Vérification pertinence                                   │
│     → Accepter / Rejeter avec motif                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. AFFECTATION (geoclic_demandes)                               │
│     → Choix du service                                          │
│     → Date de planification prévue                              │
│     → Statut : "Assigné"                                        │
│     → Email citoyen : "Prise en charge"                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. TRAITEMENT (geoclic_services)                                │
│     → Service reçoit la demande                                 │
│     → Chat si questions                                         │
│     → Intervention terrain                                      │
│     → Photo "après"                                             │
│     → Marque "Terminé" + commentaire                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  7. VALIDATION (geoclic_demandes)                                │
│     Coordination vérifie le travail :                           │
│                                                                 │
│     Option A : ✅ VALIDER                                       │
│     → Statut : "Clôturé"                                        │
│     → Email citoyen avec photo avant/après                      │
│                                                                 │
│     Option B : 🔄 RENVOYER AU SERVICE                           │
│     → Commentaire explicatif                                    │
│     → Retour à l'étape 6                                        │
│                                                                 │
│     Option C : 📝 CLÔTURER AVEC COMMENTAIRE                     │
│     → Clôture malgré réserves                                   │
│     → Commentaire interne conservé                              │
└─────────────────────────────────────────────────────────────────┘
```

### Statuts

| Statut | Description | Visible citoyen |
|--------|-------------|-----------------|
| `nouveau` | Vient d'être créé | ✅ "Nouveau" |
| `en_moderation` | En cours de vérification | ✅ "En cours de traitement" |
| `accepte` | Validé, en attente d'affectation | ✅ "Accepté" |
| `rejete` | Refusé (hors périmètre, etc.) | ✅ "Non retenu" |
| `assigne` | Affecté à un service | ✅ "Prise en charge" |
| `en_cours` | Service en intervention | ✅ "En cours" |
| `termine_service` | Service a terminé | ✅ "En cours de validation" |
| `cloture` | Terminé et validé | ✅ "Traité" |

---

## 6. Détection des doublons

### Objectif

Éviter les signalements en double pour le même problème.

### Critères de détection

| Critère | Valeur |
|---------|--------|
| Rayon géographique | 10 mètres |
| Catégorie | Même catégorie exacte |
| Statuts concernés | Tous sauf "clôturé" et "rejeté" |

### Interface citoyen

Quand un doublon potentiel est détecté :

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ Un signalement similaire existe à proximité                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📍 Nid de poule                                         │   │
│  │  📍 Rue de la Plage, La Grande-Motte                     │   │
│  │  📅 Signalé le 28/01/2026                                │   │
│  │  📊 Statut : En cours de traitement                      │   │
│  │                                                          │   │
│  │  [📍 Voir sur la carte]                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Est-ce le même problème ?                                     │
│                                                                 │
│  [ Annuler mon signalement ]  [ C'est différent, continuer ]   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Modération

### Périmètre

**Toutes les catégories** passent par la modération.

### Actions disponibles

| Action | Résultat |
|--------|----------|
| **Accepter** | Demande validée, prête pour affectation |
| **Rejeter** | Demande refusée avec motif obligatoire |
| **Demander précision** | Message au citoyen (futur) |

### Motifs de rejet (exemples)

- Hors périmètre géographique
- Signalement non pertinent
- Doublon avéré
- Information insuffisante
- Compétence autre collectivité

---

## 8. Délais et SLA

### Définition par catégorie

Chaque catégorie peut avoir un délai de traitement cible :

| Catégorie | Délai cible | Priorité |
|-----------|-------------|----------|
| Danger immédiat | 24h | Urgente |
| Voirie | 7 jours | Haute |
| Éclairage | 5 jours | Haute |
| Espaces verts | 14 jours | Normale |
| Propreté | 3 jours | Normale |
| Esthétique | 30 jours | Basse |

### Alertes

| Situation | Action |
|-----------|--------|
| 80% du délai atteint | Alerte jaune dans le tableau de bord |
| Délai dépassé | Alerte rouge + notification admin |
| Délai dépassé > 2x | Escalade automatique (optionnel) |

### Tableau de bord SLA

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 Respect des délais - Janvier 2026                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Dans les délais    ████████████████████░░░░  78%              │
│  En retard          ████░░░░░░░░░░░░░░░░░░░░  15%              │
│  Critique           ██░░░░░░░░░░░░░░░░░░░░░░   7%              │
│                                                                 │
│  Délai moyen de traitement : 4.2 jours                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Notifications

### Emails citoyen

| Événement | Objet email | Contenu |
|-----------|-------------|---------|
| Création | "Signalement enregistré" | N° suivi, récapitulatif, lien suivi |
| Prise en charge | "Votre signalement est pris en charge" | Service affecté, date prévue |
| Clôture | "Votre signalement a été traité" | Photo avant/après, commentaire, lien timeline |
| Rejet | "Votre signalement n'a pas été retenu" | Motif du rejet |

### Modèle email clôture

```
Bonjour,

Votre signalement n°SIG-2026-00042 a été traité.

📍 Nid de poule - Rue de la Plage
📅 Signalé le : 25/01/2026
✅ Traité le : 30/01/2026

Commentaire du service :
"Rebouchage effectué par l'équipe voirie."

[Voir les photos avant/après]
[Consulter le suivi complet]

Merci de votre contribution à l'amélioration de notre commune.

L'équipe GéoClic
```

---

## 10. geoclic_services (nouveau module)

### Objectif

Application dédiée aux services terrain pour traiter les demandes qui leur sont assignées.

### Versions

| Version | Plateforme | Usage |
|---------|------------|-------|
| Desktop | Web (Vue.js) | Bureau, gestion complète |
| Mobile | PWA | Terrain, intervention |

### Fonctionnalités Desktop

| Fonctionnalité | Description |
|----------------|-------------|
| **Liste demandes** | Uniquement celles assignées au service de l'utilisateur |
| **Vue Kanban** | Colonnes : À faire / En cours / Terminé |
| **Fiche demande** | Détails complets + historique |
| **Chat** | Discussion avec la coordination |
| **Photo intervention** | Upload photo "après" |
| **Calendrier** | Planning des interventions |
| **Sync calendrier** | Export vers Outlook / Google Calendar |

### Fonctionnalités PWA Mobile

| Fonctionnalité | Description |
|----------------|-------------|
| **Liste simplifiée** | Mes demandes du jour |
| **Scanner QR** | Identifier l'équipement concerné |
| **Photo intervention** | Prise de photo directe |
| **Changement statut** | En cours → Terminé |
| **Mode hors-ligne** | Sync quand connexion disponible |
| **Chat** | Messages avec coordination |

### Droits et accès

- **Créés par** : Administrateur geoclic_demandes
- **Principe** : Chaque utilisateur ne voit que les demandes de son service
- **Multi-service** : Un utilisateur peut appartenir à plusieurs services

### Interface Kanban (Desktop)

```
┌─────────────────────────────────────────────────────────────────┐
│  🔧 Service Voirie - Mes demandes                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  À FAIRE (3)        EN COURS (2)       TERMINÉ (5)             │
│  ┌───────────┐      ┌───────────┐      ┌───────────┐           │
│  │ SIG-042   │      │ SIG-038   │      │ SIG-031   │           │
│  │ Nid poule │      │ Trottoir  │      │ Marquage  │           │
│  │ 📍 Rue... │      │ 📍 Av...  │      │ ✅ 29/01  │           │
│  │ ⏰ 2j     │      │ 🔄 J+1    │      │           │           │
│  └───────────┘      └───────────┘      └───────────┘           │
│  ┌───────────┐      ┌───────────┐      ┌───────────┐           │
│  │ SIG-045   │      │ SIG-041   │      │ SIG-028   │           │
│  │ ...       │      │ ...       │      │ ...       │           │
│  └───────────┘      └───────────┘      └───────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Portail citoyen enrichi

### Timeline visuelle

Affichage chronologique de toutes les étapes :

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 Suivi de votre signalement SIG-2026-00042                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ 25/01 09:32  Signalement créé                              │
│  │               "Nid de poule dangereux"                       │
│  │                                                              │
│  ✅ 25/01 14:15  Signalement validé                            │
│  │               Pris en charge par la coordination             │
│  │                                                              │
│  ✅ 26/01 10:00  Affecté au service Voirie                     │
│  │               Intervention prévue le 29/01                   │
│  │                                                              │
│  ✅ 29/01 11:30  Intervention réalisée                         │
│  │               "Rebouchage effectué"                          │
│  │                                                              │
│  ✅ 30/01 09:00  Signalement clôturé                           │
│                   Merci pour votre contribution !               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Photo avant/après

```
┌─────────────────────────────────────────────────────────────────┐
│  📸 Photos                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  AVANT                          APRÈS                           │
│  ┌─────────────────┐           ┌─────────────────┐             │
│  │                 │           │                 │             │
│  │   [Photo nid    │    →→→    │   [Photo route  │             │
│  │    de poule]    │           │    réparée]     │             │
│  │                 │           │                 │             │
│  └─────────────────┘           └─────────────────┘             │
│  25/01/2026                     29/01/2026                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. Intégrations

### Calendrier

| Plateforme | Type | Fonctionnalité |
|------------|------|----------------|
| Outlook | Export .ics + sync | Planning interventions |
| Google Calendar | API sync | Planning interventions |

### QR Codes

- Scan QR sur équipement → Pré-remplissage du signalement
- Lien vers fiche équipement dans geoclic_data

---

## Annexes

### A. Priorités de développement (suggestion)

1. **Phase 1** : Catégories à 2 niveaux + interface tuiles
2. **Phase 2** : Détection doublons
3. **Phase 3** : Services et affectation
4. **Phase 4** : geoclic_services desktop
5. **Phase 5** : Timeline citoyen + photo avant/après
6. **Phase 6** : geoclic_services PWA mobile
7. **Phase 7** : Intégration calendrier + SLA

### B. Technologies

| Module | Stack |
|--------|-------|
| geoclic_demandes | Vue 3 + TypeScript + Pinia |
| geoclic_services | Vue 3 + TypeScript + Pinia |
| geoclic_services PWA | Vue 3 + Vite PWA plugin |
| API | FastAPI + PostgreSQL + PostGIS |

### C. Historique du document

| Date | Version | Auteur | Modifications |
|------|---------|--------|---------------|
| 31/01/2026 | 1.0 | - | Création initiale |

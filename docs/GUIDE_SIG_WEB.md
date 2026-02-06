# Guide Utilisateur - GéoClic SIG Web

**Application cartographique de la Suite GéoClic**
*Version 14 - Janvier 2026*

---

## Accès

URL : `https://votre-domaine.fr/sig/`

---

## Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Projet ▼]  [Couches ▼]  [Stats]          Barre d'outils          [? Aide] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                                                                              │
│                           CARTE INTERACTIVE                                  │
│                                                                              │
│                                                                              │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Plan IGN] [Ortho] [Cadastre] [Carte] [Historique]     Sélection fond      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fonds de Carte IGN

GéoClic SIG utilise les fonds de carte gratuits de l'IGN Géoplateforme :

| Fond | Description | Usage |
|------|-------------|-------|
| **Plan IGN** | Carte routière et administrative | Navigation générale |
| **Ortho** | Photographie aérienne | Analyse terrain |
| **Cadastre** | Parcelles cadastrales | Délimitation propriétés |
| **Carte** | Carte topographique | Relief et hydrographie |
| **Historique** | Photos anciennes | Comparaison temporelle |

**Pour changer de fond :** Cliquez sur le bouton correspondant en bas de l'écran.

---

## Barre d'Outils

### Navigation

| Outil | Icône | Description | Raccourci |
|-------|-------|-------------|-----------|
| Navigation | Curseur | Déplacer et zoomer la carte | N |
| Géolocalisation | GPS | Centrer sur votre position | G |

### Création d'entités

| Outil | Description | Raccourci | Comment terminer |
|-------|-------------|-----------|------------------|
| Point | Créer un point | P | Clic simple |
| Ligne | Créer une polyligne | L | Échap pour terminer |
| Polygone | Créer un polygone | O | Échap pour terminer |
| Série | Points successifs | S | Échap pour terminer |

### Outils de mesure

| Outil | Description | Raccourci | Comment terminer |
|-------|-------------|-----------|------------------|
| Distance | Mesurer une distance | D | Échap pour terminer |
| Surface | Mesurer une aire | A | Échap pour terminer |

### Édition

| Outil | Description | Raccourci |
|-------|-------------|-----------|
| Édition | Sélectionner et modifier | E |
| Périmètre | Créer une zone | Z |

---

## Créer des Entités

### Créer un point

1. Cliquez sur l'outil **Point** (ou appuyez sur `P`)
2. Cliquez sur la carte à l'endroit souhaité
3. Un formulaire s'ouvre pour saisir les propriétés
4. Validez

### Créer une ligne

1. Cliquez sur l'outil **Ligne** (ou appuyez sur `L`)
2. Cliquez pour placer chaque sommet
3. Appuyez sur **Échap** pour terminer
4. Remplissez le formulaire de propriétés

### Créer un polygone

1. Cliquez sur l'outil **Polygone** (ou appuyez sur `O`)
2. Cliquez pour placer chaque sommet
3. Appuyez sur **Échap** pour terminer et fermer automatiquement
4. Remplissez le formulaire de propriétés

### Mode Série (points successifs)

1. Cliquez sur l'outil **Série** (ou appuyez sur `S`)
2. Cliquez pour placer des points successivement
3. Chaque point ouvre un formulaire rapide
4. Appuyez sur **Échap** pour quitter le mode série

---

## Outils de Mesure

### Mesurer une distance

1. Cliquez sur l'outil **Distance** (ou appuyez sur `D`)
2. Cliquez pour placer les points de mesure
3. La distance totale s'affiche en temps réel
4. Appuyez sur **Échap** pour terminer

**Affichage :**
- < 1000m : affiché en mètres (ex: "450.5 m")
- >= 1000m : affiché en kilomètres (ex: "2.35 km")

### Mesurer une surface

1. Cliquez sur l'outil **Surface** (ou appuyez sur `A`)
2. Cliquez pour dessiner le périmètre
3. L'aire s'affiche en temps réel
4. Appuyez sur **Échap** pour terminer

**Affichage :**
- < 10000 m² : affiché en m² (ex: "1250.5 m²")
- >= 10000 m² : affiché en hectares (ex: "1.25 ha")

---

## Gestion des Projets

### Sélectionner un projet

1. Cliquez sur le sélecteur **Projet** en haut à gauche
2. Choisissez parmi les projets disponibles
3. Les données du projet se chargent automatiquement

### Visualiser plusieurs projets

Les données de plusieurs projets peuvent être affichées simultanément via le panneau des couches.

---

## Panneau des Couches

### Ouvrir le panneau

Cliquez sur **Couches** dans la barre supérieure.

### Gérer la visibilité

- Cochez/décochez une couche pour l'afficher/masquer
- Les couches sont groupées par type : Points, Lignes, Polygones

### Supprimer une couche

Cliquez sur l'icône de suppression à côté de la couche (couches importées uniquement).

---

## Import GeoJSON

### Méthode 1 : Drag & Drop

1. Glissez un fichier `.geojson` ou `.json` directement sur la carte
2. La couche est automatiquement ajoutée

### Méthode 2 : Bouton Import

1. Cliquez sur le bouton d'import dans la barre d'outils
2. Sélectionnez votre fichier GeoJSON
3. La couche est ajoutée avec un nom par défaut

**Formats supportés :** GeoJSON, JSON avec FeatureCollection

---

## Périmètres / Zones

### Créer un périmètre

1. Cliquez sur l'outil **Périmètre** (ou appuyez sur `Z`)
2. Dessinez le contour de la zone
3. Appuyez sur **Échap** pour terminer
4. Nommez votre périmètre

### Gérer les périmètres

Les périmètres créés apparaissent dans le panneau des couches et peuvent être :
- Affichés/masqués
- Renommés
- Supprimés

---

## Statistiques

Cliquez sur **Stats** pour ouvrir le tableau de bord :

- Nombre total de points
- Nombre de lignes
- Nombre de polygones
- Nombre de couches actives
- Dernière mise à jour

---

## Édition des Propriétés

### Modifier une entité

1. Activez l'outil **Édition** (ou appuyez sur `E`)
2. Cliquez sur une entité sur la carte
3. Le panneau de propriétés s'ouvre
4. Modifiez les valeurs
5. Cliquez sur **Enregistrer**

### Propriétés disponibles

Selon le type de lexique configuré :
- Nom
- Type
- Description
- Champs dynamiques (texte, nombre, date, liste...)

---

## Raccourcis Clavier

| Touche | Action |
|--------|--------|
| `N` | Mode navigation |
| `P` | Outil point |
| `L` | Outil ligne |
| `O` | Outil polygone |
| `S` | Mode série |
| `E` | Mode édition |
| `D` | Mesure distance |
| `A` | Mesure surface |
| `Z` | Outil périmètre |
| `G` | Géolocalisation |
| `Échap` | Terminer le dessin / Annuler |
| `?` ou `H` | Afficher l'aide |

---

## Conseils d'utilisation

### Navigation efficace

- Utilisez la molette de la souris pour zoomer
- Maintenez le clic gauche pour déplacer la carte
- Double-cliquez pour zoomer rapidement

### Précision du dessin

- Zoomez suffisamment avant de dessiner
- Utilisez le fond **Ortho** pour plus de précision
- Combinez avec le **Cadastre** pour les limites de parcelles

### Organisation

- Créez des périmètres pour délimiter vos zones de travail
- Utilisez le sélecteur de projet pour isoler les données
- Exportez régulièrement vos données

---

## Dépannage

### La carte ne s'affiche pas

1. Vérifiez votre connexion internet
2. Rafraîchissez la page (F5)
3. Videz le cache du navigateur

### Les fonds IGN ne chargent pas

Les services IGN Géoplateforme sont gratuits mais peuvent être temporairement indisponibles.
Essayez un autre fond de carte.

### Le GPS ne fonctionne pas

1. Autorisez la géolocalisation dans votre navigateur
2. Vérifiez que vous êtes en HTTPS (requis pour le GPS)

### Les données ne se chargent pas

1. Vérifiez que l'API est accessible
2. Sélectionnez un projet dans le sélecteur
3. Consultez les logs (F12 > Console)

---

## Support

- Documentation API : `https://votre-domaine.fr/api/docs`
- GitHub : https://github.com/fredco30/GeoClic_Suite

---

*GéoClic SIG Web V14 - Guide Utilisateur*

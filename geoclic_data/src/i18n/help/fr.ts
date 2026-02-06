/**
 * Contenu d'aide en français pour GéoClic Data
 * Documentation complète de toutes les pages et fonctionnalités
 */

import type { HelpContent } from './index'

const helpContentFr: HelpContent = {
  pages: {
    // ==========================================
    // PAGE CONNEXION
    // ==========================================
    login: {
      title: "Connexion",
      icon: "🔐",
      sections: [
        {
          title: "Accéder à votre compte",
          content: `Pour vous connecter à GéoClic Data, vous avez besoin de :

• **Email** : L'adresse email associée à votre compte
• **Mot de passe** : Votre mot de passe personnel (minimum 4 caractères)

Saisissez vos identifiants puis cliquez sur **Se connecter**.`
        },
        {
          title: "Problèmes de connexion",
          content: `Si vous ne parvenez pas à vous connecter :

• Vérifiez que votre adresse email est correcte
• Assurez-vous que le verrouillage majuscule (Caps Lock) est désactivé
• Contactez votre administrateur si vous avez oublié votre mot de passe
• Si le message "Identifiants incorrects" apparaît, vérifiez vos informations

**Note** : Après plusieurs tentatives échouées, votre compte peut être temporairement bloqué.`
        }
      ]
    },

    // ==========================================
    // TABLEAU DE BORD
    // ==========================================
    dashboard: {
      title: "Tableau de bord",
      icon: "📊",
      sections: [
        {
          title: "Vue d'ensemble",
          content: `Le tableau de bord est votre **centre de contrôle**. Il vous donne une vue synthétique de l'activité et des données de votre patrimoine.

Vous y trouverez les statistiques clés, les graphiques d'analyse et les derniers points créés.`
        },
        {
          title: "Statistiques principales",
          content: `Les **4 cartes statistiques** en haut de page affichent :

• **Points au total** : Nombre total de points d'inventaire dans la base
• **Ce mois-ci** : Points créés durant le mois en cours
• **Utilisateurs actifs** : Nombre d'utilisateurs ayant un compte actif
• **Projets** : Nombre de projets configurés

Ces chiffres se mettent à jour automatiquement.`
        },
        {
          title: "Graphiques d'analyse",
          content: `Deux graphiques vous permettent de visualiser vos données :

**Répartition par catégorie** (graphique circulaire)
Montre la distribution de vos points par famille/catégorie. Utile pour identifier les types d'équipements les plus inventoriés.

**Activité des 30 derniers jours** (graphique linéaire)
Affiche l'évolution du nombre de points créés jour par jour. Permet de suivre le rythme de collecte.`
        },
        {
          title: "Actions rapides",
          content: `La colonne de droite propose des **raccourcis** vers les fonctions courantes :

• **Nouveau point** : Ouvre la carte pour créer un point
• **Importer données** : Charge des données depuis un fichier
• **Exporter données** : Télécharge vos données
• **Générer QR codes** : Crée des étiquettes pour vos équipements

Cliquez sur le bouton **Actualiser** pour recharger toutes les données.`
        }
      ]
    },

    // ==========================================
    // LISTE DES POINTS
    // ==========================================
    points: {
      title: "Liste des points",
      icon: "📍",
      sections: [
        {
          title: "Présentation",
          content: `Cette page affiche l'**ensemble des points** de votre inventaire sous forme de tableau.

Chaque ligne représente un point avec ses informations principales : nom, catégorie, projet, date de création.`
        },
        {
          title: "Recherche et filtres",
          content: `Utilisez les outils de recherche pour trouver rapidement vos points :

**Barre de recherche**
Tapez un nom, une description ou un mot-clé. La recherche s'effectue automatiquement après quelques caractères.

**Filtre par projet**
Sélectionnez un projet pour n'afficher que ses points.

**Filtre par catégorie**
Choisissez une catégorie pour filtrer les résultats.

Pour réinitialiser un filtre, cliquez sur la croix (×) du champ.`
        },
        {
          title: "Export des données",
          content: `Trois boutons d'export sont disponibles :

• **CSV** : Tableur compatible Excel, LibreOffice, Google Sheets
• **GeoJSON** : Format géographique pour SIG (QGIS, MapBox)
• **Photos** : Archive ZIP contenant toutes les photos

Les exports tiennent compte des filtres actifs : si vous filtrez par projet, seuls les points de ce projet seront exportés.`
        },
        {
          title: "Navigation et pagination",
          content: `Le tableau est paginé pour faciliter la navigation :

• Utilisez les flèches **< >** pour naviguer entre les pages
• Le nombre de résultats total est affiché en bas
• 50 points sont affichés par page par défaut

**Cliquez sur une ligne** pour accéder au détail complet du point.`
        },
        {
          title: "Comprendre les colonnes",
          content: `Le tableau affiche les colonnes suivantes :

• **Nom** : Nom du point avec son icône de catégorie
• **Description** : Description courte (si renseignée)
• **Projet** : Projet auquel appartient le point
• **Catégorie** : Classification dans le lexique
• **Date création** : Date et heure de création
• **Actions** : Bouton pour voir le détail`
        }
      ]
    },

    // ==========================================
    // CARTOGRAPHIE
    // ==========================================
    carte: {
      title: "Cartographie",
      icon: "🗺️",
      sections: [
        {
          title: "Présentation de la carte",
          content: `La carte interactive affiche l'**emplacement géographique** de tous vos points d'inventaire.

Chaque point est représenté par un marqueur coloré selon sa catégorie. Cliquez sur un marqueur pour voir ses informations.`
        },
        {
          title: "Navigation sur la carte",
          content: `**Déplacement**
• Cliquez et faites glisser pour vous déplacer
• Utilisez la molette de la souris pour zoomer/dézoomer
• Les boutons +/- permettent aussi de zoomer

**Clusters**
Quand plusieurs points sont proches, ils sont regroupés en cluster avec un nombre. Cliquez dessus pour zoomer et les séparer.`
        },
        {
          title: "Filtres et recherche",
          content: `La barre d'outils permet de filtrer les points affichés :

• **Projet** : Filtre par projet
• **Catégorie** : Filtre par type d'équipement
• **Recherche** : Recherche textuelle
• **Zone** : Filtre par zone géographique (si configuré)

Le **style de carte** peut être changé : vue Streets (rues) ou Satellite.`
        },
        {
          title: "Créer un nouveau point",
          content: `Pour créer un point depuis la carte :

1. Cliquez sur le bouton **Nouveau point**
2. Un message vous invite à cliquer sur la carte
3. Cliquez à l'emplacement souhaité
4. Le système vérifie s'il existe un doublon à proximité
5. Si un doublon est détecté, choisissez : créer quand même, annuler, ou voir le point existant
6. Remplissez le formulaire de création
7. Validez pour enregistrer le point`
        },
        {
          title: "Détection des doublons",
          content: `Pour éviter les doublons, le système vérifie automatiquement si un point existe déjà à proximité (rayon de 5 mètres par défaut).

Si un doublon potentiel est détecté :
• **Distance** : La distance avec le point existant est affichée
• **Créer quand même** : Ignore l'alerte et crée le point
• **Annuler** : Abandonne la création
• **Voir le point existant** : Ouvre le détail du point trouvé

Cette vérification évite de créer plusieurs fois le même équipement.`
        },
        {
          title: "Affichage des zones",
          content: `Si des zones géographiques sont définies (quartiers, secteurs), vous pouvez les afficher sur la carte.

• Cliquez sur **Afficher les zones** pour les superposer
• Les zones apparaissent en polygones semi-transparents
• Cliquez sur **Masquer les zones** pour les retirer

Le filtre **Zone** permet de n'afficher que les points d'une zone spécifique.`
        }
      ]
    },

    // ==========================================
    // LEXIQUE
    // ==========================================
    lexique: {
      title: "Lexique",
      icon: "📖",
      sections: [
        {
          title: "Qu'est-ce que le lexique ?",
          content: `Le lexique est le **référentiel des catégories** utilisées pour classer vos points d'inventaire.

Il définit une arborescence hiérarchique : Famille → Type → Sous-type → Variante → Détail → Précision.

**Cette page est en lecture seule.** Pour modifier le lexique, rendez-vous dans la configuration d'un projet.`
        },
        {
          title: "Navigation dans l'arborescence",
          content: `L'arborescence à gauche affiche toutes les catégories :

• Cliquez sur une flèche **▶** pour déplier/replier
• Utilisez **Tout déplier** pour voir l'ensemble
• Utilisez **Tout replier** pour réduire l'affichage
• Cliquez sur une catégorie pour voir son détail à droite`
        },
        {
          title: "Détail d'une catégorie",
          content: `Quand vous sélectionnez une catégorie, le panneau de droite affiche :

• **Icône et libellé** : Identification visuelle
• **Code** : Code unique de la catégorie
• **Niveau** : Position dans la hiérarchie (Famille, Type, etc.)
• **Description** : Texte explicatif (si renseigné)
• **Statut** : Actif ou Inactif
• **Champs dynamiques** : Liste des champs personnalisés associés`
        },
        {
          title: "Champs dynamiques",
          content: `Chaque catégorie peut avoir des **champs personnalisés** pour saisir des informations spécifiques.

Exemples de champs :
• Texte : Numéro de série, marque
• Nombre : Hauteur, puissance
• Date : Date d'installation
• Liste déroulante : État, matériau
• Photo : Image de l'équipement

Les champs marqués **Obligatoire** (en rouge) doivent être renseignés lors de la création d'un point.`
        }
      ]
    },

    // ==========================================
    // LISTE DES PROJETS
    // ==========================================
    projets: {
      title: "Gestion des projets",
      icon: "📁",
      sections: [
        {
          title: "Qu'est-ce qu'un projet ?",
          content: `Un projet regroupe un ensemble de points d'inventaire autour d'une thématique ou d'un périmètre.

Exemples de projets :
• Éclairage Public
• Mobilier Urbain
• Espaces Verts
• Inventaire 2024

Chaque projet possède son propre lexique de catégories.`
        },
        {
          title: "Liste des projets",
          content: `La page affiche vos projets sous forme de **cartes** :

• **Titre** : Nom du projet
• **Statut** : Badge "Actif" ou "Archivé"
• **Description** : Texte descriptif
• **Statistiques** : Nombre de points et d'utilisateurs

Les projets archivés restent visibles mais ne peuvent plus recevoir de nouveaux points.`
        },
        {
          title: "Créer un projet avec un modèle",
          content: `Pour créer un projet avec des catégories pré-définies :

1. Cliquez sur **Créer un projet**
2. Renseignez le **nom** (obligatoire)
3. Ajoutez une **description** (optionnel)
4. Choisissez si le projet est **actif**
5. Sélectionnez un **modèle** dans la liste

**Modèles disponibles** : Éclairage Public, Mobilier Urbain, Espaces Verts, Voirie, Aires de Jeux, Réseaux, et bien d'autres.

Le modèle pré-remplit automatiquement les catégories et champs courants du domaine choisi. Vous pourrez ensuite les personnaliser.`
        },
        {
          title: "Créer un projet vide (sans modèle)",
          content: `Pour créer un projet entièrement personnalisé :

1. Cliquez sur **Créer un projet**
2. Renseignez le **nom** (obligatoire)
3. Ajoutez une **description** (optionnel)
4. Choisissez si le projet est **actif**
5. **Ne sélectionnez aucun modèle** (laissez le champ vide ou "Aucun")
6. Validez la création

Vous obtiendrez un projet **vide**, sans catégories. Cliquez ensuite sur **Configurer** pour :
• Ajouter vos propres **familles** et **catégories**
• Créer des **champs personnalisés** adaptés à vos besoins
• Organiser la structure hiérarchique à votre convenance

Cette méthode est idéale si aucun modèle ne correspond à votre besoin ou si vous souhaitez une structure sur mesure.`
        },
        {
          title: "Actions sur un projet",
          content: `Chaque carte projet propose des actions :

• **Configurer** : Ouvre le détail pour gérer les catégories et champs
• **Infos** (icône crayon) : Modifie le nom et la description
• **Supprimer** (icône poubelle) : Supprime le projet

**Attention** : La suppression d'un projet supprime aussi tous ses points. Cette action est irréversible.`
        }
      ]
    },

    // ==========================================
    // DÉTAIL PROJET
    // ==========================================
    projetDetail: {
      title: "Configuration du projet",
      icon: "⚙️",
      sections: [
        {
          title: "Vue d'ensemble",
          content: `Cette page permet de **configurer entièrement** votre projet :

• Définir la structure des catégories (lexique)
• Créer des champs personnalisés
• Configurer des champs conditionnels
• Organiser la hiérarchie des éléments
• Consulter les statistiques

Le bouton **Paramètres** en haut à droite permet de modifier le nom et la description du projet.`
        },
        {
          title: "Statistiques rapides",
          content: `Les 4 cartes en haut affichent :

• **Familles** : Nombre de catégories de niveau 1
• **Total éléments** : Nombre total de catégories (tous niveaux)
• **Total champs** : Nombre de champs dynamiques créés
• **Points collectés** : Nombre de points associés au projet`
        },
        {
          title: "Structure hiérarchique",
          content: `Les catégories sont organisées en **6 niveaux** maximum :

• **Famille** : Niveau supérieur (ex: Luminaires)
• **Type** : Grande catégorie (ex: Candélabres)
• **Sous-type** : Catégorie détaillée (ex: Candélabre simple)
• **Variante** : Déclinaison (ex: 4 mètres)
• **Détail** : Précision supplémentaire
• **Précision** : Niveau le plus fin

Chaque niveau est affiché dans une colonne. Cliquez sur un élément pour le sélectionner et voir/modifier ses propriétés.`
        },
        {
          title: "Modifier ou supprimer une catégorie",
          content: `Pour **modifier** ou **supprimer** un élément de la structure (Famille, Type, Sous-type, etc.) :

**Au survol de chaque élément**, deux boutons apparaissent :

• **Crayon (Modifier)** : Ouvre une fenêtre pour changer le nom, l'icône et la couleur
• **Poubelle (Supprimer)** : Supprime l'élément après confirmation

**Dans le dialogue de modification** :
• Le **Code** est affiché mais non modifiable (identifiant unique)
• Vous pouvez changer le **Libellé** (nom affiché)
• Vous pouvez choisir une nouvelle **Icône** par catégorie
• Vous pouvez changer la **Couleur** du marqueur

**Attention** : Supprimer une catégorie parente supprime aussi tous ses enfants.`
        },
        {
          title: "Ajouter une catégorie",
          content: `Pour créer une nouvelle catégorie :

1. Cliquez sur **Ajouter famille** (niveau 1) ou sur le **+** dans une colonne
2. Remplissez le formulaire :
   • **Code** : Identifiant unique (ex: LUM_CAND)
   • **Libellé** : Nom affiché (ex: Candélabre)
   • **Icône** : Choisissez une icône
   • **Couleur** : Couleur du marqueur sur la carte
3. Validez pour créer la catégorie

Pour créer un sous-niveau, sélectionnez d'abord le parent puis cliquez sur **+** dans la colonne suivante.`
        },
        {
          title: "Champs dynamiques",
          content: `Chaque catégorie peut avoir des **champs personnalisés** pour collecter des données spécifiques.

**Types de champs disponibles** :
• **Texte** : Saisie libre
• **Nombre** : Valeur numérique (avec min/max optionnel)
• **Date** : Sélecteur de date
• **Liste déroulante** : Choix parmi des options prédéfinies
• **Multi-sélection** : Plusieurs choix possibles
• **Photo** : Prise de photo ou import d'image
• **Fichier** : Pièce jointe
• **Géométrie** : Tracé sur carte
• **Slider** : Curseur numérique
• **Couleur** : Sélecteur de couleur
• **Signature** : Zone de signature manuscrite
• **QR Code** : Lecture de QR code
• **Calculé** : Valeur calculée automatiquement`
        },
        {
          title: "Champs conditionnels",
          content: `Les **champs conditionnels** permettent d'afficher un champ uniquement lorsqu'une condition est remplie.

**Exemple d'utilisation** :
Vous avez un champ "Modèle" avec les options "Glasdon", "JCDecaux", "Autre".
Vous voulez afficher un champ "État Glasdon" uniquement si l'utilisateur choisit "Glasdon".

**Pour créer un champ conditionnel** :
1. Ajoutez ou modifiez un champ
2. Activez l'option **"Champ conditionnel"**
3. Sélectionnez le **champ déclencheur** (ex: "Modèle")
4. Choisissez l'**opérateur** de comparaison :
   • **égal à** : le champ doit avoir exactement cette valeur
   • **différent de** : le champ doit avoir une autre valeur
   • **contient** : le champ doit contenir ce texte
   • **non vide** : le champ doit être renseigné
5. Saisissez la **valeur** attendue (ex: "Glasdon")

**Résultat** : Le champ n'apparaîtra dans le formulaire que si la condition est remplie.

**Indication visuelle** : Les champs conditionnels affichent un badge **"Conditionnel"** dans la liste.`
        },
        {
          title: "Organiser les éléments",
          content: `Vous pouvez **réorganiser** les catégories et champs :

**Drag & Drop**
• Glissez-déposez un élément pour changer son ordre
• Maintenez enfoncé et déplacez vers le haut/bas

**Modifier un champ**
• Cliquez sur le champ dans la liste
• Modifiez ses propriétés dans le dialogue qui s'ouvre
• Validez pour enregistrer les changements

**Supprimer un champ**
• Cliquez sur le bouton supprimer (poubelle) du champ
• Confirmez la suppression

**Héritage des champs**
Les champs définis sur une catégorie parente sont automatiquement hérités par les catégories enfants. Ils apparaissent en grisé avec la mention "hérité de [Parent]".`
        }
      ]
    },

    // ==========================================
    // ZONES - LISTE
    // ==========================================
    zones: {
      title: "Gestion des zones",
      icon: "🗺️",
      sections: [
        {
          title: "Qu'est-ce qu'une zone ?",
          content: `Les zones sont des **périmètres géographiques** qui permettent de découper votre territoire.

Exemples :
• Quartiers d'une commune
• Secteurs de maintenance
• Zones de compétence

Les zones permettent ensuite de filtrer les points par localisation.`
        },
        {
          title: "Liste des zones",
          content: `Le tableau affiche toutes les zones définies :

• **Nom** : Nom de la zone
• **Type** : Quartier, Secteur, Commune, etc.
• **Code** : Code court (ex: Q01, SEC-NORD)
• **Points** : Nombre de points dans cette zone
• **Actions** : Éditer, Dupliquer, Supprimer`
        },
        {
          title: "Créer une zone",
          content: `Deux méthodes pour créer des zones :

**Méthode manuelle**
1. Cliquez sur **Créer une zone**
2. Dessinez le contour sur la carte
3. Nommez et enregistrez la zone

**Import IRIS**
1. Cliquez sur **Importer IRIS**
2. Les zones INSEE sont automatiquement chargées
3. Adaptez les noms si nécessaire

L'import IRIS est utile pour récupérer les découpages officiels (quartiers INSEE).`
        }
      ]
    },

    // ==========================================
    // ZONES - ÉDITION
    // ==========================================
    zoneEdit: {
      title: "Création/édition de zone",
      icon: "✏️",
      sections: [
        {
          title: "Dessiner une zone",
          content: `Pour définir le périmètre de votre zone :

1. Activez le **mode dessin** (bouton crayon)
2. Cliquez sur la carte pour poser le premier point
3. Continuez à cliquer pour tracer le contour
4. **Double-cliquez** pour terminer le tracé

Le polygone se ferme automatiquement.`
        },
        {
          title: "Fonds de carte",
          content: `Trois fonds de carte sont disponibles pour vous aider :

• **OSM** : OpenStreetMap (vue standard)
• **Satellite** : Imagerie aérienne
• **Cadastre** : Parcelles cadastrales

Utilisez le cadastre pour un tracé précis suivant les limites de propriété.`
        },
        {
          title: "Outils de dessin",
          content: `La barre d'outils propose :

• **Mode dessin** : Active/désactive le tracé
• **Annuler** (Undo) : Retire le dernier point placé
• **Effacer** (Clear) : Supprime tout le tracé

En mode édition, vous pouvez cliquer-glisser les sommets existants pour ajuster la forme.`
        },
        {
          title: "Enregistrer la zone",
          content: `Une fois le tracé terminé :

1. Cliquez sur **Enregistrer**
2. Renseignez :
   • **Nom** : Nom de la zone (obligatoire)
   • **Type** : Quartier, Secteur, Commune...
   • **Code** : Identifiant court (optionnel)
3. Validez

Le bouton Enregistrer n'est actif que si une géométrie est tracée.`
        }
      ]
    },

    // ==========================================
    // UTILISATEURS
    // ==========================================
    utilisateurs: {
      title: "Gestion des utilisateurs",
      icon: "👥",
      sections: [
        {
          title: "Vue d'ensemble",
          content: `Cette page permet de gérer les **comptes utilisateurs** de l'application.

**Accès réservé aux administrateurs.**

Vous pouvez créer, modifier et supprimer des comptes, ainsi que définir les rôles et permissions.`
        },
        {
          title: "Les 4 rôles",
          content: `Chaque utilisateur se voit attribuer un rôle :

• **Administrateur** (rouge) : Accès complet à toutes les fonctionnalités, y compris la gestion des utilisateurs et les paramètres système.

• **Modérateur** (orange) : Gestion des points et validation des contributions. Peut modifier et supprimer des points.

• **Contributeur** (vert) : Création et modification de points. Ne peut pas supprimer ni accéder aux paramètres.

• **Lecteur** (bleu) : Consultation uniquement. Ne peut pas créer ni modifier de données.`
        },
        {
          title: "Créer un utilisateur",
          content: `Pour ajouter un nouvel utilisateur :

1. Cliquez sur **Nouvel utilisateur**
2. Remplissez les champs obligatoires :
   • **Email** : Adresse email (servira d'identifiant)
   • **Mot de passe** : Minimum 6 caractères
   • **Prénom** et **Nom**
   • **Rôle** : Choisissez parmi les 4 rôles
3. Optionnel : Définissez les permissions granulaires
4. Validez

L'utilisateur recevra ses identifiants par email (si configuré).`
        },
        {
          title: "Permissions granulaires",
          content: `Au-delà du rôle, vous pouvez restreindre l'accès :

**Par projet**
Sélectionnez les projets auxquels l'utilisateur a accès. S'il n'a accès à aucun projet, il ne verra aucune donnée.

**Par catégorie**
Limitez l'accès à certaines catégories du lexique.

**Note** : Les administrateurs ont automatiquement accès à tout, ces restrictions ne s'appliquent pas à eux.`
        },
        {
          title: "Actions sur un utilisateur",
          content: `Le tableau propose plusieurs actions :

• **Éditer** (crayon) : Modifier les informations et le rôle
• **Activer/Désactiver** : Un utilisateur désactivé ne peut plus se connecter mais son compte est conservé
• **Supprimer** : Supprime définitivement le compte

**Réinitialiser le mot de passe**
En mode édition, un bouton permet de générer un nouveau mot de passe temporaire.`
        }
      ]
    },

    // ==========================================
    // QR CODES
    // ==========================================
    qrcodes: {
      title: "Génération de QR codes",
      icon: "📱",
      sections: [
        {
          title: "À quoi servent les QR codes ?",
          content: `Les QR codes permettent d'**identifier rapidement** un équipement sur le terrain.

Collez une étiquette sur l'équipement, scannez-la avec un smartphone, et accédez directement à sa fiche dans l'application.

C'est idéal pour la maintenance, l'inventaire ou le signalement d'anomalies.`
        },
        {
          title: "Sélectionner les points",
          content: `Pour générer des QR codes :

1. Choisissez un **Projet** dans le filtre
2. Sélectionnez une **Catégorie** (optionnel)
3. Cliquez sur **Charger les points**
4. La liste des points apparaît à droite
5. Cochez les points souhaités (ou "Sélectionner tout")
6. Lancez la génération`
        },
        {
          title: "Format des étiquettes",
          content: `Configurez l'apparence des étiquettes :

**Taille**
• **Petit** (2 cm) : Discret, pour petits équipements
• **Moyen** (4 cm) : Standard, bonne lisibilité
• **Grand** (6 cm) : Pour affichage ou équipements volumineux

**Options d'affichage**
• ☑ Inclure le nom du point
• ☑ Inclure l'adresse/lieu
• ☑ Inclure le logo de la collectivité`
        },
        {
          title: "Formats de sortie",
          content: `Trois formats d'export sont disponibles :

• **PDF Planche A4** : 24 étiquettes par page, prêt à imprimer sur papier adhésif
• **PDF Individuels** : Une page par étiquette, pour impression grand format
• **ZIP Images PNG** : Fichiers images individuels pour intégration dans d'autres documents

Une fois généré, le fichier se télécharge automatiquement.`
        }
      ]
    },

    // ==========================================
    // EXPORTS
    // ==========================================
    exports: {
      title: "Export des données",
      icon: "📤",
      sections: [
        {
          title: "Exporter vos données",
          content: `Cette page permet de **télécharger vos données** dans différents formats pour les utiliser dans d'autres outils.

Choisissez vos filtres à gauche, puis cliquez sur le format souhaité pour lancer le téléchargement.`
        },
        {
          title: "Filtres disponibles",
          content: `Affinez les données exportées :

• **Projet** : Exporte uniquement les points d'un projet
• **Catégorie** : Limite à une catégorie spécifique
• **Date début / fin** : Exporte les points créés dans une période

Si aucun filtre n'est appliqué, toutes les données sont exportées.`
        },
        {
          title: "Formats disponibles",
          content: `**CSV (Excel)**
Tableur avec colonnes : ID, Nom, Catégorie, Projet, Latitude, Longitude, et données techniques.
Compatible : Excel, LibreOffice Calc, Google Sheets.

**GeoJSON**
Format géospatial standard. Chaque point devient une "Feature" avec ses propriétés.
Compatible : QGIS, MapBox, Leaflet, Geoportail.

**Shapefile**
Archive ZIP contenant .shp, .dbf, .shx. Format historique des SIG.
Compatible : ArcGIS, QGIS, MapInfo.

**KML**
Format Google Earth avec styles et couleurs par catégorie.
Compatible : Google Earth, Google Maps, GPS.

**Excel avancé**
Fichier .xlsx avec mise en forme et plusieurs onglets (points, statistiques).`
        }
      ]
    },

    // ==========================================
    // IMPORTS
    // ==========================================
    imports: {
      title: "Import de données",
      icon: "📥",
      sections: [
        {
          title: "Importer des données",
          content: `Cette page permet de **charger des données** depuis un fichier ou une base PostGIS externe.

L'import se fait en 3 étapes : choix du fichier, mapping des colonnes, exécution.`
        },
        {
          title: "Étape 1 : Fichier source",
          content: `**Formats acceptés**
• **CSV** : Fichier tableur avec séparateur virgule ou point-virgule
• **GeoJSON** : Fichier géographique standard
• **ZIP (Shapefile)** : Archive contenant les fichiers .shp, .dbf, .shx

**Configuration**
• Sélectionnez le **projet cible**
• Choisissez la **catégorie** pour les points importés

Cliquez sur **Suivant** pour passer au mapping.`
        },
        {
          title: "Étape 2 : Mapping des colonnes",
          content: `Associez les colonnes de votre fichier aux champs de l'application :

**Colonnes système**
• Nom du point
• Description
• Latitude (ou Y)
• Longitude (ou X)

**Champs personnalisés**
Les champs dynamiques de la catégorie cible apparaissent également.

Une prévisualisation des 10 premières lignes vous aide à vérifier le mapping.`
        },
        {
          title: "Étape 3 : Options et exécution",
          content: `Configurez les options d'import :

**Gestion des doublons**
• ☑ **Ignorer les doublons** : Ne crée pas de point si un existe déjà à proximité
• ☑ **Mettre à jour les existants** : Actualise les données du point existant

**Rayon de détection**
Définissez la distance (en mètres) pour considérer deux points comme doublons. Défaut : 5 mètres.

Cliquez sur **Lancer l'import**. Une barre de progression s'affiche.

**Résumé**
À la fin, un rapport indique : X créés, Y mis à jour, Z ignorés.`
        },
        {
          title: "Import PostGIS",
          content: `Si une connexion PostGIS est configurée (voir Paramètres), vous pouvez importer directement depuis une table de base de données.

1. Sélectionnez la **table source**
2. Mappez les colonnes
3. Ajoutez un filtre WHERE (optionnel)
4. Lancez l'import

Cette méthode est idéale pour synchroniser avec un SIG existant.`
        }
      ]
    },

    // ==========================================
    // ONEGEO SUITE
    // ==========================================
    ogs: {
      title: "OneGeo Suite",
      icon: "🌐",
      sections: [
        {
          title: "Qu'est-ce que OneGeo Suite ?",
          content: `OneGeo Suite (OGS) est une **passerelle de publication** vers le SIG de votre collectivité.

Elle permet de transférer les données validées de GéoClic Data vers votre système d'information géographique principal.`
        },
        {
          title: "Statistiques de publication",
          content: `Les cartes en haut affichent :

• **Tables OGS créées** : Nombre de tables publiées
• **Points publiés** : Total des points transférés
• **Points validés à publier** : En attente de publication
• **Points en attente validation** : Non encore validés`
        },
        {
          title: "Publier vers OGS",
          content: `Pour publier une catégorie :

1. Repérez la catégorie dans la liste
2. Vérifiez le nombre de points prêts
3. Cliquez sur **Publier**
4. La table OGS est créée/mise à jour

**Bouton "Tout publier"**
Publie toutes les catégories ayant des points validés en une seule opération.

Les tables publiées peuvent être supprimées via l'icône poubelle (cela ne supprime pas les données sources).`
        }
      ]
    },

    // ==========================================
    // PARAMÈTRES
    // ==========================================
    parametres: {
      title: "Paramètres",
      icon: "⚙️",
      sections: [
        {
          title: "Paramètres généraux",
          content: `Cette page regroupe les **configurations globales** de l'application.

Seuls les administrateurs peuvent modifier ces paramètres.`
        },
        {
          title: "Apparence",
          content: `Personnalisez l'interface :

• **Mode sombre** : Active le thème sombre (fond foncé, texte clair)
• **Langue** : Français, Anglais, Espagnol, Allemand

Le changement de langue s'applique immédiatement à toute l'interface.`
        },
        {
          title: "Cartographie",
          content: `Configurez les paramètres par défaut de la carte :

• **Style par défaut** : Streets (plan) ou Satellite
• **Niveau de zoom** : Zoom initial (1 = monde, 18 = rue)
• **Position par défaut** : Latitude et longitude du centre de la carte

Ces valeurs sont utilisées quand aucun point n'est sélectionné.`
        },
        {
          title: "PostGIS externe",
          content: `Connectez une base de données PostgreSQL/PostGIS externe pour les imports ou la synchronisation.

**Paramètres de connexion**
• **Hôte** : Adresse du serveur (localhost ou IP)
• **Port** : Port PostgreSQL (par défaut 5432)
• **Base de données** : Nom de la base
• **Utilisateur** : Compte PostgreSQL
• **Mot de passe** : Mot de passe du compte
• **Schéma** : Schéma cible (optionnel, défaut: public)

**Tester la connexion** vérifie que les paramètres sont corrects avant de sauvegarder.

**Note** : Cette configuration est technique, faites-vous accompagner par votre service informatique.`
        }
      ]
    },

    // ==========================================
    // PROFIL
    // ==========================================
    profil: {
      title: "Mon profil",
      icon: "👤",
      sections: [
        {
          title: "Informations personnelles",
          content: `Consultez et modifiez vos informations :

• **Prénom** et **Nom** : Votre identité
• **Email** : Votre adresse email (non modifiable)
• **Rôle** : Votre niveau d'accès (non modifiable)

Cliquez sur **Enregistrer** après toute modification.`
        },
        {
          title: "Changer de mot de passe",
          content: `Pour modifier votre mot de passe :

1. Saisissez votre **mot de passe actuel**
2. Entrez le **nouveau mot de passe** (minimum 6 caractères)
3. **Confirmez** le nouveau mot de passe
4. Cliquez sur **Changer le mot de passe**

Choisissez un mot de passe robuste mélangeant lettres, chiffres et caractères spéciaux.`
        },
        {
          title: "Informations du compte",
          content: `La section inférieure affiche :

• **Date de création** : Quand votre compte a été créé
• **Dernière connexion** : Date et heure de votre précédente connexion

Ces informations sont en lecture seule.`
        }
      ]
    },

    // ==========================================
    // DÉTAIL POINT PUBLIC
    // ==========================================
    pointDetail: {
      title: "Fiche équipement",
      icon: "📄",
      sections: [
        {
          title: "Accès à la fiche",
          content: `Cette page affiche les **informations publiques** d'un point d'inventaire.

Elle est accessible :
• En scannant le **QR code** collé sur l'équipement
• Via un **lien partagé**

Aucune connexion n'est requise pour consulter cette fiche.`
        },
        {
          title: "Informations affichées",
          content: `La fiche présente :

• **Photo** : Image de l'équipement (si disponible)
• **Nom** : Identifiant du point
• **Catégorie** : Type d'équipement avec icône et couleur
• **Description** : Détails complémentaires
• **Localisation** : Mini-carte avec position GPS
• **Coordonnées** : Latitude et longitude exactes
• **Données techniques** : Champs personnalisés renseignés`
        },
        {
          title: "Actions disponibles",
          content: `Deux boutons d'action :

• **Ouvrir dans Google Maps** : Lance la navigation vers l'équipement
• **Partager** : Copie le lien de la fiche dans le presse-papier

Le lien copié peut être envoyé par email, SMS ou tout autre moyen pour permettre à d'autres personnes de localiser l'équipement.`
        }
      ]
    }
  },

  // ==========================================
  // TOOLTIPS CONTEXTUELS
  // ==========================================
  tooltips: {
    // --- Projets ---
    projetNom: "Nom unique du projet, affiché dans les listes et filtres",
    projetDescription: "Description optionnelle pour expliquer l'objectif du projet",
    projetActif: "Un projet inactif n'accepte plus de nouveaux points mais reste consultable",
    projetTemplate: "Modèle prédéfini pour créer automatiquement les catégories et champs courants",

    // --- Lexique / Catégories ---
    categorieCode: "Identifiant unique de la catégorie (ex: MOB_BANC). Ne peut pas être modifié après création",
    categorieLibelle: "Nom affiché de la catégorie dans les listes et sur la carte",
    categorieIcone: "Icône représentant la catégorie (affichée sur les marqueurs de carte)",
    categorieCouleur: "Couleur du marqueur sur la carte et des badges dans l'interface",
    categorieParent: "Catégorie parente pour créer une hiérarchie (Famille > Type > Sous-type)",
    categorieNiveau: "Position dans la hiérarchie : 1=Famille, 2=Type, 3=Sous-type, etc.",
    categorieActif: "Une catégorie inactive ne peut plus être utilisée pour créer de nouveaux points",
    categorieDescription: "Texte explicatif pour aider les utilisateurs à choisir la bonne catégorie",

    // --- Champs dynamiques ---
    champNom: "Nom du champ affiché dans le formulaire de saisie",
    champType: "Type de donnée : texte, nombre, date, liste, photo, etc.",
    champObligatoire: "Si coché, le champ doit être renseigné pour créer un point",
    champOrdre: "Position du champ dans le formulaire (les champs sont triés par ordre croissant)",
    champOptions: "Options disponibles pour les champs de type liste ou multi-sélection (une par ligne)",
    champMin: "Valeur minimale autorisée (pour les champs numériques)",
    champMax: "Valeur maximale autorisée (pour les champs numériques)",
    champDefaut: "Valeur pré-remplie par défaut dans le formulaire",
    champCondition: "Affiche ce champ uniquement si une condition est remplie (champ conditionnel)",
    champConditionField: "Champ déclencheur : le champ dont la valeur sera testée pour afficher ou masquer ce champ",
    champConditionOperator: "Opérateur de comparaison : égal à, différent de, contient, ou non vide",
    champConditionValue: "Valeur attendue : la valeur que le champ déclencheur doit avoir pour afficher ce champ",
    champFormule: "Formule de calcul pour les champs de type 'calculé' (ex: {hauteur} * {largeur})",

    // --- Points ---
    pointNom: "Nom ou identifiant du point d'inventaire",
    pointDescription: "Description libre ou commentaire sur le point",
    pointLatitude: "Coordonnée GPS latitude (ex: 48.8566)",
    pointLongitude: "Coordonnée GPS longitude (ex: 2.3522)",
    pointProjet: "Projet auquel rattacher ce point",
    pointCategorie: "Catégorie du lexique pour classifier ce point",
    pointStatut: "État du point : actif, en maintenance, hors service, etc.",
    pointCondition: "État général de l'équipement : bon, moyen, mauvais",

    // --- Zones ---
    zoneNom: "Nom de la zone géographique (ex: Quartier Centre, Secteur Nord)",
    zoneType: "Type de découpage : quartier, secteur, commune, zone de maintenance",
    zoneCode: "Code court pour identifier la zone (ex: Q01, SEC-N)",
    zoneGeometrie: "Contour de la zone dessiné sur la carte",

    // --- Utilisateurs ---
    userEmail: "Adresse email utilisée comme identifiant de connexion",
    userPassword: "Mot de passe (minimum 6 caractères, mélangez lettres, chiffres et symboles)",
    userPrenom: "Prénom de l'utilisateur",
    userNom: "Nom de famille de l'utilisateur",
    userRole: "Niveau d'accès : Admin (tout), Modérateur (gestion), Contributeur (création), Lecteur (consultation)",
    userActif: "Un utilisateur inactif ne peut plus se connecter mais son compte est conservé",
    userPermissionsProjets: "Projets auxquels l'utilisateur a accès (vide = tous si admin, aucun sinon)",
    userPermissionsCategories: "Catégories que l'utilisateur peut utiliser (vide = toutes si admin)",

    // --- QR Codes ---
    qrProjet: "Projet contenant les points pour lesquels générer des QR codes",
    qrCategorie: "Filtrer les points par catégorie (optionnel)",
    qrTaille: "Dimension de l'étiquette : Petit (2cm), Moyen (4cm), Grand (6cm)",
    qrInclureNom: "Afficher le nom du point sous le QR code",
    qrInclureAdresse: "Afficher l'adresse ou le lieu sous le QR code",
    qrIncludeLogo: "Ajouter le logo de la collectivité sur l'étiquette",
    qrFormat: "Format de sortie : PDF planche A4, PDF individuels, ou images PNG",

    // --- Exports ---
    exportProjet: "Exporter uniquement les points de ce projet (vide = tous)",
    exportCategorie: "Exporter uniquement les points de cette catégorie (vide = toutes)",
    exportDateDebut: "Date de création minimale des points à exporter",
    exportDateFin: "Date de création maximale des points à exporter",
    exportFormat: "Format du fichier : CSV, GeoJSON, Shapefile, KML, Excel",

    // --- Imports ---
    importFichier: "Fichier à importer : CSV, GeoJSON ou ZIP (Shapefile)",
    importProjet: "Projet dans lequel importer les données",
    importCategorie: "Catégorie à attribuer aux points importés",
    importMapping: "Correspondance entre les colonnes du fichier et les champs de l'application",
    importIgnorerDoublons: "Ne pas créer de point si un existe déjà à proximité",
    importMettreAJour: "Mettre à jour les données du point existant plutôt que l'ignorer",
    importRayonDoublon: "Distance en mètres pour considérer deux points comme identiques",

    // --- PostGIS ---
    postgisHost: "Adresse du serveur PostgreSQL (ex: localhost, 192.168.1.10)",
    postgisPort: "Port de connexion PostgreSQL (par défaut : 5432)",
    postgisDatabase: "Nom de la base de données PostgreSQL",
    postgisUser: "Nom d'utilisateur PostgreSQL",
    postgisPassword: "Mot de passe de l'utilisateur PostgreSQL",
    postgisSchema: "Schéma PostgreSQL à utiliser (par défaut : public)",

    // --- Paramètres apparence ---
    paramModeSombre: "Activer le thème sombre pour réduire la fatigue visuelle",
    paramLangue: "Langue de l'interface utilisateur",

    // --- Paramètres carte ---
    paramCarteStyle: "Style de carte par défaut à l'ouverture",
    paramCarteZoom: "Niveau de zoom initial (1=monde, 18=rue)",
    paramCarteLatitude: "Latitude du centre de la carte par défaut",
    paramCarteLongitude: "Longitude du centre de la carte par défaut",

    // --- Statistiques ---
    statsPeriode: "Période d'analyse : 7 jours, 30 jours, 3 mois, 1 an",
    statsExport: "Télécharger les statistiques au format CSV ou PDF"
  }
}

export default helpContentFr

/**
 * Contenus d'aide en français pour GéoClic Demandes
 * Structure multilingue préparée pour le futur
 */

export const helpContentFr = {
  // ═══════════════════════════════════════════════════════════════════════════
  // PAGES - Aide globale (panneau latéral)
  // ═══════════════════════════════════════════════════════════════════════════

  pages: {
    dashboard: {
      title: "Tableau de bord",
      icon: "📊",
      sections: [
        {
          title: "Bienvenue",
          content: `Le tableau de bord est votre centre de contrôle pour gérer les demandes citoyennes. Il vous donne une vue d'ensemble de l'activité en temps réel.`
        },
        {
          title: "Statistiques en temps réel",
          content: `Les cartes en haut de l'écran affichent :
• **Total demandes** : Nombre total de signalements reçus
• **Nouvelles** : Demandes en attente de traitement (action requise)
• **Urgentes** : Demandes marquées comme urgentes
• **Délai moyen** : Temps moyen de résolution en jours
• **Traitées ce mois** : Signalements résolus dans le mois en cours`
        },
        {
          title: "À traiter en priorité",
          content: `Cette section liste les demandes nécessitant une attention immédiate :

**Critères d'affichage :**
• Demandes de priorité **Urgente** ou **Haute**
• Demandes dont le **délai de traitement est dépassé**

**Indicateurs visuels :**
• 🔴 Badge rouge : Délai dépassé (X jours de retard)
• 📧 Icône email : Un rappel a été envoyé à l'agent

Cliquez sur une demande pour accéder directement à son détail.`
        },
        {
          title: "Graphiques d'analyse",
          content: `Trois graphiques vous aident à visualiser l'activité :

**Répartition par catégorie** (camembert)
Montre la distribution des demandes par type de problème.

**Répartition par service** (camembert)
Affiche la charge de travail par service municipal. Les couleurs correspondent aux couleurs des services.

**Évolution sur 30 jours** (courbe)
Montre le nombre de demandes créées jour par jour.`
        },
        {
          title: "Statistiques par service",
          content: `Le tableau en bas affiche pour chaque service :
• **Nombre de demandes** assignées
• **Délai moyen** de traitement en jours

Ces données permettent d'identifier les services surchargés ou les plus performants.`
        },
        {
          title: "Actions rapides",
          content: `Trois boutons vous permettent d'accéder rapidement aux fonctions principales :
• **Nouvelles demandes** : Accès direct aux demandes en attente (le badge rouge indique le nombre)
• **Voir la carte** : Visualiser tous les signalements sur une carte interactive
• **Statistiques** : Accéder aux analyses détaillées et graphiques`
        }
      ]
    },

    demandesList: {
      title: "Liste des demandes",
      icon: "📋",
      sections: [
        {
          title: "Présentation",
          content: `Cette page affiche toutes les demandes citoyennes dans un tableau. Vous pouvez rechercher, filtrer et accéder au détail de chaque demande.`
        },
        {
          title: "Recherche",
          content: `La barre de recherche permet de trouver une demande par :
• Numéro de suivi (ex: DEM-2026-0001)
• Mot-clé dans la description
• Email du déclarant

Tapez votre recherche et appuyez sur **Entrée** pour lancer la recherche.`
        },
        {
          title: "Filtres",
          content: `Utilisez les filtres pour affiner l'affichage :
• **Statut** : Filtrer par état d'avancement de la demande
• **Priorité** : Filtrer par niveau d'urgence (Urgente, Haute, Normale, Basse)
• **Zone** : Filtrer par quartier ou secteur géographique`
        },
        {
          title: "Comprendre les colonnes",
          content: `Le tableau affiche plusieurs informations :

• **N°** : Numéro de suivi unique
• **Catégorie** : Type de signalement avec icône
• **Description** : Résumé du problème
• **Statut** : État actuel (badge coloré)
• **Priorité** : Niveau d'urgence (cliquez pour modifier)
• **Agent** : Agent assigné à la demande
• **Messages** : Badge avec nombre de messages non lus (💬)
• **Date** : Date de création`
        },
        {
          title: "Changer la priorité rapidement",
          content: `Vous pouvez modifier la priorité directement depuis la liste :

1. Cliquez sur le **badge de priorité** (Urgente, Haute, Normale, Basse)
2. Un menu déroulant s'ouvre
3. Sélectionnez la nouvelle priorité
4. Le changement est enregistré immédiatement

Cette fonction permet de trier rapidement les demandes sans ouvrir chaque fiche.`
        },
        {
          title: "Indicateur de messages",
          content: `Le badge **💬** indique les messages non lus :

• Un **chiffre** apparaît si des messages du tchat n'ont pas été consultés
• Le badge **pulse** (animation) pour attirer l'attention
• Cliquez sur la demande pour lire les messages

Le tchat permet de communiquer avec les agents terrain.`
        },
        {
          title: "Comprendre les statuts",
          content: `Chaque demande passe par différents états :
• 🔵 **Nouveau** : Demande reçue, non encore traitée
• 🟠 **En modération** : En attente de validation par un modérateur
• 🟢 **Accepté** : Validée, en attente d'assignation à un agent
• 🟣 **En cours** : Prise en charge par un agent
• 🔷 **Planifié** : Intervention programmée à une date précise
• ✅ **Traité** : Problème résolu
• 🔴 **Non retenu** : Rejeté (hors périmètre, doublon, etc.)
• ⬛ **Clôturé** : Dossier fermé définitivement`
        },
        {
          title: "Navigation",
          content: `• Cliquez sur une ligne du tableau pour voir le détail complet de la demande
• Utilisez les boutons "Précédent" et "Suivant" pour naviguer entre les pages
• Le compteur en haut indique le nombre total de résultats`
        }
      ]
    },

    demandeDetail: {
      title: "Détail d'une demande",
      icon: "📄",
      sections: [
        {
          title: "Vue d'ensemble",
          content: `Cette page affiche toutes les informations d'un signalement citoyen en 3 colonnes :

**Colonne gauche** : Informations de la demande
**Colonne centrale** : Photos et carte
**Colonne droite** : Tchat avec les agents terrain`
        },
        {
          title: "Actions disponibles",
          content: `Les boutons d'action permettent de :

• **Changer statut** : Faire avancer la demande dans le workflow
• **Modifier priorité** : Changer le niveau d'urgence (Urgente, Haute, Normale, Basse)
• **Assigner service** : Attribuer à un service municipal
• **Assigner agent** : Désigner un agent responsable
• **Planifier** : Programmer une date d'intervention

**Selon le statut actuel**, certaines actions sont disponibles ou non.`
        },
        {
          title: "Tchat avec le terrain",
          content: `La colonne de droite contient un **tchat intégré** pour communiquer avec les agents terrain :

**Envoyer un message :**
1. Tapez votre message dans le champ en bas
2. Cliquez sur **Envoyer** ou appuyez sur Entrée

**Types d'expéditeurs :**
• 💼 **Demandes** : Messages du back-office (vous)
• 🔧 **Service** : Messages de GeoClic Services (desktop)
• 📱 **Terrain** : Messages de l'application mobile terrain

Chaque participant a une **couleur unique** pour faciliter la lecture.
Les messages se rafraîchissent automatiquement toutes les 30 secondes.`
        },
        {
          title: "Carte et localisation",
          content: `La section centrale affiche :

• **Photos** : Galerie des photos du signalement (cliquez pour agrandir)
• **Carte** : Position exacte du signalement sur une mini-carte
• **Coordonnées GPS** : Latitude et longitude
• **Zone** : Quartier ou secteur concerné

Cliquez sur la carte pour voir une vue plus large.`
        },
        {
          title: "Détection des doublons",
          content: `Le système détecte automatiquement les **doublons potentiels** :

**Doublons potentiels :**
Signalements similaires à proximité (même zone, même catégorie). Vous pouvez :
• **Marquer comme doublon** : Lie cette demande à une autre
• **Ignorer** : Ce n'est pas un doublon

**Doublons liés :**
Si d'autres demandes sont liées comme doublons, elles apparaissent ici.
Cela permet de traiter ensemble des signalements identiques.`
        },
        {
          title: "Historique",
          content: `L'historique trace toutes les actions effectuées :
• Création initiale
• Changements de statut avec commentaires
• Assignations (service et agent)
• Planifications d'intervention
• Notes internes des agents

Chaque entrée indique la date, l'heure et la personne responsable.`
        },
        {
          title: "Contacter le déclarant",
          content: `Les coordonnées du citoyen sont affichées :
• Cliquez sur l'**email** pour ouvrir votre messagerie
• Cliquez sur le **téléphone** pour appeler directement (sur mobile)

⚠️ Ces informations sont confidentielles et ne doivent pas être partagées.`
        }
      ]
    },

    carte: {
      title: "Carte des signalements",
      icon: "🗺️",
      sections: [
        {
          title: "Présentation",
          content: `La carte affiche tous les signalements géolocalisés. Chaque marqueur représente une demande, sa couleur indique son statut.`
        },
        {
          title: "Couleurs des marqueurs",
          content: `Les marqueurs sont colorés selon le statut :
• 🔵 **Bleu** : Nouveau
• 🟠 **Orange** : En modération
• 🟢 **Vert clair** : Accepté
• 🟣 **Violet** : En cours
• 🔷 **Indigo** : Planifié
• ✅ **Vert foncé** : Traité
• 🔴 **Rouge** : Non retenu
• ⬛ **Gris** : Clôturé`
        },
        {
          title: "Zones géographiques",
          content: `Les zones permettent de découper votre territoire :

**Types de zones :**
• 🔵 **Quartiers** : Zones bleues
• 🟣 **Secteurs** : Zones violettes
• 🟢 **Communes** : Zones vertes

**Afficher/Masquer les zones :**
Cochez la case **"Afficher les zones"** pour superposer les périmètres sur la carte.
Passez la souris sur une zone pour voir son nom.

Les zones sont configurées dans le module d'administration.`
        },
        {
          title: "Filtrer les marqueurs",
          content: `Le panneau de filtres permet d'affiner l'affichage :

• **Par statut** : Cochez/décochez les statuts souhaités
• **Multi-sélection** : Affichez plusieurs statuts simultanément

Le compteur en bas indique le nombre de demandes affichées par rapport au total.`
        },
        {
          title: "Interagir avec la carte",
          content: `**Marqueurs :**
• Cliquez sur un marqueur pour voir les informations principales
• Dans la popup, cliquez sur **"Voir détails"** pour ouvrir la fiche complète

**Navigation :**
• Utilisez la molette de la souris ou les boutons +/- pour zoomer
• Glissez-déposez pour déplacer la carte
• La carte s'ajuste automatiquement pour afficher toutes les zones`
        }
      ]
    },

    categories: {
      title: "Gestion des catégories",
      icon: "🏷️",
      sections: [
        {
          title: "À quoi servent les catégories ?",
          content: `Les catégories permettent de classer les signalements par type de problème. Elles apparaissent dans le formulaire du portail citoyen et facilitent le tri et les statistiques.

Les catégories sont **hiérarchiques** : une catégorie parente peut avoir des sous-catégories.`
        },
        {
          title: "Affichage en tuiles",
          content: `Les catégories sont présentées sous forme de **tuiles colorées** :

• L'**icône** et la **couleur** permettent une identification rapide
• Le **nom** et la **description** informent les citoyens
• Le nombre de **demandes** associées est affiché
• Les **sous-catégories** sont regroupées sous leur parent

Cliquez sur une tuile pour voir ou modifier ses paramètres.`
        },
        {
          title: "Créer une catégorie",
          content: `1. Cliquez sur **"+ Nouvelle catégorie"**
2. Renseignez le **nom** (obligatoire)
3. Ajoutez une **description** pour aider les citoyens
4. Choisissez une **icône** (emoji + icône Material)
5. Sélectionnez une **couleur** parmi les 10 disponibles
6. Optionnel : Sélectionnez une **catégorie parente** pour créer une sous-catégorie
7. Cliquez sur **"Créer"**`
        },
        {
          title: "Options avancées",
          content: `Chaque catégorie dispose d'options avancées :

**Traitement :**
• **Modération requise** : Les demandes passent par la modération avant acceptation
• **Délai de traitement** : Nombre de jours prévu pour résoudre ce type de problème

**Photos :**
• **Photos obligatoires** : Le citoyen doit joindre au moins une photo
• **Nombre max de photos** : Limite le nombre de photos par demande

**Assignation :**
• **Service par défaut** : Service automatiquement assigné aux nouvelles demandes
• **Ordre d'affichage** : Position dans la liste du portail citoyen`
        },
        {
          title: "Champs personnalisés",
          content: `Vous pouvez ajouter des **champs personnalisés** par catégorie :

Ces champs permettent de collecter des informations spécifiques selon le type de signalement.

**Exemple pour "Éclairage" :**
• N° du lampadaire
• Type de panne (ampoule, câble, vandalisme)

Configurez les champs dans le détail de la catégorie.`
        },
        {
          title: "Assignation automatique",
          content: `Liez une catégorie à un **service municipal** :

1. Modifiez la catégorie
2. Dans **"Service par défaut"**, sélectionnez le service
3. Enregistrez

Toute nouvelle demande de cette catégorie sera **automatiquement assignée** à ce service.
Cela évite de trier manuellement chaque demande.`
        },
        {
          title: "Modifier ou supprimer",
          content: `Chaque carte de catégorie affiche des actions :
• ✏️ **Modifier** : Changer le nom, l'icône, la couleur ou les options
• 🔄 **Activer/Désactiver** : Rendre visible ou non dans le portail citoyen
• 🗑️ **Supprimer** : Retirer la catégorie (impossible si des demandes y sont associées)

⚠️ **Désactivez** plutôt que supprimer pour conserver l'historique des demandes existantes.`
        }
      ]
    },

    services: {
      title: "Gestion des services",
      icon: "🏢",
      sections: [
        {
          title: "À quoi servent les services ?",
          content: `Les services représentent les **équipes municipales** chargées de traiter les demandes :

• Service Voirie
• Service Espaces Verts
• Service Éclairage Public
• Service Propreté
• etc.

Chaque service peut avoir plusieurs **agents** qui interviennent sur le terrain.`
        },
        {
          title: "Liste des services",
          content: `La page affiche les services sous forme de **cartes** :

• **Nom** et **code** du service
• **Couleur** et **icône** pour l'identification
• **Responsable** du service
• **Nombre d'agents** rattachés
• **Statistiques** : Demandes assignées et en cours

Les statistiques en haut résument l'activité globale.`
        },
        {
          title: "Créer un service",
          content: `1. Cliquez sur **"+ Nouveau service"**
2. Renseignez les informations :
   • **Nom** : Nom complet du service (ex: "Service Voirie")
   • **Code** : Code court (ex: "VOIRIE")
   • **Description** : Rôle du service
   • **Couleur** et **Icône** : Identification visuelle
3. Coordonnées :
   • **Email** : Email du service pour les notifications
   • **Téléphone** : Numéro de contact
   • **Responsable** : Nom du chef de service
4. Cliquez sur **"Créer"**`
        },
        {
          title: "Notifications du service",
          content: `Configurez les notifications automatiques :

• **Nouvelle demande** : Email quand une demande est assignée au service
• **Changement de statut** : Email quand le statut d'une demande change
• **Emails supplémentaires** : Ajoutez d'autres destinataires (un par ligne)

Ces notifications permettent au service d'être informé en temps réel.`
        },
        {
          title: "Gestion des agents",
          content: `Chaque service a ses propres **agents terrain** :

**Voir les agents :**
Cliquez sur un service pour afficher ses agents.

**Ajouter un agent :**
1. Cliquez sur **"+ Nouvel agent"**
2. Renseignez :
   • **Email** : Identifiant de connexion
   • **Nom** et **Prénom**
   • **Téléphone** : Pour contact terrain
   • **Rôle** : Responsable ou Agent
3. Options :
   • **Peut être assigné** : Apparaît dans la liste d'assignation
   • **Reçoit les notifications** : Emails automatiques
4. Cliquez sur **"Créer"**`
        },
        {
          title: "Rôles des agents",
          content: `Deux rôles sont disponibles :

**🔴 Responsable**
• Supervise les agents du service
• Reçoit toutes les notifications du service
• Peut réassigner les demandes

**🔵 Agent**
• Intervient sur le terrain
• Reçoit les notifications pour ses demandes
• Utilise l'application mobile GéoClic Terrain`
        },
        {
          title: "Réinitialiser un mot de passe",
          content: `Si un agent a oublié son mot de passe :

1. Cliquez sur l'agent dans la liste
2. Cliquez sur **"Réinitialiser le mot de passe"**
3. Un nouveau mot de passe temporaire est généré
4. Communiquez-le à l'agent

L'agent pourra ensuite le modifier dans son profil.`
        },
        {
          title: "Lier services et catégories",
          content: `Pour automatiser l'assignation :

1. Allez dans **Catégories**
2. Modifiez une catégorie
3. Dans **"Service par défaut"**, choisissez le service
4. Enregistrez

Toute nouvelle demande de cette catégorie sera automatiquement assignée au service choisi.`
        }
      ]
    },

    templates: {
      title: "Templates de notification",
      icon: "📧",
      sections: [
        {
          title: "À quoi servent les templates ?",
          content: `Les templates sont des modèles de messages envoyés automatiquement aux citoyens. Ils permettent de personnaliser la communication tout en automatisant l'envoi.`
        },
        {
          title: "Types de templates",
          content: `Deux formats sont disponibles :
• **Email** : Messages complets avec mise en forme, images, liens
• **SMS** : Messages courts (160 caractères max), plus directs`
        },
        {
          title: "Déclencheurs automatiques",
          content: `Chaque template s'active automatiquement selon l'événement :
• **Création** : Quand un citoyen soumet une nouvelle demande
• **Acceptée** : Quand la demande est validée par un modérateur
• **Rejetée** : Quand la demande n'est pas retenue
• **Planifiée** : Quand une intervention est programmée
• **Traitée** : Quand le problème est résolu
• **Clôturée** : Quand le dossier est définitivement fermé`
        },
        {
          title: "Variables dynamiques",
          content: `Insérez des informations dynamiques avec les variables :
• **{{numero_suivi}}** : Numéro unique de la demande
• **{{categorie}}** : Type de signalement
• **{{statut}}** : État actuel
• **{{date_creation}}** : Date de création
• **{{date_planification}}** : Date d'intervention prévue
• **{{declarant_nom}}** : Nom du citoyen
• **{{lien_suivi}}** : URL pour suivre la demande`
        },
        {
          title: "Exemple de template",
          content: `**Sujet** : Votre demande {{numero_suivi}} a été reçue

**Contenu** :
Bonjour {{declarant_nom}},

Nous avons bien reçu votre signalement concernant "{{categorie}}".

Votre numéro de suivi est : {{numero_suivi}}

Vous pouvez suivre l'avancement de votre demande sur :
{{lien_suivi}}

Cordialement,
Le service technique`
        }
      ]
    },

    statistiques: {
      title: "Statistiques et analyses",
      icon: "📊",
      sections: [
        {
          title: "Présentation",
          content: `Cette page vous permet d'analyser l'activité de votre service avec des graphiques et tableaux détaillés.`
        },
        {
          title: "Choisir la période",
          content: `Sélectionnez l'intervalle d'analyse avec les boutons :
• **7 jours** : Activité de la semaine passée
• **30 jours** : Vue mensuelle (par défaut)
• **3 mois** : Tendances trimestrielles
• **1 an** : Vue annuelle complète`
        },
        {
          title: "Comprendre les graphiques",
          content: `Trois graphiques sont disponibles :
• **Évolution** : Courbe montrant le nombre de demandes par jour
• **Par statut** : Camembert de répartition des états
• **Top catégories** : Barres horizontales des types les plus fréquents`
        },
        {
          title: "Tableaux détaillés",
          content: `Deux tableaux complètent les graphiques :
• **Par quartier** : Volume de demandes par zone géographique
• **Par catégorie** : Détail avec pourcentages pour chaque type`
        },
        {
          title: "Exporter les données",
          content: `Cliquez sur **"Exporter"** pour télécharger les données au format JSON. Vous pourrez les exploiter dans Excel ou un autre outil d'analyse.`
        }
      ]
    },

    parametres: {
      title: "Paramètres",
      icon: "⚙️",
      sections: [
        {
          title: "Présentation",
          content: `La page Paramètres permet de configurer votre espace GéoClic. Elle est divisée en **5 onglets** selon vos droits d'accès.`
        },
        {
          title: "Onglets disponibles",
          content: `• **Général** : Configuration de base (nom, logo, options de traitement)
• **Alertes** : Configuration des délais et rappels automatiques
• **Email** : Configuration SMTP pour les notifications (admin uniquement)
• **Utilisateurs** : Gestion des comptes d'accès (admin uniquement)
• **Mon profil** : Vos informations personnelles`
        }
      ]
    },

    parametresAlertes: {
      title: "Paramètres des alertes",
      icon: "🔔",
      sections: [
        {
          title: "Délais de traitement",
          content: `Configurez les seuils d'alerte pour les demandes en retard :

**Délai de retard (jours)**
Nombre de jours après lequel une demande est considérée en retard.
Passé ce délai, la demande apparaît dans la liste **"À traiter en priorité"** du tableau de bord avec un badge rouge.

Exemple : Si vous mettez 7, les demandes non traitées depuis plus de 7 jours seront signalées.`
        },
        {
          title: "Rappels d'intervention",
          content: `Configurez les rappels automatiques pour les agents terrain :

**Activer les rappels**
• ✅ Activé : Un email est envoyé à l'agent avant l'intervention planifiée
• ⬜ Désactivé : Aucun rappel automatique

**Heures avant l'intervention**
Nombre d'heures avant la date planifiée pour envoyer le rappel.
Exemples :
• **2 heures** : Rappel court terme
• **24 heures** : Rappel la veille
• **48 heures** : Rappel 2 jours avant

L'email contient le numéro, la catégorie, l'adresse et la description de la demande.`
        },
        {
          title: "Indicateurs visuels",
          content: `Les alertes apparaissent à plusieurs endroits :

**Tableau de bord :**
• Section "À traiter en priorité" avec délais dépassés
• Badge 📧 si un rappel a été envoyé

**Liste des demandes :**
• Badge rouge sur les demandes en retard
• Tri automatique par priorité

**Détail demande :**
• Alerte visuelle si délai dépassé`
        }
      ]
    },

    parametresGeneral: {
      title: "Paramètres généraux",
      icon: "⚙️",
      sections: [
        {
          title: "Identité de la collectivité",
          content: `Ces informations personnalisent votre espace :
• **Nom du projet** : Le nom de votre collectivité ou service (ex: "Mairie de La Grande-Motte")
• **Couleur principale** : Personnalise l'interface avec votre identité visuelle
• **URL du logo** : Adresse web de votre logo (format https://...). Dimensions recommandées : 200x60 pixels`
        },
        {
          title: "Notifications",
          content: `• **Email notifications admin** : Cette adresse recevra les alertes pour les nouvelles demandes, demandes urgentes et rapports quotidiens`
        },
        {
          title: "Options de traitement",
          content: `**Modération des demandes**
• ✅ Activé : Les nouvelles demandes passent par l'état "En modération" avant d'être acceptées. Cela permet de filtrer les abus, doublons ou demandes hors périmètre.
• ⬜ Désactivé : Les demandes sont directement "Acceptées" et visibles pour assignation.

**Assignation automatique par quartier**
• ✅ Activé : Les demandes sont automatiquement assignées à l'agent responsable du quartier concerné (si configuré).
• ⬜ Désactivé : Un superviseur doit assigner manuellement chaque demande.`
        }
      ]
    },

    parametresEmail: {
      title: "Configuration Email",
      icon: "✉️",
      sections: [
        {
          title: "Pourquoi configurer l'email ?",
          content: `⚠️ **Important** : Sans configuration email, les citoyens ne recevront aucune notification de suivi de leur demande.

L'email permet d'envoyer automatiquement :
• Accusé de réception lors de la création
• Notifications de changement de statut
• Informations sur les interventions planifiées`
        },
        {
          title: "Serveur SMTP",
          content: `Le serveur SMTP est fourni par votre hébergeur email. Exemples courants :
• **Gmail** : smtp.gmail.com (port 587)
• **OVH** : ssl0.ovh.net (port 587)
• **Office 365** : smtp.office365.com (port 587)
• **Free** : smtp.free.fr (port 587)

Contactez votre service informatique si vous ne connaissez pas ces informations.`
        },
        {
          title: "Port SMTP",
          content: `Le port dépend du type de connexion :
• **587** : Standard avec TLS (recommandé)
• **465** : SSL direct
• **25** : Non sécurisé (déconseillé, souvent bloqué)`
        },
        {
          title: "Authentification",
          content: `• **Utilisateur** : Généralement votre adresse email complète
• **Mot de passe** : Le mot de passe de votre compte email

⚠️ Pour Gmail avec 2FA, créez un "Mot de passe d'application" dans les paramètres de sécurité Google.`
        },
        {
          title: "Expéditeur",
          content: `• **Nom expéditeur** : Nom affiché dans les emails reçus (ex: "Mairie de La Grande-Motte")
• **Email expéditeur** : Adresse qui apparaîtra comme émetteur (ex: "noreply@mairie.fr")`
        },
        {
          title: "Sécurité TLS",
          content: `✅ **Recommandé** : Cochez "Utiliser TLS" pour chiffrer la connexion. La plupart des serveurs modernes l'exigent.`
        },
        {
          title: "Tester la configuration",
          content: `Avant d'enregistrer, cliquez sur **"Envoyer un test"** pour vérifier que tout fonctionne. Un email de test sera envoyé à votre adresse admin.

Si le test échoue, vérifiez :
• Le serveur et le port sont corrects
• L'utilisateur et le mot de passe sont valides
• TLS est activé si requis par le serveur`
        }
      ]
    },

    parametresUtilisateurs: {
      title: "Gestion des utilisateurs",
      icon: "👥",
      sections: [
        {
          title: "Les rôles expliqués",
          content: `**🔴 Administrateur**
• Accès complet à toutes les fonctionnalités
• Gestion des paramètres et utilisateurs
• Création/suppression de catégories et templates
• Visualisation de toutes les demandes

**🟡 Modérateur**
• Validation ou rejet des nouvelles demandes
• Assignation des demandes aux agents
• Pas d'accès aux paramètres système

**🔵 Agent**
• Traitement des demandes qui lui sont assignées
• Changement de statut et ajout de commentaires
• Vision limitée à ses propres demandes`
        },
        {
          title: "Créer un utilisateur",
          content: `1. Cliquez sur **"+ Nouvel utilisateur"**
2. Renseignez le **nom** complet
3. Entrez l'**email** (servira d'identifiant de connexion)
4. Choisissez le **rôle** approprié
5. Définissez un **mot de passe** temporaire
6. Cliquez sur **"Créer"**

L'utilisateur pourra ensuite changer son mot de passe dans "Mon profil".`
        },
        {
          title: "Modifier un utilisateur",
          content: `• Cliquez sur ✏️ pour modifier
• Vous pouvez changer le nom et le rôle
• L'email ne peut pas être modifié (identifiant unique)
• Laissez le mot de passe vide pour le conserver
• Ou entrez un nouveau mot de passe pour le réinitialiser`
        },
        {
          title: "Sécurité",
          content: `• Minimum **8 caractères** pour les mots de passe
• Chaque utilisateur doit avoir un **email unique**
• Supprimez les comptes des personnes qui quittent le service
• Vérifiez régulièrement la liste des utilisateurs actifs`
        }
      ]
    },

    parametresProfil: {
      title: "Mon profil",
      icon: "👤",
      sections: [
        {
          title: "Vos informations",
          content: `• **Nom** : Votre nom affiché dans l'application et les historiques de demandes
• **Email** : Votre identifiant de connexion (non modifiable)`
        },
        {
          title: "Changer votre mot de passe",
          content: `Pour des raisons de sécurité, changez votre mot de passe régulièrement :

1. Entrez votre **nouveau mot de passe** (minimum 8 caractères)
2. **Confirmez** en le saisissant à nouveau
3. Cliquez sur **"Mettre à jour"**

Conseils :
• Mélangez lettres, chiffres et symboles
• Évitez les mots du dictionnaire
• N'utilisez pas le même mot de passe qu'ailleurs`
        },
        {
          title: "En cas d'oubli",
          content: `Si vous avez oublié votre mot de passe, contactez un administrateur de votre organisation pour le réinitialiser.`
        }
      ]
    },

    login: {
      title: "Connexion",
      icon: "🔐",
      sections: [
        {
          title: "Se connecter",
          content: `Entrez vos identifiants pour accéder à GéoClic Demandes :
• **Email** : Votre adresse email professionnelle
• **Mot de passe** : Votre mot de passe personnel`
        },
        {
          title: "Problème de connexion ?",
          content: `Si vous ne parvenez pas à vous connecter :
• Vérifiez que votre email est correct
• Vérifiez les majuscules/minuscules du mot de passe
• Contactez un administrateur pour réinitialiser votre mot de passe`
        }
      ]
    },

    // ═════════════════════════════════════════════════════════════════════════
    // GUIDES PAR RÔLE
    // ═════════════════════════════════════════════════════════════════════════

    guideAdmin: {
      title: "Guide Administrateur",
      icon: "👑",
      sections: [
        {
          title: "Votre rôle",
          content: `En tant qu'administrateur, vous avez un accès complet à toutes les fonctionnalités de GéoClic Demandes. Vous êtes responsable de la **configuration**, de la **gestion des utilisateurs** et du **suivi global** de l'activité.`
        },
        {
          title: "Première configuration",
          content: `Après l'installation, configurez votre collectivité dans cet ordre :

**1. Identité de la collectivité** (Paramètres > Personnalisation)
• Nom de la collectivité, logo, couleurs
• Informations de contact (email, téléphone, site web)

**2. Catégories de signalement** (menu Catégories)
• Créez les catégories principales (Voirie, Propreté, Éclairage...)
• Ajoutez les sous-catégories avec icônes et couleurs

**3. Services municipaux** (menu Services)
• Créez les services (Service Technique, Espaces Verts...)
• Associez chaque catégorie à un service

**4. Utilisateurs et agents** (Paramètres > Utilisateurs)
• Créez les comptes agents avec le rôle approprié
• Associez chaque agent à un service

**5. Configuration email** (Paramètres > Email)
• Paramétrage SMTP pour les notifications
• Activation des notifications citoyen et agents`
        },
        {
          title: "Gestion quotidienne",
          content: `**Tableau de bord** : Consultez les KPIs chaque matin
• Taux de résolution : doit rester au-dessus de 70%
• Demandes urgentes et en retard : traiter en priorité
• Comparaison avec le mois précédent : détecter les tendances

**Modération** : Si activée, validez les nouvelles demandes
• Accepter les signalements légitimes
• Rejeter les doublons ou signalements non pertinents

**Suivi des services** : Vérifiez les délais de traitement
• Identifier les services en surcharge
• Réaffecter les demandes si nécessaire`
        },
        {
          title: "Statistiques et reporting",
          content: `Utilisez le menu **Statistiques** pour analyser l'activité :
• **Filtres par période** : jour, semaine, mois, année
• **Répartition par catégorie** : identifier les problèmes récurrents
• **Répartition par quartier** : cibler les zones à améliorer
• **Temps moyen de traitement** : évaluer la performance

Le **Tableau de bord** affiche aussi :
• **Tendance 12 mois** : évolution à long terme
• **Distribution des statuts** : pipeline des demandes en cours
• **Comparaison inter-périodes** : progression par rapport au mois précédent`
        }
      ]
    },

    guideAgent: {
      title: "Guide Agent Back-office",
      icon: "🧑‍💼",
      sections: [
        {
          title: "Votre rôle",
          content: `En tant qu'agent back-office, vous gérez les demandes citoyennes depuis le bureau. Vous êtes le lien entre les citoyens et les agents terrain.`
        },
        {
          title: "Traiter une demande",
          content: `**1. Consulter les nouvelles demandes** (menu Demandes)
• Les demandes sont triées par date (plus récentes en premier)
• Filtrez par statut "Nouveau" pour voir ce qui est à traiter
• Le badge orange indique le nombre de nouvelles demandes

**2. Ouvrir une demande**
• Cliquez sur une demande pour voir son détail
• Consultez la description, les photos, la localisation sur la carte
• Vérifiez les éventuels doublons signalés

**3. Changer le statut**
• **Accepter** : La demande est prise en charge
• **Rejeter** : Signalement non pertinent (avec motif)
• **En cours** : Un agent travaille dessus
• **Traité** : L'intervention est terminée

**4. Modifier la priorité** si nécessaire
• Cliquez sur le badge de priorité pour le modifier
• Urgente, Haute, Normale, Basse`
        },
        {
          title: "Communication",
          content: `**Tchat interne** (colonne droite du détail demande)
• Échangez avec les agents terrain via le tchat intégré
• Les messages sont visibles uniquement par les agents (pas les citoyens)
• Le badge de message non lu apparaît dans la liste

**Templates de réponses** (menu Templates)
• Utilisez des réponses pré-formatées pour gagner du temps
• Les templates sont envoyés par email aux citoyens`
        },
        {
          title: "Bonnes pratiques",
          content: `• Traitez les demandes **urgentes** en priorité chaque matin
• Vérifiez les **doublons** avant de créer une intervention
• Ajoutez des **notes internes** pour le suivi
• Communiquez avec les agents terrain via le **tchat**
• Consultez le **tableau de bord** pour votre charge de travail`
        }
      ]
    },

    guideTerrain: {
      title: "Guide Agent Terrain",
      icon: "🔧",
      sections: [
        {
          title: "Votre rôle",
          content: `En tant qu'agent terrain, vous intervenez sur le terrain pour résoudre les signalements. Vous utilisez l'application **GéoClic Services** (desktop) ou la **PWA Terrain** (mobile).`
        },
        {
          title: "Application desktop (GéoClic Services)",
          content: `Accédez à GéoClic Services depuis votre navigateur :

**Tableau de bord** : Vos demandes assignées
• Triées par priorité et date
• Badge de nouveaux messages

**Détail demande** : Informations complètes
• Description, photos, localisation
• Boutons d'action : Prendre en charge, Planifier, Terminer

**Tchat** : 2 canaux de communication
• Canal **Back-office** : échangez avec l'agent administratif
• Canal **Terrain** : échangez avec un collègue terrain`
        },
        {
          title: "Application mobile (PWA Terrain)",
          content: `Installez la PWA sur votre téléphone pour les interventions :

**Connexion** : Utilisez vos identifiants habituels

**Liste des demandes** : Uniquement vos demandes assignées

**Détail et navigation** :
• Onglet **Détail** : description et photos
• Onglet **Carte** : localisation avec boutons GPS
• Bouton **Google Maps** : itinéraire en voiture
• Bouton **Waze** : navigation GPS optimisée

**Actions rapides** :
• **Prendre en charge** : marquer que vous y allez
• **Planifier** : choisir une date d'intervention
• **Terminer** : marquer comme traité`
        },
        {
          title: "Bonnes pratiques terrain",
          content: `• Consultez vos demandes **le matin** avant de partir
• Utilisez le **GPS** pour naviguer vers le lieu d'intervention
• **Prenez en charge** la demande avant d'intervenir
• **Planifiez** si l'intervention est reportée à un autre jour
• **Marquez comme traité** dès que l'intervention est terminée
• Communiquez via le **tchat** si vous avez besoin d'informations`
        }
      ]
    },

    guideCitoyen: {
      title: "Guide Citoyen",
      icon: "🏠",
      sections: [
        {
          title: "Signaler un problème",
          content: `Le portail citoyen vous permet de signaler les problèmes dans votre commune en 4 étapes simples :

**Étape 1 - Catégorie** : Choisissez le type de problème
• Voirie (nid-de-poule, trottoir cassé...)
• Propreté (dépôt sauvage, poubelle pleine...)
• Éclairage (lampadaire cassé, zone sombre...)
• Espaces verts (arbre dangereux, pelouse...)

**Étape 2 - Description** : Décrivez le problème
• Soyez précis (quel côté de la rue, quelle ampleur)
• Ajoutez des photos pour illustrer (facultatif mais recommandé)

**Étape 3 - Localisation** : Indiquez où se situe le problème
• Utilisez le GPS pour une localisation automatique
• Ou déplacez le marqueur sur la carte
• Ou entrez une adresse manuellement

**Étape 4 - Vos coordonnées** : Pour vous tenir informé
• Email obligatoire (vous recevrez le numéro de suivi)
• Nom et téléphone facultatifs`
        },
        {
          title: "Suivre votre demande",
          content: `Après votre signalement, vous recevez un **numéro de suivi** par email.

**Pour consulter l'avancement :**
• Allez sur la page "Suivi" du portail
• Entrez votre numéro de suivi
• Consultez le statut actuel et l'historique

**Signification des statuts :**
• **Nouveau** : Signalement reçu, en attente de traitement
• **Accepté** : La collectivité a pris connaissance
• **En cours** : Un agent est assigné
• **Planifié** : Intervention prévue à une date fixée
• **Traité** : L'intervention est terminée
• **Rejeté** : Signalement non retenu (avec motif)`
        },
        {
          title: "Carte des signalements",
          content: `La carte publique affiche tous les signalements de votre commune :
• Visualisez les problèmes déjà signalés dans votre quartier
• Évitez de signaler un problème déjà connu
• Cliquez sur un marqueur pour voir le détail`
        }
      ]
    }
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // TOOLTIPS - Infobulles contextuelles
  // ═══════════════════════════════════════════════════════════════════════════

  tooltips: {
    // Paramètres généraux
    nomProjet: "Le nom de votre collectivité ou service. Il apparaîtra dans l'interface et les notifications.",
    couleurPrincipale: "Personnalisez l'interface avec la couleur de votre identité visuelle.",
    urlLogo: "Lien vers votre logo (format https://...). Dimensions recommandées : 200x60 pixels.",
    emailNotifications: "Cette adresse recevra les alertes : nouvelles demandes, urgences, rapports.",
    moderationActive: "Si activé, les demandes passent par une étape de validation avant d'être acceptées.",
    assignationAuto: "Si activé, les demandes sont automatiquement assignées à l'agent du quartier concerné.",

    // Paramètres email
    smtpHost: "Adresse du serveur SMTP (ex: smtp.gmail.com, ssl0.ovh.net)",
    smtpPort: "Port de connexion : 587 (TLS), 465 (SSL) ou 25 (non sécurisé)",
    smtpUser: "Identifiant de connexion au serveur SMTP, souvent votre email",
    smtpPassword: "Mot de passe du compte SMTP. Pour Gmail avec 2FA, utilisez un mot de passe d'application.",
    senderName: "Nom qui apparaîtra comme expéditeur dans les emails reçus",
    senderEmail: "Adresse email qui apparaîtra comme expéditeur",
    smtpTls: "Connexion sécurisée recommandée. Décochez uniquement si votre serveur ne le supporte pas.",

    // Utilisateurs
    userRole: "Admin : accès total. Modérateur : validation des demandes. Agent : traitement assigné.",
    userEmail: "L'email sert d'identifiant de connexion et ne peut pas être modifié ensuite.",
    userPassword: "Minimum 8 caractères. Laissez vide pour conserver le mot de passe actuel.",

    // Templates
    templateType: "Email pour messages longs, SMS pour notifications courtes (160 car. max)",
    templateTrigger: "L'événement qui déclenchera l'envoi automatique de ce template",
    templateVariables: "Cliquez sur une variable pour l'insérer dans le contenu",
    templateSubject: "Objet de l'email. Vous pouvez utiliser des variables comme {{numero_suivi}}",

    // Catégories
    categorieNom: "Nom court et explicite (ex: Voirie, Éclairage, Propreté)",
    categorieDescription: "Description pour aider les citoyens à choisir la bonne catégorie",
    categorieIcone: "Icône visuelle pour identifier rapidement la catégorie",
    categorieCouleur: "Couleur pour l'affichage dans les listes et sur la carte",
    categorieActive: "Seules les catégories actives sont visibles dans le portail citoyen",
    categorieParent: "Catégorie parente pour créer une hiérarchie (sous-catégorie)",
    categorieServiceDefaut: "Service municipal automatiquement assigné aux nouvelles demandes de cette catégorie",
    categorieDelaiTraitement: "Nombre de jours prévu pour traiter ce type de demande",
    categorieModeration: "Si activé, les demandes passent par la modération avant acceptation",
    categoriePhotoObligatoire: "Si activé, le citoyen doit joindre au moins une photo",
    categoriePhotoMax: "Nombre maximum de photos autorisées par demande",

    // Services
    serviceNom: "Nom complet du service municipal (ex: Service Voirie)",
    serviceCode: "Code court pour identifier le service (ex: VOIRIE, ESP-VERTS)",
    serviceEmail: "Email du service pour recevoir les notifications",
    serviceTelephone: "Numéro de téléphone du service",
    serviceResponsable: "Nom du responsable ou chef de service",
    serviceNotifNouvelle: "Envoyer un email quand une demande est assignée au service",
    serviceNotifStatut: "Envoyer un email quand le statut d'une demande change",
    serviceEmailsSupp: "Emails supplémentaires pour les notifications (un par ligne)",

    // Agents
    agentEmail: "Email de l'agent, sert d'identifiant de connexion",
    agentNom: "Nom complet de l'agent",
    agentTelephone: "Numéro de téléphone pour contact terrain",
    agentRole: "Responsable : supervise le service. Agent : intervient sur le terrain",
    agentAssignable: "Si activé, l'agent apparaît dans la liste d'assignation des demandes",
    agentNotifications: "Si activé, l'agent reçoit les emails de notification",

    // Demandes
    demandeStatut: "Statut actuel de la demande dans le workflow de traitement",
    demandePriorite: "Niveau d'urgence : Urgente > Haute > Normale > Basse",
    demandeAgent: "Agent responsable du traitement de cette demande",
    demandeService: "Service municipal assigné à cette demande",
    demandePlanification: "Date et heure prévues pour l'intervention sur le terrain",
    demandeDoublon: "Demande identifiée comme doublon d'une autre",
    demandeTchat: "Conversation avec les agents terrain et le service",

    // Alertes
    delaiRetard: "Nombre de jours après lequel une demande est considérée en retard",
    rappelIntervention: "Envoyer un email de rappel à l'agent avant l'intervention planifiée",
    rappelHeures: "Nombre d'heures avant l'intervention pour envoyer le rappel",

    // Statistiques
    statsPeriode: "Période d'analyse des données",
    statsExport: "Télécharger les données au format JSON pour analyse externe",
    statsParService: "Répartition des demandes par service municipal",
    statsDelaiMoyen: "Temps moyen de traitement des demandes en jours"
  }
}

export default helpContentFr

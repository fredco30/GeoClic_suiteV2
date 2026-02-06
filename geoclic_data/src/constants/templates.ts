/**
 * Templates de projet prédéfinis - Structure municipale professionnelle
 * Ces templates sont utilisés lors de la création de projets et l'ajout de familles
 *
 * Types de géométrie supportés:
 * - POINT: Élément ponctuel (lampadaire, banc, arbre...)
 * - LINESTRING: Élément linéaire (canalisation, chemin, haie...)
 * - POLYGON: Zone/Surface (parking, parc, parcelle...)
 */

export type GeometryType = 'POINT' | 'LINESTRING' | 'POLYGON'

export interface TemplateField {
  nom: string
  type: string
  obligatoire: boolean
  ordre: number
  options?: string[]
  min?: number
  max?: number
}

export interface TemplateChild {
  code: string
  label: string
  icon: string
  geomType?: GeometryType  // Type de géométrie (hérite du parent si non spécifié)
  children?: TemplateChild[]
}

export interface TemplateFamily {
  code: string
  label: string
  icon: string
  color: string
  geomType: GeometryType  // Type de géométrie par défaut pour cette famille
  children: TemplateChild[]
  fields: TemplateField[]
}

export interface ProjectTemplate {
  id: string
  name: string
  icon: string
  color: string
  description: string
  geomType?: GeometryType  // Type dominant (pour l'affichage)
  families: TemplateFamily[]
}

export const projectTemplates: ProjectTemplate[] = [
  {
    id: 'eclairage',
    name: 'Éclairage Public',
    icon: 'mdi-lightbulb-on',
    color: 'amber',
    description: 'Inventaire complet des points lumineux',
    families: [
      {
        code: 'ECLAIRAGE',
        label: 'Éclairage Public',
        icon: 'mdi-lightbulb-on',
        color: '#FFC107',
        geomType: 'POINT',
        children: [
          {
            code: 'LUMINAIRE',
            label: 'Luminaire',
            icon: 'mdi-ceiling-light',
            children: [
              { code: 'LUM_LED', label: 'LED', icon: 'mdi-led-on' },
              { code: 'LUM_SODIUM', label: 'Sodium HP/BP', icon: 'mdi-lightbulb' },
              { code: 'LUM_HALOGENE', label: 'Halogène', icon: 'mdi-lightbulb-outline' },
              { code: 'LUM_DECORATIF', label: 'Décoratif', icon: 'mdi-lamps' },
            ]
          },
          {
            code: 'SUPPORT',
            label: 'Support',
            icon: 'mdi-transmission-tower',
            children: [
              { code: 'MAT_ACIER', label: 'Mât acier', icon: 'mdi-cylinder' },
              { code: 'MAT_ALU', label: 'Mât aluminium', icon: 'mdi-cylinder-off' },
              { code: 'MAT_BOIS', label: 'Mât bois', icon: 'mdi-forest' },
              { code: 'CONSOLE', label: 'Console/Crosse', icon: 'mdi-hook' },
              { code: 'FACADE', label: 'Fixation façade', icon: 'mdi-home' },
            ]
          },
          {
            code: 'ARMOIRE_EP',
            label: 'Armoire électrique',
            icon: 'mdi-flash',
            children: [
              { code: 'ARM_COMMANDE', label: 'Armoire commande', icon: 'mdi-server' },
              { code: 'ARM_DISTRIBUTION', label: 'Armoire distribution', icon: 'mdi-electric-switch' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État général', type: 'select', obligatoire: true, options: ['Neuf', 'Bon', 'Moyen', 'Dégradé', 'Hors service'], ordre: 2 },
          { nom: 'Puissance (W)', type: 'number', obligatoire: false, min: 0, max: 1000, ordre: 3 },
          { nom: 'Hauteur feu (m)', type: 'number', obligatoire: false, min: 0, max: 20, ordre: 4 },
          { nom: 'Année installation', type: 'number', obligatoire: false, min: 1950, max: 2030, ordre: 5 },
          { nom: 'Numéro série', type: 'text', obligatoire: false, ordre: 6 },
          { nom: 'Fabricant', type: 'text', obligatoire: false, ordre: 7 },
        ]
      },
    ],
  },
  {
    id: 'mobilier',
    name: 'Mobilier Urbain',
    icon: 'mdi-bench',
    color: 'brown',
    description: 'Bancs, poubelles, abris, signalétique',
    families: [
      {
        code: 'MOBILIER',
        label: 'Mobilier Urbain',
        icon: 'mdi-bench',
        color: '#795548',
        geomType: 'POINT',
        children: [
          {
            code: 'ASSISE',
            label: 'Assises',
            icon: 'mdi-bench',
            children: [
              { code: 'BANC_BOIS', label: 'Banc bois', icon: 'mdi-bench' },
              { code: 'BANC_METAL', label: 'Banc métal', icon: 'mdi-bench' },
              { code: 'BANC_BETON', label: 'Banc béton', icon: 'mdi-bench-back' },
              { code: 'CHAISE', label: 'Chaise urbaine', icon: 'mdi-seat' },
            ]
          },
          {
            code: 'PROPRETE',
            label: 'Propreté',
            icon: 'mdi-delete-outline',
            children: [
              { code: 'POUB_SIMPLE', label: 'Poubelle simple', icon: 'mdi-delete' },
              { code: 'POUB_TRI', label: 'Poubelle tri sélectif', icon: 'mdi-recycle' },
              { code: 'CORBEILLE', label: 'Corbeille', icon: 'mdi-basket' },
              { code: 'CANISETTE', label: 'Distributeur canisettes', icon: 'mdi-dog' },
            ]
          },
          {
            code: 'ABRI',
            label: 'Abris',
            icon: 'mdi-bus-stop',
            children: [
              { code: 'ABRIBUS', label: 'Abribus', icon: 'mdi-bus-stop' },
              { code: 'ABRI_VELO', label: 'Abri vélos', icon: 'mdi-bike' },
              { code: 'KIOSQUE', label: 'Kiosque', icon: 'mdi-store' },
            ]
          },
          {
            code: 'DECO',
            label: 'Décoratif',
            icon: 'mdi-pot',
            children: [
              { code: 'JARDINIERE', label: 'Jardinière', icon: 'mdi-pot' },
              { code: 'BAC_FLEUR', label: 'Bac à fleurs', icon: 'mdi-flower' },
              { code: 'FONTAINE', label: 'Fontaine', icon: 'mdi-fountain' },
              { code: 'STATUE', label: 'Statue/Monument', icon: 'mdi-chess-rook' },
            ]
          },
          {
            code: 'STATIONNEMENT',
            label: 'Stationnement',
            icon: 'mdi-bike',
            children: [
              { code: 'ARCEAU_VELO', label: 'Arceau vélo', icon: 'mdi-bike' },
              { code: 'RACK_VELO', label: 'Rack vélos', icon: 'mdi-bicycle' },
              { code: 'BORNE_ELEC', label: 'Borne recharge', icon: 'mdi-ev-station' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État', type: 'select', obligatoire: true, options: ['Neuf', 'Bon', 'Moyen', 'Dégradé', 'À remplacer'], ordre: 2 },
          { nom: 'Matériau', type: 'select', obligatoire: false, options: ['Bois', 'Métal', 'Béton', 'Plastique', 'Inox', 'Fonte', 'Mixte'], ordre: 3 },
          { nom: 'Couleur', type: 'color', obligatoire: false, ordre: 4 },
          { nom: 'Année installation', type: 'number', obligatoire: false, min: 1900, max: 2030, ordre: 5 },
          { nom: 'Fabricant', type: 'text', obligatoire: false, ordre: 6 },
          { nom: 'Accessibilité PMR', type: 'select', obligatoire: false, options: ['Oui', 'Non', 'Partiel'], ordre: 7 },
        ]
      },
    ],
  },
  {
    id: 'espaces_verts',
    name: 'Espaces Verts',
    icon: 'mdi-tree',
    color: 'green',
    description: 'Arbres, parcs, jardins, arrosage',
    families: [
      {
        code: 'VEGETATION',
        label: 'Espaces Verts',
        icon: 'mdi-tree',
        color: '#4CAF50',
        geomType: 'POINT',
        children: [
          {
            code: 'ARBRE',
            label: 'Arbres',
            icon: 'mdi-tree',
            children: [
              { code: 'ARBRE_ALIGNEMENT', label: 'Arbre alignement', icon: 'mdi-tree' },
              { code: 'ARBRE_ISOLE', label: 'Arbre isolé', icon: 'mdi-pine-tree' },
              { code: 'ARBRE_REMARQUABLE', label: 'Arbre remarquable', icon: 'mdi-tree-outline' },
              { code: 'ARBUSTE', label: 'Arbuste', icon: 'mdi-flower' },
            ]
          },
          {
            code: 'SURFACE',
            label: 'Surfaces végétales',
            icon: 'mdi-grass',
            children: [
              { code: 'PELOUSE', label: 'Pelouse', icon: 'mdi-grass' },
              { code: 'PRAIRIE', label: 'Prairie fleurie', icon: 'mdi-flower-tulip' },
              { code: 'MASSIF', label: 'Massif floral', icon: 'mdi-flower' },
              { code: 'HAIE', label: 'Haie', icon: 'mdi-fence' },
            ]
          },
          {
            code: 'ARROSAGE',
            label: 'Arrosage',
            icon: 'mdi-water',
            children: [
              { code: 'ASPERSEUR', label: 'Asperseur', icon: 'mdi-sprinkler' },
              { code: 'GOUTTE_GOUTTE', label: 'Goutte à goutte', icon: 'mdi-water-outline' },
              { code: 'VANNE', label: 'Vanne', icon: 'mdi-pipe-valve' },
              { code: 'PROGRAMMATEUR', label: 'Programmateur', icon: 'mdi-timer' },
            ]
          },
          {
            code: 'EQUIPEMENT_EV',
            label: 'Équipements',
            icon: 'mdi-fence',
            children: [
              { code: 'CLOTURE', label: 'Clôture', icon: 'mdi-fence' },
              { code: 'PORTILLON', label: 'Portillon', icon: 'mdi-gate' },
              { code: 'TUTEUR', label: 'Tuteur', icon: 'mdi-arrow-up' },
              { code: 'PROTECTION', label: 'Protection arbre', icon: 'mdi-shield' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État sanitaire', type: 'select', obligatoire: true, options: ['Excellent', 'Bon', 'Moyen', 'Dépérissant', 'Mort', 'À surveiller'], ordre: 2 },
          { nom: 'Espèce', type: 'text', obligatoire: false, ordre: 3 },
          { nom: 'Hauteur (m)', type: 'number', obligatoire: false, min: 0, max: 50, ordre: 4 },
          { nom: 'Circonférence (cm)', type: 'number', obligatoire: false, min: 0, max: 500, ordre: 5 },
          { nom: 'Année plantation', type: 'number', obligatoire: false, min: 1800, max: 2030, ordre: 6 },
          { nom: 'Risque', type: 'select', obligatoire: false, options: ['Aucun', 'Faible', 'Moyen', 'Élevé', 'Critique'], ordre: 7 },
          { nom: 'Surface (m²)', type: 'number', obligatoire: false, min: 0, ordre: 8 },
        ]
      },
    ],
  },
  {
    id: 'voirie',
    name: 'Voirie & Signalisation',
    icon: 'mdi-road',
    color: 'grey',
    description: 'Routes, panneaux, feux, marquages',
    families: [
      {
        code: 'VOIRIE',
        label: 'Voirie & Signalisation',
        icon: 'mdi-road',
        color: '#607D8B',
        geomType: 'POINT',
        children: [
          {
            code: 'SIGNALISATION',
            label: 'Signalisation verticale',
            icon: 'mdi-sign-direction',
            children: [
              { code: 'PANNEAU_DANGER', label: 'Panneau danger', icon: 'mdi-alert' },
              { code: 'PANNEAU_INTERDIT', label: 'Panneau interdiction', icon: 'mdi-cancel' },
              { code: 'PANNEAU_OBLIGATION', label: 'Panneau obligation', icon: 'mdi-arrow-right-circle' },
              { code: 'PANNEAU_DIRECTION', label: 'Panneau direction', icon: 'mdi-sign-direction' },
              { code: 'PANNEAU_INFO', label: 'Panneau information', icon: 'mdi-information' },
            ]
          },
          {
            code: 'REGULATION',
            label: 'Régulation trafic',
            icon: 'mdi-traffic-light',
            children: [
              { code: 'FEU_TRICOLORE', label: 'Feu tricolore', icon: 'mdi-traffic-light' },
              { code: 'FEU_PIETON', label: 'Feu piéton', icon: 'mdi-walk' },
              { code: 'RADAR', label: 'Radar pédagogique', icon: 'mdi-speedometer' },
            ]
          },
          {
            code: 'SECURITE',
            label: 'Sécurité',
            icon: 'mdi-shield-car',
            children: [
              { code: 'RALENTISSEUR', label: 'Ralentisseur', icon: 'mdi-car-brake-alert' },
              { code: 'PASSAGE_PIETON', label: 'Passage piéton', icon: 'mdi-walk' },
              { code: 'BARRIERE', label: 'Barrière', icon: 'mdi-boom-gate' },
              { code: 'BORNE_ANTI', label: 'Borne anti-stationnement', icon: 'mdi-cylinder' },
            ]
          },
          {
            code: 'CHAUSSEE',
            label: 'Chaussée',
            icon: 'mdi-road-variant',
            children: [
              { code: 'TROTTOIR', label: 'Trottoir', icon: 'mdi-walk' },
              { code: 'BORDURE', label: 'Bordure', icon: 'mdi-border-bottom' },
              { code: 'CANIVEAU', label: 'Caniveau', icon: 'mdi-pipe-leak' },
              { code: 'NID_POULE', label: 'Nid de poule', icon: 'mdi-circle-outline' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État', type: 'select', obligatoire: true, options: ['Neuf', 'Bon', 'Moyen', 'Dégradé', 'À remplacer'], ordre: 2 },
          { nom: 'Conformité', type: 'select', obligatoire: false, options: ['Conforme', 'Non conforme', 'À vérifier'], ordre: 3 },
          { nom: 'Dimension', type: 'text', obligatoire: false, ordre: 4 },
          { nom: 'Rétroréflexion', type: 'select', obligatoire: false, options: ['Classe 1', 'Classe 2', 'Non applicable'], ordre: 5 },
          { nom: 'Année pose', type: 'number', obligatoire: false, min: 1950, max: 2030, ordre: 6 },
        ]
      },
    ],
  },
  {
    id: 'aires_jeux',
    name: 'Aires de Jeux',
    icon: 'mdi-seesaw',
    color: 'purple',
    description: 'Jeux enfants, équipements sécurisés',
    families: [
      {
        code: 'JEUX',
        label: 'Aires de Jeux',
        icon: 'mdi-seesaw',
        color: '#9C27B0',
        geomType: 'POINT',
        children: [
          {
            code: 'JEU_RESSORT',
            label: 'Jeux à ressort',
            icon: 'mdi-horse-variant',
            children: [
              { code: 'RESSORT_SIMPLE', label: 'Ressort simple', icon: 'mdi-horse' },
              { code: 'RESSORT_DOUBLE', label: 'Ressort double', icon: 'mdi-horse-variant' },
            ]
          },
          {
            code: 'JEU_BALANCEMENT',
            label: 'Balancement',
            icon: 'mdi-seesaw',
            children: [
              { code: 'BALANCOIRE_SIMPLE', label: 'Balançoire simple', icon: 'mdi-seesaw' },
              { code: 'BALANCOIRE_NID', label: 'Balançoire nid', icon: 'mdi-egg' },
              { code: 'BASCULE', label: 'Bascule', icon: 'mdi-scale-balance' },
            ]
          },
          {
            code: 'JEU_GLISSE',
            label: 'Glisse',
            icon: 'mdi-slide',
            children: [
              { code: 'TOBOGGAN_SIMPLE', label: 'Toboggan simple', icon: 'mdi-slide' },
              { code: 'TOBOGGAN_TUBE', label: 'Toboggan tube', icon: 'mdi-tunnel' },
            ]
          },
          {
            code: 'JEU_STRUCTURE',
            label: 'Structures',
            icon: 'mdi-castle',
            children: [
              { code: 'STRUCTURE_MULTI', label: 'Structure multi-jeux', icon: 'mdi-castle' },
              { code: 'CABANE', label: 'Cabane', icon: 'mdi-home' },
              { code: 'PONT_SUSPENDU', label: 'Pont suspendu', icon: 'mdi-bridge' },
              { code: 'FILET_GRIMPE', label: 'Filet à grimper', icon: 'mdi-spider-web' },
            ]
          },
          {
            code: 'JEU_SOL',
            label: 'Jeux au sol',
            icon: 'mdi-checkerboard',
            children: [
              { code: 'BAC_SABLE', label: 'Bac à sable', icon: 'mdi-beach' },
              { code: 'MARELLE', label: 'Marelle', icon: 'mdi-grid' },
              { code: 'TABLE_JEU', label: 'Table de jeu', icon: 'mdi-table-furniture' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: true, ordre: 1 },
          { nom: 'État', type: 'select', obligatoire: true, options: ['Conforme', 'À surveiller', 'Non conforme', 'Interdit', 'À remplacer'], ordre: 2 },
          { nom: 'Date dernier contrôle', type: 'date', obligatoire: true, ordre: 3 },
          { nom: 'Tranche âge', type: 'select', obligatoire: true, options: ['0-3 ans', '3-6 ans', '6-12 ans', 'Tous âges'], ordre: 4 },
          { nom: 'Norme NF EN 1176', type: 'select', obligatoire: false, options: ['Conforme', 'Non conforme', 'Non vérifié'], ordre: 5 },
          { nom: 'Fabricant', type: 'text', obligatoire: false, ordre: 6 },
          { nom: 'Année installation', type: 'number', obligatoire: false, min: 1980, max: 2030, ordre: 7 },
          { nom: 'Numéro série', type: 'text', obligatoire: false, ordre: 8 },
          { nom: 'Sol amortissant', type: 'select', obligatoire: false, options: ['EPDM', 'Copeaux bois', 'Sable', 'Gazon', 'Béton', 'Autre'], ordre: 9 },
          { nom: 'Hauteur chute (m)', type: 'number', obligatoire: false, min: 0, max: 5, ordre: 10 },
        ]
      },
    ],
  },
  {
    id: 'reseaux',
    name: 'Réseaux & Assainissement',
    icon: 'mdi-pipe',
    color: 'cyan',
    description: 'Canalisations, regards, bouches',
    families: [
      {
        code: 'RESEAUX',
        label: 'Réseaux & Assainissement',
        icon: 'mdi-pipe',
        color: '#00BCD4',
        geomType: 'POINT',
        children: [
          {
            code: 'ASSAINISSEMENT',
            label: 'Assainissement',
            icon: 'mdi-pipe-leak',
            children: [
              { code: 'REGARD_VISITE', label: 'Regard de visite', icon: 'mdi-checkbox-blank-circle' },
              { code: 'BOUCHE_EGOUT', label: 'Bouche égout', icon: 'mdi-grid' },
              { code: 'AVALOIR', label: 'Avaloir', icon: 'mdi-arrow-down-circle' },
              { code: 'GRILLE', label: 'Grille', icon: 'mdi-view-grid' },
            ]
          },
          {
            code: 'EAU_POTABLE',
            label: 'Eau potable',
            icon: 'mdi-water',
            children: [
              { code: 'VANNE_EP', label: 'Vanne', icon: 'mdi-pipe-valve' },
              { code: 'BOUCHE_INCENDIE', label: 'Bouche incendie', icon: 'mdi-fire-hydrant' },
              { code: 'BORNE_FONTAINE', label: 'Borne fontaine', icon: 'mdi-water-pump' },
              { code: 'COMPTEUR', label: 'Compteur', icon: 'mdi-counter' },
            ]
          },
          {
            code: 'TELECOM',
            label: 'Télécommunications',
            icon: 'mdi-phone',
            children: [
              { code: 'CHAMBRE_TELECOM', label: 'Chambre télécom', icon: 'mdi-phone-classic' },
              { code: 'ARMOIRE_TELECOM', label: 'Armoire télécom', icon: 'mdi-server' },
              { code: 'POTEAU_TELECOM', label: 'Poteau télécom', icon: 'mdi-transmission-tower' },
            ]
          },
          {
            code: 'GAZ',
            label: 'Gaz',
            icon: 'mdi-fire',
            children: [
              { code: 'COFFRET_GAZ', label: 'Coffret gaz', icon: 'mdi-gas-cylinder' },
              { code: 'VANNE_GAZ', label: 'Vanne gaz', icon: 'mdi-pipe-valve' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État', type: 'select', obligatoire: true, options: ['Bon', 'Moyen', 'Dégradé', 'Bouché', 'À remplacer'], ordre: 2 },
          { nom: 'Matériau', type: 'select', obligatoire: false, options: ['Fonte', 'Béton', 'PVC', 'Acier', 'PEHD', 'Autre'], ordre: 3 },
          { nom: 'Diamètre (mm)', type: 'number', obligatoire: false, min: 0, max: 2000, ordre: 4 },
          { nom: 'Profondeur (m)', type: 'number', obligatoire: false, min: 0, max: 10, ordre: 5 },
          { nom: 'Année pose', type: 'number', obligatoire: false, min: 1900, max: 2030, ordre: 6 },
          { nom: 'Gestionnaire', type: 'text', obligatoire: false, ordre: 7 },
        ]
      },
    ],
  },
  // ============================================================================
  // TEMPLATES LINÉAIRES (LINESTRING) - Réseaux, chemins, clôtures
  // ============================================================================
  {
    id: 'reseaux_lineaires',
    name: 'Réseaux Linéaires',
    icon: 'mdi-pipe',
    color: 'blue',
    description: 'Canalisations, conduites, câbles enterrés',
    geomType: 'LINESTRING',
    families: [
      {
        code: 'CANALISATION',
        label: 'Canalisations',
        icon: 'mdi-pipe',
        color: '#2196F3',
        geomType: 'LINESTRING',
        children: [
          {
            code: 'CANA_EAU',
            label: 'Eau potable',
            icon: 'mdi-water',
            children: [
              { code: 'CANA_EP_FONTE', label: 'Fonte ductile', icon: 'mdi-pipe' },
              { code: 'CANA_EP_PEHD', label: 'PEHD', icon: 'mdi-pipe' },
              { code: 'CANA_EP_PVC', label: 'PVC', icon: 'mdi-pipe' },
              { code: 'CANA_EP_ACIER', label: 'Acier', icon: 'mdi-pipe' },
            ]
          },
          {
            code: 'CANA_ASSAINI',
            label: 'Assainissement',
            icon: 'mdi-pipe-leak',
            children: [
              { code: 'CANA_EU', label: 'Eaux usées', icon: 'mdi-water-off' },
              { code: 'CANA_EP_PLUV', label: 'Eaux pluviales', icon: 'mdi-weather-rainy' },
              { code: 'CANA_UNITAIRE', label: 'Unitaire', icon: 'mdi-pipe-disconnected' },
            ]
          },
          {
            code: 'CANA_GAZ',
            label: 'Gaz',
            icon: 'mdi-fire',
            children: [
              { code: 'CANA_GAZ_BP', label: 'Basse pression', icon: 'mdi-gas-cylinder' },
              { code: 'CANA_GAZ_MP', label: 'Moyenne pression', icon: 'mdi-gas-cylinder' },
            ]
          },
          {
            code: 'CANA_ELEC',
            label: 'Électricité',
            icon: 'mdi-flash',
            children: [
              { code: 'CANA_BT', label: 'Basse tension', icon: 'mdi-flash' },
              { code: 'CANA_HTA', label: 'Haute tension A', icon: 'mdi-flash-alert' },
              { code: 'CANA_EP_ELEC', label: 'Éclairage public', icon: 'mdi-lightbulb' },
            ]
          },
          {
            code: 'CANA_TELECOM',
            label: 'Télécommunications',
            icon: 'mdi-ethernet-cable',
            children: [
              { code: 'CANA_FIBRE', label: 'Fibre optique', icon: 'mdi-fiber-smart-record' },
              { code: 'CANA_CUIVRE', label: 'Cuivre télécom', icon: 'mdi-phone-classic' },
              { code: 'CANA_FOURREAU', label: 'Fourreau vide', icon: 'mdi-pipe' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État', type: 'select', obligatoire: true, options: ['Bon', 'Moyen', 'Dégradé', 'Fuité', 'À remplacer'], ordre: 2 },
          { nom: 'Matériau', type: 'select', obligatoire: true, options: ['Fonte', 'PEHD', 'PVC', 'Béton', 'Grès', 'Acier', 'Cuivre', 'Fibre'], ordre: 3 },
          { nom: 'Diamètre (mm)', type: 'number', obligatoire: true, min: 10, max: 2000, ordre: 4 },
          { nom: 'Longueur (m)', type: 'calculated', obligatoire: false, ordre: 5 },
          { nom: 'Profondeur (m)', type: 'number', obligatoire: false, min: 0, max: 10, ordre: 6 },
          { nom: 'Année pose', type: 'number', obligatoire: false, min: 1900, max: 2030, ordre: 7 },
          { nom: 'Gestionnaire', type: 'select', obligatoire: false, options: ['Commune', 'GRDF', 'Enedis', 'Orange', 'Véolia', 'Suez', 'Autre'], ordre: 8 },
          { nom: 'Classe pression', type: 'select', obligatoire: false, options: ['PN6', 'PN10', 'PN16', 'PN25', 'Non applicable'], ordre: 9 },
        ]
      },
    ],
  },
  {
    id: 'voies_chemins',
    name: 'Voies & Chemins',
    icon: 'mdi-road-variant',
    color: 'grey',
    description: 'Routes, chemins piétons, pistes cyclables',
    geomType: 'LINESTRING',
    families: [
      {
        code: 'VOIE_LINEAIRE',
        label: 'Voies Linéaires',
        icon: 'mdi-road-variant',
        color: '#9E9E9E',
        geomType: 'LINESTRING',
        children: [
          {
            code: 'ROUTE',
            label: 'Routes',
            icon: 'mdi-road',
            children: [
              { code: 'ROUTE_COMMUNALE', label: 'Route communale', icon: 'mdi-road' },
              { code: 'ROUTE_DEPARTEMENTALE', label: 'Route départementale', icon: 'mdi-highway' },
              { code: 'RUE', label: 'Rue', icon: 'mdi-road-variant' },
              { code: 'IMPASSE', label: 'Impasse', icon: 'mdi-sign-caution' },
            ]
          },
          {
            code: 'CHEMIN',
            label: 'Chemins',
            icon: 'mdi-walk',
            children: [
              { code: 'CHEMIN_PIETON', label: 'Chemin piéton', icon: 'mdi-walk' },
              { code: 'PISTE_CYCLABLE', label: 'Piste cyclable', icon: 'mdi-bike' },
              { code: 'CHEMIN_RURAL', label: 'Chemin rural', icon: 'mdi-forest' },
              { code: 'ALLEE', label: 'Allée', icon: 'mdi-arrow-right' },
            ]
          },
          {
            code: 'TROTTOIR_LIN',
            label: 'Trottoirs',
            icon: 'mdi-walk',
            children: [
              { code: 'TROTTOIR_BETON', label: 'Trottoir béton', icon: 'mdi-walk' },
              { code: 'TROTTOIR_PAVE', label: 'Trottoir pavé', icon: 'mdi-checkerboard' },
              { code: 'TROTTOIR_ENROBE', label: 'Trottoir enrobé', icon: 'mdi-walk' },
            ]
          },
          {
            code: 'BORDURE_LIN',
            label: 'Bordures',
            icon: 'mdi-border-bottom',
            children: [
              { code: 'BORDURE_BETON', label: 'Bordure béton', icon: 'mdi-border-bottom' },
              { code: 'BORDURE_GRANITE', label: 'Bordure granite', icon: 'mdi-border-all' },
              { code: 'CANIVEAU_LIN', label: 'Caniveau', icon: 'mdi-pipe-leak' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État chaussée', type: 'select', obligatoire: true, options: ['Neuf', 'Bon', 'Usé', 'Dégradé', 'À refaire'], ordre: 2 },
          { nom: 'Revêtement', type: 'select', obligatoire: true, options: ['Enrobé', 'Béton', 'Pavés', 'Gravillons', 'Stabilisé', 'Terre', 'Dalles'], ordre: 3 },
          { nom: 'Largeur (m)', type: 'number', obligatoire: false, min: 0.5, max: 30, ordre: 4 },
          { nom: 'Longueur (m)', type: 'calculated', obligatoire: false, ordre: 5 },
          { nom: 'Année réfection', type: 'number', obligatoire: false, min: 1950, max: 2030, ordre: 6 },
          { nom: 'Éclairage', type: 'select', obligatoire: false, options: ['Oui', 'Non', 'Partiel'], ordre: 7 },
          { nom: 'Accessibilité PMR', type: 'select', obligatoire: false, options: ['Conforme', 'Non conforme', 'À adapter'], ordre: 8 },
        ]
      },
    ],
  },
  {
    id: 'clotures_haies',
    name: 'Clôtures & Haies',
    icon: 'mdi-fence',
    color: 'green',
    description: 'Clôtures, haies, murs de séparation',
    geomType: 'LINESTRING',
    families: [
      {
        code: 'SEPARATION',
        label: 'Clôtures & Haies',
        icon: 'mdi-fence',
        color: '#8BC34A',
        geomType: 'LINESTRING',
        children: [
          {
            code: 'CLOTURE',
            label: 'Clôtures',
            icon: 'mdi-fence',
            children: [
              { code: 'CLOTURE_GRILLAGE', label: 'Grillage', icon: 'mdi-grid' },
              { code: 'CLOTURE_RIGIDE', label: 'Panneau rigide', icon: 'mdi-fence' },
              { code: 'CLOTURE_BOIS', label: 'Bois', icon: 'mdi-forest' },
              { code: 'CLOTURE_PVC', label: 'PVC', icon: 'mdi-fence' },
              { code: 'GARDE_CORPS', label: 'Garde-corps', icon: 'mdi-railing' },
            ]
          },
          {
            code: 'MUR',
            label: 'Murs',
            icon: 'mdi-wall',
            children: [
              { code: 'MUR_PIERRE', label: 'Mur pierre', icon: 'mdi-wall' },
              { code: 'MUR_BETON', label: 'Mur béton', icon: 'mdi-wall' },
              { code: 'MUR_PARPAING', label: 'Mur parpaing', icon: 'mdi-wall' },
              { code: 'MURET', label: 'Muret', icon: 'mdi-wall' },
            ]
          },
          {
            code: 'HAIE_LIN',
            label: 'Haies',
            icon: 'mdi-tree',
            children: [
              { code: 'HAIE_CHAMPETRE', label: 'Haie champêtre', icon: 'mdi-tree' },
              { code: 'HAIE_TAILLEE', label: 'Haie taillée', icon: 'mdi-content-cut' },
              { code: 'HAIE_PERSISTANTE', label: 'Haie persistante', icon: 'mdi-pine-tree' },
              { code: 'HAIE_BOCAGERE', label: 'Haie bocagère', icon: 'mdi-forest' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État', type: 'select', obligatoire: true, options: ['Neuf', 'Bon', 'Moyen', 'Dégradé', 'À remplacer'], ordre: 2 },
          { nom: 'Hauteur (m)', type: 'number', obligatoire: false, min: 0, max: 10, ordre: 3 },
          { nom: 'Longueur (m)', type: 'calculated', obligatoire: false, ordre: 4 },
          { nom: 'Matériau', type: 'select', obligatoire: false, options: ['Grillage', 'Bois', 'PVC', 'Métal', 'Pierre', 'Béton', 'Végétal'], ordre: 5 },
          { nom: 'Espèce (haie)', type: 'text', obligatoire: false, ordre: 6 },
          { nom: 'Année installation', type: 'number', obligatoire: false, min: 1900, max: 2030, ordre: 7 },
          { nom: 'Propriétaire', type: 'select', obligatoire: false, options: ['Commune', 'Privé', 'Copropriété', 'État'], ordre: 8 },
        ]
      },
    ],
  },
  // ============================================================================
  // TEMPLATES SURFACIQUES (POLYGON) - Zones, parcelles, espaces
  // ============================================================================
  {
    id: 'espaces_publics',
    name: 'Espaces Publics',
    icon: 'mdi-texture-box',
    color: 'teal',
    description: 'Parcs, places, parkings, squares',
    geomType: 'POLYGON',
    families: [
      {
        code: 'ESPACE_PUBLIC',
        label: 'Espaces Publics',
        icon: 'mdi-texture-box',
        color: '#009688',
        geomType: 'POLYGON',
        children: [
          {
            code: 'PARC',
            label: 'Parcs & Jardins',
            icon: 'mdi-tree',
            children: [
              { code: 'PARC_URBAIN', label: 'Parc urbain', icon: 'mdi-tree' },
              { code: 'JARDIN_PUBLIC', label: 'Jardin public', icon: 'mdi-flower' },
              { code: 'SQUARE', label: 'Square', icon: 'mdi-nature-people' },
              { code: 'ESPACE_VERT', label: 'Espace vert', icon: 'mdi-grass' },
            ]
          },
          {
            code: 'PLACE',
            label: 'Places',
            icon: 'mdi-city',
            children: [
              { code: 'PLACE_PUBLIQUE', label: 'Place publique', icon: 'mdi-city' },
              { code: 'PARVIS', label: 'Parvis', icon: 'mdi-domain' },
              { code: 'ESPLANADE', label: 'Esplanade', icon: 'mdi-texture' },
              { code: 'MAIL', label: 'Mail', icon: 'mdi-arrow-left-right' },
            ]
          },
          {
            code: 'PARKING_ZONE',
            label: 'Parkings',
            icon: 'mdi-parking',
            children: [
              { code: 'PARKING_PUBLIC', label: 'Parking public', icon: 'mdi-parking' },
              { code: 'PARKING_PRIVE', label: 'Parking privé', icon: 'mdi-car' },
              { code: 'PARKING_VELO', label: 'Parking vélos', icon: 'mdi-bike' },
              { code: 'AIRE_COVOITURAGE', label: 'Aire covoiturage', icon: 'mdi-car-multiple' },
            ]
          },
          {
            code: 'AIRE_JEUX_ZONE',
            label: 'Aires de jeux',
            icon: 'mdi-seesaw',
            children: [
              { code: 'AIRE_ENFANTS', label: 'Aire enfants', icon: 'mdi-human-child' },
              { code: 'AIRE_FITNESS', label: 'Aire fitness', icon: 'mdi-dumbbell' },
              { code: 'TERRAIN_PETANQUE', label: 'Terrain pétanque', icon: 'mdi-baseball' },
              { code: 'CITY_STADE', label: 'City stade', icon: 'mdi-soccer' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État général', type: 'select', obligatoire: true, options: ['Excellent', 'Bon', 'Moyen', 'Dégradé', 'À rénover'], ordre: 2 },
          { nom: 'Surface (m²)', type: 'calculated', obligatoire: false, ordre: 3 },
          { nom: 'Périmètre (m)', type: 'calculated', obligatoire: false, ordre: 4 },
          { nom: 'Revêtement', type: 'select', obligatoire: false, options: ['Gazon', 'Enrobé', 'Gravillons', 'Dalles', 'Béton', 'Sable', 'Mixte'], ordre: 5 },
          { nom: 'Éclairage', type: 'select', obligatoire: false, options: ['Oui', 'Non', 'Partiel'], ordre: 6 },
          { nom: 'Accessibilité PMR', type: 'select', obligatoire: false, options: ['Conforme', 'Non conforme', 'Partiel'], ordre: 7 },
          { nom: 'Capacité places', type: 'number', obligatoire: false, min: 0, max: 1000, ordre: 8 },
          { nom: 'Horaires ouverture', type: 'text', obligatoire: false, ordre: 9 },
        ]
      },
    ],
  },
  {
    id: 'surfaces_vegetales',
    name: 'Surfaces Végétales',
    icon: 'mdi-grass',
    color: 'light-green',
    description: 'Pelouses, massifs, prairies, zones boisées',
    geomType: 'POLYGON',
    families: [
      {
        code: 'SURFACE_VERTE',
        label: 'Surfaces Végétales',
        icon: 'mdi-grass',
        color: '#8BC34A',
        geomType: 'POLYGON',
        children: [
          {
            code: 'PELOUSE_ZONE',
            label: 'Pelouses',
            icon: 'mdi-grass',
            children: [
              { code: 'PELOUSE_ORNEMENT', label: 'Pelouse ornement', icon: 'mdi-grass' },
              { code: 'PELOUSE_SPORT', label: 'Pelouse sportive', icon: 'mdi-soccer-field' },
              { code: 'PELOUSE_RUSTIQUE', label: 'Pelouse rustique', icon: 'mdi-flower-tulip' },
              { code: 'GAZON_SYNTHETIQUE', label: 'Gazon synthétique', icon: 'mdi-soccer' },
            ]
          },
          {
            code: 'MASSIF_ZONE',
            label: 'Massifs',
            icon: 'mdi-flower',
            children: [
              { code: 'MASSIF_FLORAL', label: 'Massif floral', icon: 'mdi-flower' },
              { code: 'MASSIF_ARBUSTIF', label: 'Massif arbustif', icon: 'mdi-tree' },
              { code: 'ROCAILLE', label: 'Rocaille', icon: 'mdi-spa' },
              { code: 'MASSIF_VIVACES', label: 'Massif vivaces', icon: 'mdi-flower-tulip' },
            ]
          },
          {
            code: 'PRAIRIE_ZONE',
            label: 'Prairies',
            icon: 'mdi-flower-tulip',
            children: [
              { code: 'PRAIRIE_FLEURIE', label: 'Prairie fleurie', icon: 'mdi-flower-tulip' },
              { code: 'PRAIRIE_NATURELLE', label: 'Prairie naturelle', icon: 'mdi-nature' },
              { code: 'FRICHE', label: 'Friche gérée', icon: 'mdi-sprout' },
            ]
          },
          {
            code: 'BOISE_ZONE',
            label: 'Zones boisées',
            icon: 'mdi-forest',
            children: [
              { code: 'BOSQUET', label: 'Bosquet', icon: 'mdi-forest' },
              { code: 'BOIS', label: 'Bois', icon: 'mdi-pine-tree' },
              { code: 'VERGER', label: 'Verger', icon: 'mdi-fruit-cherries' },
              { code: 'SOUS_BOIS', label: 'Sous-bois', icon: 'mdi-tree-outline' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État sanitaire', type: 'select', obligatoire: true, options: ['Excellent', 'Bon', 'Moyen', 'Dégradé', 'À rénover'], ordre: 2 },
          { nom: 'Surface (m²)', type: 'calculated', obligatoire: false, ordre: 3 },
          { nom: 'Type entretien', type: 'select', obligatoire: false, options: ['Intensif', 'Régulier', 'Extensif', 'Gestion différenciée', 'Aucun'], ordre: 4 },
          { nom: 'Fréquence tonte', type: 'select', obligatoire: false, options: ['Hebdomadaire', 'Bi-mensuelle', 'Mensuelle', 'Saisonnière', 'Annuelle'], ordre: 5 },
          { nom: 'Arrosage', type: 'select', obligatoire: false, options: ['Automatique', 'Manuel', 'Aucun'], ordre: 6 },
          { nom: 'Espèces principales', type: 'text', obligatoire: false, ordre: 7 },
          { nom: 'Année création', type: 'number', obligatoire: false, min: 1900, max: 2030, ordre: 8 },
          { nom: 'Biodiversité', type: 'select', obligatoire: false, options: ['Élevée', 'Moyenne', 'Faible', 'Non évaluée'], ordre: 9 },
        ]
      },
    ],
  },
  {
    id: 'batiments_zones',
    name: 'Bâtiments & Emprises',
    icon: 'mdi-domain',
    color: 'orange',
    description: 'Bâtiments publics, emprises au sol',
    geomType: 'POLYGON',
    families: [
      {
        code: 'BATIMENT',
        label: 'Bâtiments & Emprises',
        icon: 'mdi-domain',
        color: '#FF9800',
        geomType: 'POLYGON',
        children: [
          {
            code: 'BAT_PUBLIC',
            label: 'Bâtiments publics',
            icon: 'mdi-bank',
            children: [
              { code: 'MAIRIE', label: 'Mairie', icon: 'mdi-bank' },
              { code: 'ECOLE', label: 'École', icon: 'mdi-school' },
              { code: 'MEDIATHEQUE', label: 'Médiathèque', icon: 'mdi-library' },
              { code: 'SALLE_FETES', label: 'Salle des fêtes', icon: 'mdi-party-popper' },
              { code: 'GYMNASE', label: 'Gymnase', icon: 'mdi-basketball' },
            ]
          },
          {
            code: 'BAT_TECHNIQUE',
            label: 'Bâtiments techniques',
            icon: 'mdi-warehouse',
            children: [
              { code: 'ATELIER_MUNICIPAL', label: 'Atelier municipal', icon: 'mdi-tools' },
              { code: 'STATION_POMPAGE', label: 'Station pompage', icon: 'mdi-water-pump' },
              { code: 'POSTE_TRANSFO', label: 'Poste transfo', icon: 'mdi-flash' },
              { code: 'LOCAL_TECHNIQUE', label: 'Local technique', icon: 'mdi-cog' },
            ]
          },
          {
            code: 'EMPRISE',
            label: 'Emprises',
            icon: 'mdi-texture',
            children: [
              { code: 'EMPRISE_BATIMENT', label: 'Emprise bâtiment', icon: 'mdi-home-outline' },
              { code: 'EMPRISE_TECHNIQUE', label: 'Emprise technique', icon: 'mdi-cog-outline' },
              { code: 'EMPRISE_CHANTIER', label: 'Emprise chantier', icon: 'mdi-crane' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État général', type: 'select', obligatoire: true, options: ['Neuf', 'Bon', 'Correct', 'Vétuste', 'À démolir'], ordre: 2 },
          { nom: 'Surface (m²)', type: 'calculated', obligatoire: false, ordre: 3 },
          { nom: 'Surface plancher (m²)', type: 'number', obligatoire: false, min: 0, ordre: 4 },
          { nom: 'Nombre niveaux', type: 'number', obligatoire: false, min: 1, max: 20, ordre: 5 },
          { nom: 'Année construction', type: 'number', obligatoire: false, min: 1800, max: 2030, ordre: 6 },
          { nom: 'DPE', type: 'select', obligatoire: false, options: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'Non évalué'], ordre: 7 },
          { nom: 'Accessibilité PMR', type: 'select', obligatoire: false, options: ['Conforme', 'Non conforme', 'En cours'], ordre: 8 },
          { nom: 'Usage', type: 'text', obligatoire: false, ordre: 9 },
        ]
      },
    ],
  },
  {
    id: 'cimetieres',
    name: 'Cimetières',
    icon: 'mdi-grave-stone',
    color: 'blue-grey',
    description: 'Parcelles, concessions, espaces funéraires',
    geomType: 'POLYGON',
    families: [
      {
        code: 'CIMETIERE',
        label: 'Cimetières',
        icon: 'mdi-grave-stone',
        color: '#607D8B',
        geomType: 'POLYGON',
        children: [
          {
            code: 'PARCELLE_CIM',
            label: 'Parcelles',
            icon: 'mdi-grid',
            children: [
              { code: 'CARRE_INHUM', label: 'Carré inhumation', icon: 'mdi-checkbox-blank' },
              { code: 'CARRE_CINERAIRE', label: 'Espace cinéraire', icon: 'mdi-fire' },
              { code: 'JARDIN_SOUVENIR', label: 'Jardin du souvenir', icon: 'mdi-flower' },
              { code: 'OSSUAIRE', label: 'Ossuaire', icon: 'mdi-archive' },
            ]
          },
          {
            code: 'ALLEE_CIM',
            label: 'Allées',
            icon: 'mdi-road-variant',
            geomType: 'LINESTRING',  // Exception: les allées sont linéaires
            children: [
              { code: 'ALLEE_PRINCIPALE', label: 'Allée principale', icon: 'mdi-road' },
              { code: 'ALLEE_SECONDAIRE', label: 'Allée secondaire', icon: 'mdi-road-variant' },
            ]
          },
          {
            code: 'EQUIPEMENT_CIM',
            label: 'Équipements',
            icon: 'mdi-fountain',
            geomType: 'POINT',  // Exception: les équipements sont ponctuels
            children: [
              { code: 'POINT_EAU_CIM', label: 'Point d\'eau', icon: 'mdi-water-pump' },
              { code: 'POUBELLE_CIM', label: 'Poubelle', icon: 'mdi-delete' },
              { code: 'BANC_CIM', label: 'Banc', icon: 'mdi-bench' },
            ]
          },
        ],
        fields: [
          { nom: 'Photo', type: 'photo', obligatoire: false, ordre: 1 },
          { nom: 'État', type: 'select', obligatoire: true, options: ['Bon', 'Moyen', 'Dégradé', 'À rénover'], ordre: 2 },
          { nom: 'Surface (m²)', type: 'calculated', obligatoire: false, ordre: 3 },
          { nom: 'Nombre emplacements', type: 'number', obligatoire: false, min: 0, ordre: 4 },
          { nom: 'Emplacements libres', type: 'number', obligatoire: false, min: 0, ordre: 5 },
          { nom: 'Type concession', type: 'select', obligatoire: false, options: ['Perpétuelle', '50 ans', '30 ans', '15 ans', 'Terrain commun'], ordre: 6 },
          { nom: 'Revêtement sol', type: 'select', obligatoire: false, options: ['Gravillons', 'Stabilisé', 'Enrobé', 'Dalles', 'Gazon'], ordre: 7 },
        ]
      },
    ],
  },
]

/**
 * Compte le nombre total d'éléments dans une famille (types + sous-types)
 */
export function countTotalElements(family: any): number {
  let count = 0
  if (family.children) {
    count += family.children.length
    for (const child of family.children) {
      count += countTotalElements(child)
    }
  }
  return count
}

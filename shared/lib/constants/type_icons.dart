import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:flutter/material.dart';

/// Icônes prédéfinies pour les types de points SIG
/// Organisées par catégorie pour faciliter la sélection
class TypeIcons {
  /// Liste complète des icônes disponibles (44 icônes)
  static final List<IconData> allIcons = [
    ...infrastructureIcons,
    ...eclairageSignalisationIcons,
    ...mobilierUrbainIcons,
    ...natureIcons,
    ...servicesIcons,
  ];

  /// Infrastructure (13 icônes)
  static const List<IconData> infrastructureIcons = [
    FontAwesomeIcons.water,           // 💧 Assainissement/Eau
    FontAwesomeIcons.circle,          // 🔧 Canalisation
    FontAwesomeIcons.circleNotch,     // ⭕ Regard EU
    FontAwesomeIcons.droplet,         // 💧 Regard pluvial
    FontAwesomeIcons.gaugeHigh,       // 📊 Compteur eau
    FontAwesomeIcons.plug,            // 🔌 Compteur électrique
    FontAwesomeIcons.fire,            // 🔥 Incendie
    FontAwesomeIcons.bolt,            // ⚡ Électricité
    FontAwesomeIcons.wifi,            // 📡 Télécom
    FontAwesomeIcons.gasPump,         // ⛽ Gaz
    FontAwesomeIcons.bridge,          // 🌉 Ouvrage d'art
    FontAwesomeIcons.buildingColumns, // 🏛️ Bâtiment public
    FontAwesomeIcons.houseChimney,    // 🏠 Habitation
  ];

  /// Éclairage & Signalisation (8 icônes)
  static const List<IconData> eclairageSignalisationIcons = [
    FontAwesomeIcons.lightbulb,          // 💡 Éclairage général
    FontAwesomeIcons.streetView,         // 🏙️ Lampadaire
    FontAwesomeIcons.trafficLight,       // 🚦 Feu tricolore
    FontAwesomeIcons.triangleExclamation, // ⚠️ Danger
    FontAwesomeIcons.signHanging,        // 🪧 Panneau
    FontAwesomeIcons.roadBarrier,        // 🚧 Barrière
    FontAwesomeIcons.circleStop,         // 🛑 Stop
    FontAwesomeIcons.arrowsAlt,          // ➡️ Direction
  ];

  /// Mobilier Urbain (8 icônes)
  static const List<IconData> mobilierUrbainIcons = [
    FontAwesomeIcons.chair,          // 🪑 Banc/Siège
    FontAwesomeIcons.trashCan,       // 🗑️ Poubelle
    FontAwesomeIcons.umbrellaBeach,  // ⛱️ Abri
    FontAwesomeIcons.bus,            // 🚌 Arrêt de bus
    FontAwesomeIcons.bicycle,        // 🚲 Stationnement vélo
    FontAwesomeIcons.squareParking,  // 🅿️ Parking
    FontAwesomeIcons.phoneFlip,      // 📞 Cabine téléphonique
    FontAwesomeIcons.newspaper,      // 📰 Kiosque
  ];

  /// Nature & Espaces Verts (7 icônes)
  static const List<IconData> natureIcons = [
    FontAwesomeIcons.tree,       // 🌳 Arbre/Végétation
    FontAwesomeIcons.leaf,       // 🍃 Espace vert
    FontAwesomeIcons.seedling,   // 🌱 Plantation
    FontAwesomeIcons.mountain,   // ⛰️ Relief
    FontAwesomeIcons.cloudRain,  // 🌧️ Zone humide
    FontAwesomeIcons.sun,        // ☀️ Zone ensoleillée
    FontAwesomeIcons.spa,        // 🌸 Jardin/Parc
  ];

  /// Services & Équipements (8 icônes)
  static const List<IconData> servicesIcons = [
    FontAwesomeIcons.school,         // 🏫 École
    FontAwesomeIcons.hospital,       // 🏥 Santé
    FontAwesomeIcons.cartShopping,   // 🛒 Commerce
    FontAwesomeIcons.utensils,       // 🍴 Restaurant
    FontAwesomeIcons.dumbbell,       // 🏋️ Sport
    FontAwesomeIcons.users,          // 👥 Zone collective
    FontAwesomeIcons.toolbox,        // 🧰 Technique
    FontAwesomeIcons.industry,       // 🏭 Zone industrielle
  ];

  /// Noms des catégories
  static const List<String> categoryNames = [
    'Infrastructure',
    'Éclairage & Signalisation',
    'Mobilier Urbain',
    'Nature & Espaces Verts',
    'Services & Équipements',
  ];

  /// Récupère les icônes par catégorie
  static List<IconData> getIconsByCategory(int categoryIndex) {
    switch (categoryIndex) {
      case 0:
        return infrastructureIcons;
      case 1:
        return eclairageSignalisationIcons;
      case 2:
        return mobilierUrbainIcons;
      case 3:
        return natureIcons;
      case 4:
        return servicesIcons;
      default:
        return [];
    }
  }

  /// Convertit un IconData en nom de chaîne (pour stockage)
  static String iconToString(IconData icon) {
    // Mapping des IconData vers des noms de chaînes
    final iconMap = {
      FontAwesomeIcons.water: 'water',
      FontAwesomeIcons.circle: 'circle',
      FontAwesomeIcons.circleNotch: 'circleNotch',
      FontAwesomeIcons.droplet: 'droplet',
      FontAwesomeIcons.gaugeHigh: 'gaugeHigh',
      FontAwesomeIcons.plug: 'plug',
      FontAwesomeIcons.fire: 'fire',
      FontAwesomeIcons.bolt: 'bolt',
      FontAwesomeIcons.wifi: 'wifi',
      FontAwesomeIcons.gasPump: 'gasPump',
      FontAwesomeIcons.bridge: 'bridge',
      FontAwesomeIcons.buildingColumns: 'buildingColumns',
      FontAwesomeIcons.houseChimney: 'houseChimney',
      FontAwesomeIcons.lightbulb: 'lightbulb',
      FontAwesomeIcons.streetView: 'streetView',
      FontAwesomeIcons.trafficLight: 'trafficLight',
      FontAwesomeIcons.triangleExclamation: 'triangleExclamation',
      FontAwesomeIcons.signHanging: 'signHanging',
      FontAwesomeIcons.roadBarrier: 'roadBarrier',
      FontAwesomeIcons.circleStop: 'circleStop',
      FontAwesomeIcons.arrowsAlt: 'arrowsAlt',
      FontAwesomeIcons.chair: 'chair',
      FontAwesomeIcons.trashCan: 'trashCan',
      FontAwesomeIcons.umbrellaBeach: 'umbrellaBeach',
      FontAwesomeIcons.bus: 'bus',
      FontAwesomeIcons.bicycle: 'bicycle',
      FontAwesomeIcons.squareParking: 'squareParking',
      FontAwesomeIcons.phoneFlip: 'phoneFlip',
      FontAwesomeIcons.newspaper: 'newspaper',
      FontAwesomeIcons.tree: 'tree',
      FontAwesomeIcons.leaf: 'leaf',
      FontAwesomeIcons.seedling: 'seedling',
      FontAwesomeIcons.mountain: 'mountain',
      FontAwesomeIcons.cloudRain: 'cloudRain',
      FontAwesomeIcons.sun: 'sun',
      FontAwesomeIcons.spa: 'spa',
      FontAwesomeIcons.school: 'school',
      FontAwesomeIcons.hospital: 'hospital',
      FontAwesomeIcons.cartShopping: 'cartShopping',
      FontAwesomeIcons.utensils: 'utensils',
      FontAwesomeIcons.dumbbell: 'dumbbell',
      FontAwesomeIcons.users: 'users',
      FontAwesomeIcons.toolbox: 'toolbox',
      FontAwesomeIcons.industry: 'industry',
    };

    return iconMap[icon] ?? 'place'; // Fallback
  }

  /// Convertit un nom de chaîne en IconData
  static IconData stringToIcon(String? iconName) {
    if (iconName == null || iconName.isEmpty) {
      return FontAwesomeIcons.mapMarker; // Icône par défaut
    }

    final iconMap = {
      'water': FontAwesomeIcons.water,
      'circle': FontAwesomeIcons.circle,
      'circleNotch': FontAwesomeIcons.circleNotch,
      'droplet': FontAwesomeIcons.droplet,
      'gaugeHigh': FontAwesomeIcons.gaugeHigh,
      'plug': FontAwesomeIcons.plug,
      'fire': FontAwesomeIcons.fire,
      'bolt': FontAwesomeIcons.bolt,
      'wifi': FontAwesomeIcons.wifi,
      'gasPump': FontAwesomeIcons.gasPump,
      'bridge': FontAwesomeIcons.bridge,
      'buildingColumns': FontAwesomeIcons.buildingColumns,
      'houseChimney': FontAwesomeIcons.houseChimney,
      'lightbulb': FontAwesomeIcons.lightbulb,
      'streetView': FontAwesomeIcons.streetView,
      'trafficLight': FontAwesomeIcons.trafficLight,
      'triangleExclamation': FontAwesomeIcons.triangleExclamation,
      'signHanging': FontAwesomeIcons.signHanging,
      'roadBarrier': FontAwesomeIcons.roadBarrier,
      'circleStop': FontAwesomeIcons.circleStop,
      'arrowsAlt': FontAwesomeIcons.arrowsAlt,
      'chair': FontAwesomeIcons.chair,
      'trashCan': FontAwesomeIcons.trashCan,
      'umbrellaBeach': FontAwesomeIcons.umbrellaBeach,
      'bus': FontAwesomeIcons.bus,
      'bicycle': FontAwesomeIcons.bicycle,
      'squareParking': FontAwesomeIcons.squareParking,
      'phoneFlip': FontAwesomeIcons.phoneFlip,
      'newspaper': FontAwesomeIcons.newspaper,
      'tree': FontAwesomeIcons.tree,
      'leaf': FontAwesomeIcons.leaf,
      'seedling': FontAwesomeIcons.seedling,
      'mountain': FontAwesomeIcons.mountain,
      'cloudRain': FontAwesomeIcons.cloudRain,
      'sun': FontAwesomeIcons.sun,
      'spa': FontAwesomeIcons.spa,
      'school': FontAwesomeIcons.school,
      'hospital': FontAwesomeIcons.hospital,
      'cartShopping': FontAwesomeIcons.cartShopping,
      'utensils': FontAwesomeIcons.utensils,
      'dumbbell': FontAwesomeIcons.dumbbell,
      'users': FontAwesomeIcons.users,
      'toolbox': FontAwesomeIcons.toolbox,
      'industry': FontAwesomeIcons.industry,
      // Icônes anciennes pour compatibilité
      'pole': FontAwesomeIcons.plug,
      'manhole': FontAwesomeIcons.circleNotch,
      'building': FontAwesomeIcons.buildingColumns,
      'pipe': FontAwesomeIcons.circle,
      'pipeSection': FontAwesomeIcons.circle,
      'area': FontAwesomeIcons.drawPolygon,
      'furniture': FontAwesomeIcons.chair,
      'light': FontAwesomeIcons.lightbulb,
      'sign': FontAwesomeIcons.signHanging,
      // ═══ Mapping des icônes Material vers FontAwesome ═══
      // Icônes génériques
      'place': FontAwesomeIcons.locationDot,
      'location_on': FontAwesomeIcons.locationDot,
      'pin_drop': FontAwesomeIcons.mapPin,
      // Mobilier urbain
      'weekend': FontAwesomeIcons.chair,  // bancs
      'park': FontAwesomeIcons.tree,
      'delete_outline': FontAwesomeIcons.trashCan,
      'fence': FontAwesomeIcons.bars,
      // Éclairage & signalisation
      'lightbulb_outline': FontAwesomeIcons.lightbulb,
      'signpost': FontAwesomeIcons.signHanging,
      'traffic': FontAwesomeIcons.trafficLight,
      // Infrastructure
      'local_fire_department': FontAwesomeIcons.fire,
      'electrical_services': FontAwesomeIcons.bolt,
      'construction': FontAwesomeIcons.personDigging,
      'build': FontAwesomeIcons.wrench,
      'visibility': FontAwesomeIcons.eye,
      // Transport
      'directions_bus': FontAwesomeIcons.bus,
      'directions_car': FontAwesomeIcons.car,
      'local_parking': FontAwesomeIcons.squareParking,
      'directions_bike': FontAwesomeIcons.bicycle,
      // Nature
      'nature': FontAwesomeIcons.tree,
      'grass': FontAwesomeIcons.seedling,
      'water_drop': FontAwesomeIcons.droplet,
      // Services
      'store': FontAwesomeIcons.store,
      'restaurant': FontAwesomeIcons.utensils,
      'local_hospital': FontAwesomeIcons.hospital,
      'school': FontAwesomeIcons.school,
      // Zones
      'crop_square': FontAwesomeIcons.drawPolygon,
      'polyline': FontAwesomeIcons.bezierCurve,
      'timeline': FontAwesomeIcons.bezierCurve,
    };

    return iconMap[iconName] ?? FontAwesomeIcons.mapMarker;
  }
}

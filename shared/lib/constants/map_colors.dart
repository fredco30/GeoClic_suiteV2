import 'package:flutter/material.dart';

/// Palette de couleurs optimisées pour la cartographie
/// 16 couleurs avec contraste élevé et visibilité sur fond de carte
/// Compatible avec les daltoniens
class MapColors {
  /// Palette complète de 16 couleurs
  static const List<Color> allColors = [
    // Bleus (Eau & Infrastructure)
    bleuVif,
    bleuClair,
    bleuFonce,
    cyan,

    // Verts (Nature)
    vertStandard,
    vertClair,
    vertFonce,
    vertPomme,

    // Jaunes/Oranges (Énergie & Attention)
    jaune,
    orange,
    orangeFonce,

    // Rouges/Violets (Urgence & Services)
    rouge,
    violet,
    rose,

    // Neutres
    marron,
    gris,
  ];

  /// Noms des couleurs pour affichage
  static const List<String> colorNames = [
    'Bleu vif',
    'Bleu clair',
    'Bleu foncé',
    'Cyan',
    'Vert standard',
    'Vert clair',
    'Vert foncé',
    'Vert pomme',
    'Jaune',
    'Orange',
    'Orange foncé',
    'Rouge',
    'Violet',
    'Rose',
    'Marron',
    'Gris',
  ];

  // === BLEUS (Infrastructure & Eau) ===
  static const Color bleuVif = Color(0xFF0088FF);      // #0088FF
  static const Color bleuClair = Color(0xFF4FC3F7);    // #4FC3F7
  static const Color bleuFonce = Color(0xFF0277BD);    // #0277BD
  static const Color cyan = Color(0xFF00ACC1);         // #00ACC1

  // === VERTS (Nature & Espaces verts) ===
  static const Color vertStandard = Color(0xFF4CAF50); // #4CAF50
  static const Color vertClair = Color(0xFF81C784);    // #81C784
  static const Color vertFonce = Color(0xFF2E7D32);    // #2E7D32
  static const Color vertPomme = Color(0xFF66BB6A);    // #66BB6A

  // === JAUNES/ORANGES (Énergie & Attention) ===
  static const Color jaune = Color(0xFFFFEB3B);        // #FFEB3B
  static const Color orange = Color(0xFFFFA726);       // #FFA726
  static const Color orangeFonce = Color(0xFFFF9800);  // #FF9800

  // === ROUGES/VIOLETS (Urgence & Services) ===
  static const Color rouge = Color(0xFFF44336);        // #F44336
  static const Color violet = Color(0xFF9C27B0);       // #9C27B0
  static const Color rose = Color(0xFFE91E63);         // #E91E63

  // === NEUTRES ===
  static const Color marron = Color(0xFF795548);       // #795548 (Voirie)
  static const Color gris = Color(0xFF757575);         // #757575

  /// Récupère le nom d'une couleur
  static String getColorName(Color color) {
    final index = allColors.indexOf(color);
    if (index >= 0 && index < colorNames.length) {
      return colorNames[index];
    }
    return 'Couleur personnalisée';
  }

  /// Récupère la couleur à partir de sa valeur int
  static Color fromValue(int colorValue) {
    return Color(colorValue);
  }

  /// Vérifie si une couleur fait partie de la palette
  static bool isInPalette(Color color) {
    return allColors.any((c) => c.value == color.value);
  }

  /// Trouve la couleur la plus proche dans la palette
  static Color findClosest(Color color) {
    if (isInPalette(color)) return color;

    // Calculer la distance euclidienne dans l'espace RGB
    double minDistance = double.infinity;
    Color closestColor = allColors[0];

    for (final paletteColor in allColors) {
      final distance = _colorDistance(color, paletteColor);
      if (distance < minDistance) {
        minDistance = distance;
        closestColor = paletteColor;
      }
    }

    return closestColor;
  }

  /// Calcule la distance entre deux couleurs (espace RGB)
  static double _colorDistance(Color c1, Color c2) {
    final r = (c1.red - c2.red).toDouble();
    final g = (c1.green - c2.green).toDouble();
    final b = (c1.blue - c2.blue).toDouble();
    return r * r + g * g + b * b;
  }

  /// Obtient une couleur de contraste (noir ou blanc) pour le texte
  static Color getContrastColor(Color backgroundColor) {
    // Calcul de la luminance selon la norme W3C
    final luminance = (0.299 * backgroundColor.red +
            0.587 * backgroundColor.green +
            0.114 * backgroundColor.blue) /
        255;

    // Si la couleur est claire, utiliser du noir, sinon du blanc
    return luminance > 0.5 ? Colors.black : Colors.white;
  }

  /// Suggestions de couleurs par catégorie de type
  static const Map<String, Color> categorySuggestions = {
    'Infrastructure': bleuVif,
    'Assainissement': bleuFonce,
    'Eau': cyan,
    'Éclairage': jaune,
    'Signalisation': orange,
    'Mobilier': violet,
    'Nature': vertStandard,
    'Espaces verts': vertClair,
    'Voirie': marron,
    'Urgence': rouge,
    'Services': rose,
    'Technique': gris,
  };

  /// Obtient une suggestion de couleur pour un type
  static Color suggestColor(String typeName) {
    final lowerName = typeName.toLowerCase();

    for (final entry in categorySuggestions.entries) {
      if (lowerName.contains(entry.key.toLowerCase())) {
        return entry.value;
      }
    }

    // Couleur par défaut
    return bleuVif;
  }
}

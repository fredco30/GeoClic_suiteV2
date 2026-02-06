import 'dart:convert';

/// Entrée du Lexique - Menu en cascade hiérarchique
///
/// Le Lexique est le coeur de GéoClic V12 Pro. Il définit l'arborescence
/// de saisie avec profondeur illimitée.
///
/// Exemple :
/// ```
/// Éclairage public (level 0)
/// ├── Luminaire (level 1)
/// │   ├── LED → Form (level 2, triggers_form = true)
/// │   └── Sodium → Form
/// └── Mât (level 1)
///     ├── Acier → Form
///     └── Béton → Form
/// ```
class LexiqueEntry {
  /// ID auto-généré (null si nouveau)
  final int? id;

  /// Code unique : "ECLAIRAGE_LUMINAIRE_LED"
  final String code;

  /// Libellé affiché : "LED"
  final String label;

  /// Code du parent (null si racine)
  final String? parentCode;

  /// Niveau dans l'arborescence (0 = racine)
  final int level;

  /// Ordre d'affichage dans le niveau
  final int displayOrder;

  /// true = déclenche l'affichage du formulaire
  final bool triggersForm;

  /// Référence vers le TypeFieldConfig (si triggersForm = true)
  final String? formTypeRef;

  /// Nom de l'icône Font Awesome
  final String? iconName;

  /// Couleur ARGB
  final int? colorValue;

  /// Entrée active ou archivée
  final bool isActive;

  /// Métadonnées supplémentaires (JSONB)
  final Map<String, dynamic>? metadata;

  const LexiqueEntry({
    this.id,
    required this.code,
    required this.label,
    this.parentCode,
    this.level = 0,
    this.displayOrder = 0,
    this.triggersForm = false,
    this.formTypeRef,
    this.iconName,
    this.colorValue,
    this.isActive = true,
    this.metadata,
  });

  /// Génère un code à partir du parent et du label
  static String generateCode(String? parentCode, String label) {
    final normalizedLabel = label
        .toUpperCase()
        .replaceAll(RegExp(r'[^A-Z0-9]'), '_')
        .replaceAll(RegExp(r'_+'), '_');
    if (parentCode == null || parentCode.isEmpty) {
      return normalizedLabel;
    }
    return '${parentCode}_$normalizedLabel';
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'code': code,
      'label': label,
      'parent_code': parentCode,
      'level': level,
      'display_order': displayOrder,
      'triggers_form': triggersForm,
      'form_type_ref': formTypeRef,
      'icon_name': iconName,
      'color_value': colorValue,
      'is_active': isActive,
      'metadata': metadata,
    };
  }

  factory LexiqueEntry.fromJson(Map<String, dynamic> json) {
    return LexiqueEntry(
      id: json['id'],
      code: json['code'] ?? '',
      label: json['label'] ?? '',
      parentCode: json['parent_code'],
      level: json['level'] ?? 0,
      displayOrder: json['display_order'] ?? 0,
      triggersForm: json['triggers_form'] ?? false,
      formTypeRef: json['form_type_ref'],
      iconName: json['icon_name'],
      colorValue: json['color_value'],
      isActive: json['is_active'] ?? true,
      metadata: json['metadata'] != null
          ? Map<String, dynamic>.from(
              json['metadata'] is String
                  ? jsonDecode(json['metadata'])
                  : json['metadata'],
            )
          : null,
    );
  }

  LexiqueEntry copyWith({
    int? id,
    String? code,
    String? label,
    String? parentCode,
    int? level,
    int? displayOrder,
    bool? triggersForm,
    String? formTypeRef,
    String? iconName,
    int? colorValue,
    bool? isActive,
    Map<String, dynamic>? metadata,
  }) {
    return LexiqueEntry(
      id: id ?? this.id,
      code: code ?? this.code,
      label: label ?? this.label,
      parentCode: parentCode ?? this.parentCode,
      level: level ?? this.level,
      displayOrder: displayOrder ?? this.displayOrder,
      triggersForm: triggersForm ?? this.triggersForm,
      formTypeRef: formTypeRef ?? this.formTypeRef,
      iconName: iconName ?? this.iconName,
      colorValue: colorValue ?? this.colorValue,
      isActive: isActive ?? this.isActive,
      metadata: metadata ?? this.metadata,
    );
  }

  @override
  String toString() => 'LexiqueEntry($code, level: $level, form: $triggersForm)';
}

/// Arbre complet du Lexique avec méthodes de navigation
class LexiqueTree {
  final List<LexiqueEntry> _entries;

  LexiqueTree(this._entries);

  /// Toutes les entrées
  List<LexiqueEntry> get all => List.unmodifiable(_entries);

  /// Entrées racines (level 0, sans parent)
  List<LexiqueEntry> get roots => _entries
      .where((e) => e.parentCode == null && e.isActive)
      .toList()
    ..sort((a, b) => a.displayOrder.compareTo(b.displayOrder));

  /// Enfants d'une entrée
  List<LexiqueEntry> getChildren(String parentCode) => _entries
      .where((e) => e.parentCode == parentCode && e.isActive)
      .toList()
    ..sort((a, b) => a.displayOrder.compareTo(b.displayOrder));

  /// Recherche une entrée par code
  LexiqueEntry? findByCode(String code) {
    try {
      return _entries.firstWhere((e) => e.code == code);
    } catch (_) {
      return null;
    }
  }

  /// Chemin complet (breadcrumb) depuis la racine
  List<LexiqueEntry> getPath(String code) {
    final path = <LexiqueEntry>[];
    LexiqueEntry? current = findByCode(code);

    while (current != null) {
      path.insert(0, current);
      current = current.parentCode != null ? findByCode(current.parentCode!) : null;
    }

    return path;
  }

  /// Label complet avec séparateur
  String getFullLabel(String code, {String separator = ' > '}) {
    return getPath(code).map((e) => e.label).join(separator);
  }

  /// Entrées qui déclenchent un formulaire
  List<LexiqueEntry> get formTriggers =>
      _entries.where((e) => e.triggersForm && e.isActive).toList();

  /// Profondeur maximale de l'arbre
  int get maxDepth {
    if (_entries.isEmpty) return 0;
    return _entries.map((e) => e.level).reduce((a, b) => a > b ? a : b);
  }

  /// Vérifie si une entrée a des enfants
  bool hasChildren(String code) =>
      _entries.any((e) => e.parentCode == code && e.isActive);

  /// Compte les entrées par niveau
  Map<int, int> get countByLevel {
    final counts = <int, int>{};
    for (final entry in _entries.where((e) => e.isActive)) {
      counts[entry.level] = (counts[entry.level] ?? 0) + 1;
    }
    return counts;
  }
}

/// Templates métiers pré-configurés
class LexiqueTemplates {
  /// Template Éclairage Public
  static List<LexiqueEntry> get eclairagePublic => [
    const LexiqueEntry(
      code: 'ECLAIRAGE',
      label: 'Éclairage public',
      level: 0,
      iconName: 'lightbulb',
      colorValue: 0xFFFFEB3B,
    ),
    const LexiqueEntry(
      code: 'ECLAIRAGE_LUMINAIRE',
      label: 'Luminaire',
      parentCode: 'ECLAIRAGE',
      level: 1,
    ),
    const LexiqueEntry(
      code: 'ECLAIRAGE_LUMINAIRE_LED',
      label: 'LED',
      parentCode: 'ECLAIRAGE_LUMINAIRE',
      level: 2,
      triggersForm: true,
      formTypeRef: 'luminaire_led',
    ),
    const LexiqueEntry(
      code: 'ECLAIRAGE_LUMINAIRE_SODIUM',
      label: 'Sodium',
      parentCode: 'ECLAIRAGE_LUMINAIRE',
      level: 2,
      triggersForm: true,
      formTypeRef: 'luminaire_sodium',
    ),
    const LexiqueEntry(
      code: 'ECLAIRAGE_MAT',
      label: 'Mât',
      parentCode: 'ECLAIRAGE',
      level: 1,
    ),
    const LexiqueEntry(
      code: 'ECLAIRAGE_MAT_ACIER',
      label: 'Acier',
      parentCode: 'ECLAIRAGE_MAT',
      level: 2,
      triggersForm: true,
      formTypeRef: 'mat_acier',
    ),
    const LexiqueEntry(
      code: 'ECLAIRAGE_MAT_BETON',
      label: 'Béton',
      parentCode: 'ECLAIRAGE_MAT',
      level: 2,
      triggersForm: true,
      formTypeRef: 'mat_beton',
    ),
  ];

  /// Template Mobilier Urbain
  static List<LexiqueEntry> get mobilierUrbain => [
    const LexiqueEntry(
      code: 'MOBILIER',
      label: 'Mobilier urbain',
      level: 0,
      iconName: 'chair',
      colorValue: 0xFF795548,
    ),
    const LexiqueEntry(
      code: 'MOBILIER_BANC',
      label: 'Banc',
      parentCode: 'MOBILIER',
      level: 1,
      triggersForm: true,
      formTypeRef: 'banc',
    ),
    const LexiqueEntry(
      code: 'MOBILIER_POUBELLE',
      label: 'Poubelle',
      parentCode: 'MOBILIER',
      level: 1,
      triggersForm: true,
      formTypeRef: 'poubelle',
    ),
    const LexiqueEntry(
      code: 'MOBILIER_ABRI',
      label: 'Abri bus',
      parentCode: 'MOBILIER',
      level: 1,
      triggersForm: true,
      formTypeRef: 'abri_bus',
    ),
  ];

  /// Template Aires de Jeux
  static List<LexiqueEntry> get airesDeJeux => [
    const LexiqueEntry(
      code: 'AIRE_JEUX',
      label: 'Aire de jeux',
      level: 0,
      iconName: 'users',
      colorValue: 0xFF4CAF50,
    ),
    const LexiqueEntry(
      code: 'AIRE_JEUX_TOBOGGAN',
      label: 'Toboggan',
      parentCode: 'AIRE_JEUX',
      level: 1,
    ),
    const LexiqueEntry(
      code: 'AIRE_JEUX_TOBOGGAN_FIXATIONS',
      label: 'Fixations',
      parentCode: 'AIRE_JEUX_TOBOGGAN',
      level: 2,
      triggersForm: true,
      formTypeRef: 'jeux_fixation',
    ),
    const LexiqueEntry(
      code: 'AIRE_JEUX_TOBOGGAN_GLISSIERE',
      label: 'Glissière',
      parentCode: 'AIRE_JEUX_TOBOGGAN',
      level: 2,
      triggersForm: true,
      formTypeRef: 'jeux_plastique',
    ),
    const LexiqueEntry(
      code: 'AIRE_JEUX_BALANCOIRE',
      label: 'Balançoire',
      parentCode: 'AIRE_JEUX',
      level: 1,
      triggersForm: true,
      formTypeRef: 'jeux_balancoire',
    ),
  ];

  /// Tous les templates disponibles
  static Map<String, List<LexiqueEntry>> get all => {
    'eclairage_public': eclairagePublic,
    'mobilier_urbain': mobilierUrbain,
    'aires_de_jeux': airesDeJeux,
  };
}

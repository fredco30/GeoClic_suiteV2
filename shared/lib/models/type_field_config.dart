import 'dart:convert';

/// Types de champs disponibles pour les formulaires dynamiques
enum FieldType {
  text('text', 'Texte libre', 'abc'),
  number('number', 'Nombre', '123'),
  dropdown('dropdown', 'Liste déroulante', '▼'),
  date('date', 'Date', '📅'),
  checkbox('checkbox', 'Case à cocher', '☑'),
  photo('photo', 'Photo', '📷');

  final String value;
  final String label;
  final String icon;

  const FieldType(this.value, this.label, this.icon);

  static FieldType fromString(String? value) {
    if (value == null || value.isEmpty) return FieldType.text;
    return FieldType.values.firstWhere(
      (f) => f.value == value,
      orElse: () => FieldType.text,
    );
  }

  /// Convertit en type SQL pour les colonnes geoclic_*
  String toSqlType() {
    switch (this) {
      case FieldType.text:
        return 'TEXT';
      case FieldType.number:
        return 'DOUBLE PRECISION';
      case FieldType.dropdown:
        return 'VARCHAR(255)';
      case FieldType.date:
        return 'DATE';
      case FieldType.checkbox:
        return 'BOOLEAN DEFAULT FALSE';
      case FieldType.photo:
        return 'JSONB'; // Stocke les métadonnées photo
    }
  }
}

/// Configuration d'un champ dynamique pour un type de point
///
/// Définit la structure des formulaires de saisie.
/// Les champs sont associés à un type (via formTypeRef du Lexique).
class TypeFieldConfig {
  final int? id;

  /// Nom du type associé (ex: "luminaire_led")
  final String typeName;

  /// Nom technique du champ (ex: "puissance_w")
  final String fieldName;

  /// Libellé affiché (ex: "Puissance (W)")
  final String fieldLabel;

  /// Type de champ
  final FieldType fieldType;

  /// Champ obligatoire ?
  final bool isRequired;

  /// Options pour les dropdowns
  final List<String>? dropdownOptions;

  /// Valeur par défaut
  final String? defaultValue;

  /// Ordre d'affichage
  final int displayOrder;

  /// Unité (ex: "m", "W", "€")
  final String? unit;

  /// Valeur minimale (pour number)
  final double? minValue;

  /// Valeur maximale (pour number)
  final double? maxValue;

  /// Champ standard (colonne SQL dédiée) vs custom (JSONB)
  final bool isStandardField;

  /// Description/aide pour l'utilisateur
  final String? helpText;

  const TypeFieldConfig({
    this.id,
    required this.typeName,
    required this.fieldName,
    required this.fieldLabel,
    required this.fieldType,
    this.isRequired = false,
    this.dropdownOptions,
    this.defaultValue,
    this.displayOrder = 0,
    this.unit,
    this.minValue,
    this.maxValue,
    this.isStandardField = false,
    this.helpText,
  });

  /// Nom de la colonne SQL (avec préfixe geoclic_ si custom)
  String get sqlColumnName =>
      isStandardField ? fieldName : 'geoclic_$fieldName';

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type_name': typeName,
      'field_name': fieldName,
      'field_label': fieldLabel,
      'field_type': fieldType.value,
      'is_required': isRequired,
      'dropdown_options':
          dropdownOptions != null ? jsonEncode(dropdownOptions) : null,
      'default_value': defaultValue,
      'display_order': displayOrder,
      'unit': unit,
      'min_value': minValue,
      'max_value': maxValue,
      'is_standard_field': isStandardField,
      'help_text': helpText,
    };
  }

  factory TypeFieldConfig.fromJson(Map<String, dynamic> json) {
    List<String>? options;
    if (json['dropdown_options'] != null) {
      if (json['dropdown_options'] is String) {
        options = List<String>.from(jsonDecode(json['dropdown_options']));
      } else if (json['dropdown_options'] is List) {
        options = List<String>.from(json['dropdown_options']);
      }
    }

    return TypeFieldConfig(
      id: json['id'],
      typeName: json['type_name'] ?? '',
      fieldName: json['field_name'] ?? '',
      fieldLabel: json['field_label'] ?? '',
      fieldType: FieldType.fromString(json['field_type']),
      isRequired: json['is_required'] ?? false,
      dropdownOptions: options,
      defaultValue: json['default_value'],
      displayOrder: json['display_order'] ?? 0,
      unit: json['unit'],
      minValue: json['min_value']?.toDouble(),
      maxValue: json['max_value']?.toDouble(),
      isStandardField: json['is_standard_field'] ?? false,
      helpText: json['help_text'],
    );
  }

  TypeFieldConfig copyWith({
    int? id,
    String? typeName,
    String? fieldName,
    String? fieldLabel,
    FieldType? fieldType,
    bool? isRequired,
    List<String>? dropdownOptions,
    String? defaultValue,
    int? displayOrder,
    String? unit,
    double? minValue,
    double? maxValue,
    bool? isStandardField,
    String? helpText,
  }) {
    return TypeFieldConfig(
      id: id ?? this.id,
      typeName: typeName ?? this.typeName,
      fieldName: fieldName ?? this.fieldName,
      fieldLabel: fieldLabel ?? this.fieldLabel,
      fieldType: fieldType ?? this.fieldType,
      isRequired: isRequired ?? this.isRequired,
      dropdownOptions: dropdownOptions ?? this.dropdownOptions,
      defaultValue: defaultValue ?? this.defaultValue,
      displayOrder: displayOrder ?? this.displayOrder,
      unit: unit ?? this.unit,
      minValue: minValue ?? this.minValue,
      maxValue: maxValue ?? this.maxValue,
      isStandardField: isStandardField ?? this.isStandardField,
      helpText: helpText ?? this.helpText,
    );
  }

  @override
  String toString() => 'TypeFieldConfig($typeName.$fieldName, ${fieldType.value})';
}

/// Catalogue des champs standards pré-définis
///
/// Ces champs correspondent à des colonnes SQL dédiées (pas JSONB).
/// Privilégier les dropdowns pour garantir des données propres.
class StandardFields {
  static const List<Map<String, dynamic>> all = [
    // ═══════════════════════════════════════════════════════════════════════
    // IDENTIFICATION
    // ═══════════════════════════════════════════════════════════════════════
    {
      'fieldName': 'materiau',
      'fieldLabel': 'Matériau',
      'fieldType': 'dropdown',
      'defaultOptions': [
        'Acier',
        'Acier galvanisé',
        'Aluminium',
        'Béton',
        'Bois',
        'Bois traité',
        'Fonte',
        'Inox',
        'PVC',
        'Pierre',
        'Plastique',
        'Composite'
      ],
    },
    {
      'fieldName': 'marque_modele',
      'fieldLabel': 'Marque / Modèle',
      'fieldType': 'text',
    },

    // ═══════════════════════════════════════════════════════════════════════
    // DIMENSIONS
    // ═══════════════════════════════════════════════════════════════════════
    {
      'fieldName': 'hauteur',
      'fieldLabel': 'Hauteur',
      'fieldType': 'dropdown',
      'unit': 'm',
      'defaultOptions': [
        '0.5',
        '1.0',
        '1.5',
        '2.0',
        '2.5',
        '3.0',
        '3.5',
        '4.0',
        '4.5',
        '5.0',
        '6.0',
        '7.0',
        '8.0',
        '10.0',
        '12.0'
      ],
    },
    {
      'fieldName': 'largeur',
      'fieldLabel': 'Largeur',
      'fieldType': 'dropdown',
      'unit': 'm',
      'defaultOptions': [
        '0.3',
        '0.5',
        '0.8',
        '1.0',
        '1.2',
        '1.5',
        '2.0',
        '2.5',
        '3.0'
      ],
    },

    // ═══════════════════════════════════════════════════════════════════════
    // DATES
    // ═══════════════════════════════════════════════════════════════════════
    {
      'fieldName': 'date_installation',
      'fieldLabel': 'Date d\'installation',
      'fieldType': 'date',
    },
    {
      'fieldName': 'duree_vie_annees',
      'fieldLabel': 'Durée de vie (années)',
      'fieldType': 'number',
    },

    // ═══════════════════════════════════════════════════════════════════════
    // MAINTENANCE
    // ═══════════════════════════════════════════════════════════════════════
    {
      'fieldName': 'date_derniere_intervention',
      'fieldLabel': 'Dernière intervention',
      'fieldType': 'date',
    },
    {
      'fieldName': 'date_prochaine_intervention',
      'fieldLabel': 'Prochaine intervention',
      'fieldType': 'date',
    },
    {
      'fieldName': 'priorite',
      'fieldLabel': 'Priorité',
      'fieldType': 'dropdown',
      'defaultOptions': ['Urgent', 'Normal', 'Faible'],
    },
    {
      'fieldName': 'cout_remplacement',
      'fieldLabel': 'Coût de remplacement',
      'fieldType': 'number',
      'unit': '€',
    },

    // ═══════════════════════════════════════════════════════════════════════
    // ÉTAT
    // ═══════════════════════════════════════════════════════════════════════
    {
      'fieldName': 'condition_etat',
      'fieldLabel': 'État / Condition',
      'fieldType': 'dropdown',
      'defaultOptions': [
        'Neuf',
        'Très bon',
        'Bon',
        'Moyen',
        'Mauvais',
        'Hors service',
        'À remplacer'
      ],
    },

    // ═══════════════════════════════════════════════════════════════════════
    // CONFORMITÉ
    // ═══════════════════════════════════════════════════════════════════════
    {
      'fieldName': 'conforme_norme',
      'fieldLabel': 'Conforme aux normes',
      'fieldType': 'checkbox',
    },
    {
      'fieldName': 'accessibilite_pmr',
      'fieldLabel': 'Accessibilité PMR',
      'fieldType': 'checkbox',
    },
  ];

  /// Obtient un champ standard par son nom
  static Map<String, dynamic>? getByName(String fieldName) {
    try {
      return all.firstWhere((f) => f['fieldName'] == fieldName);
    } catch (_) {
      return null;
    }
  }

  /// Vérifie si c'est un champ standard
  static bool isStandard(String fieldName) {
    return all.any((f) => f['fieldName'] == fieldName);
  }

  /// Crée un TypeFieldConfig depuis un champ standard
  static TypeFieldConfig createConfig(String fieldName, String typeName) {
    final standard = getByName(fieldName);
    if (standard == null) {
      return TypeFieldConfig(
        typeName: typeName,
        fieldName: fieldName,
        fieldLabel: fieldName,
        fieldType: FieldType.text,
        isStandardField: false,
      );
    }

    return TypeFieldConfig(
      typeName: typeName,
      fieldName: standard['fieldName'],
      fieldLabel: standard['fieldLabel'],
      fieldType: FieldType.fromString(standard['fieldType']),
      dropdownOptions: standard['defaultOptions'] != null
          ? List<String>.from(standard['defaultOptions'])
          : null,
      unit: standard['unit'],
      isStandardField: true,
    );
  }
}

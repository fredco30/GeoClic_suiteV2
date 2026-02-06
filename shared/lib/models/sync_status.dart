/// Statuts de synchronisation pour le workflow de validation
///
/// Workflow complet :
/// draft → pending → validated → published (dans OGS)
///                 ↘ rejected (retour à l'agent)
enum SyncStatus {
  /// Brouillon local, non soumis
  draft('draft', 'Brouillon', 'Sauvegardé localement'),

  /// Soumis pour validation par le modérateur
  pending('pending', 'En attente', 'Soumis pour validation'),

  /// Validé par le modérateur, prêt pour publication OGS
  validated('validated', 'Validé', 'Approuvé par le modérateur'),

  /// Rejeté par le modérateur, nécessite correction
  rejected('rejected', 'Rejeté', 'Corrections demandées'),

  /// Publié dans la table OGS de production
  published('published', 'Publié', 'Données dans OGS'),

  /// En cours de synchronisation
  syncing('syncing', 'Synchronisation', 'Envoi en cours...'),

  /// Erreur de synchronisation
  error('error', 'Erreur', 'Échec de synchronisation');

  final String value;
  final String label;
  final String description;

  const SyncStatus(this.value, this.label, this.description);

  /// Convertit une chaîne en SyncStatus
  static SyncStatus fromString(String? value) {
    if (value == null || value.isEmpty) return SyncStatus.draft;
    return SyncStatus.values.firstWhere(
      (s) => s.value == value.toLowerCase(),
      orElse: () => SyncStatus.draft,
    );
  }

  /// Indique si le point est modifiable par l'agent
  bool get isEditable => this == draft || this == rejected;

  /// Indique si le point est en attente de validation
  bool get isPendingReview => this == pending;

  /// Indique si le point est finalisé (validé ou publié)
  bool get isFinalized => this == validated || this == published;

  /// Indique si le point peut être soumis pour validation
  bool get canSubmit => this == draft || this == rejected;

  /// Couleur associée au statut (valeur ARGB)
  int get colorValue {
    switch (this) {
      case SyncStatus.draft:
        return 0xFF9E9E9E; // Gris
      case SyncStatus.pending:
        return 0xFFFF9800; // Orange
      case SyncStatus.validated:
        return 0xFF4CAF50; // Vert
      case SyncStatus.rejected:
        return 0xFFF44336; // Rouge
      case SyncStatus.published:
        return 0xFF2196F3; // Bleu
      case SyncStatus.syncing:
        return 0xFF9C27B0; // Violet
      case SyncStatus.error:
        return 0xFFE91E63; // Rose
    }
  }
}

/// Statuts possibles d'un élément de patrimoine
enum PointStatus {
  projet('Projet', 'À faire', 0xFF2196F3),
  enCours('En cours', 'En cours de traitement', 0xFFFF9800),
  realise('Réalisé', 'Terminé', 0xFF4CAF50),
  annule('Annulé', 'Annulé', 0xFF9E9E9E);

  final String label;
  final String description;
  final int colorValue;

  const PointStatus(this.label, this.description, this.colorValue);

  static PointStatus fromString(String? value) {
    if (value == null || value.isEmpty) return PointStatus.projet;
    return PointStatus.values.firstWhere(
      (s) => s.label.toLowerCase() == value.toLowerCase(),
      orElse: () => PointStatus.projet,
    );
  }
}

/// États de condition d'un élément de patrimoine
enum ConditionState {
  neuf('Neuf', 0xFF4CAF50),
  tresBon('Très bon', 0xFF66BB6A),
  bon('Bon', 0xFF8BC34A),
  moyen('Moyen', 0xFFFFEB3B),
  mauvais('Mauvais', 0xFFFF9800),
  horsService('Hors service', 0xFFF44336),
  aRemplacer('À remplacer', 0xFF9C27B0);

  final String label;
  final int colorValue;

  const ConditionState(this.label, this.colorValue);

  static ConditionState fromString(String? value) {
    if (value == null || value.isEmpty) return ConditionState.neuf;
    return ConditionState.values.firstWhere(
      (s) => s.label.toLowerCase() == value.toLowerCase(),
      orElse: () => ConditionState.neuf,
    );
  }

  /// Liste des labels pour les dropdowns
  static List<String> get labels => values.map((e) => e.label).toList();
}

/// Types de géométrie supportés
enum GeometryType {
  point('POINT'),
  line('LINESTRING'),
  polygon('POLYGON');

  final String wktType;

  const GeometryType(this.wktType);

  static GeometryType fromString(String? value) {
    if (value == null || value.isEmpty) return GeometryType.point;
    switch (value.toUpperCase()) {
      case 'POINT':
        return GeometryType.point;
      case 'LINE':
      case 'LINESTRING':
        return GeometryType.line;
      case 'POLYGON':
      case 'MULTIPOLYGON':
        return GeometryType.polygon;
      default:
        return GeometryType.point;
    }
  }
}

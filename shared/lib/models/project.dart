/// Projet/Chantier GéoClic V12 Pro
///
/// Un projet regroupe des points liés à une campagne de saisie.
class Project {
  /// UUID unique
  final String? id;

  /// Nom du projet
  final String name;

  /// Description détaillée
  final String? description;

  /// Statut (En cours, Terminé, Archivé)
  final String status;

  /// Projet actif ou archivé
  final bool isActive;

  /// Nombre de points associés (calculé)
  final int? pointCount;

  /// Emprise géographique (bounds)
  final double? minLat;
  final double? maxLat;
  final double? minLng;
  final double? maxLng;

  /// Informations collectivité
  final String? collectiviteName;
  final String? collectiviteAddress;
  final String? responsableName;
  final String? responsableEmail;

  /// Dates
  final DateTime createdAt;
  final DateTime? updatedAt;
  final DateTime? startDate;
  final DateTime? endDate;

  /// Métadonnées supplémentaires
  final Map<String, dynamic>? metadata;

  const Project({
    this.id,
    required this.name,
    this.description,
    this.status = 'En cours',
    this.isActive = true,
    this.pointCount,
    this.minLat,
    this.maxLat,
    this.minLng,
    this.maxLng,
    this.collectiviteName,
    this.collectiviteAddress,
    this.responsableName,
    this.responsableEmail,
    required this.createdAt,
    this.updatedAt,
    this.startDate,
    this.endDate,
    this.metadata,
  });

  /// Indique si le projet a des bounds définies
  bool get hasBounds =>
      minLat != null && maxLat != null && minLng != null && maxLng != null;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'status': status,
      'is_active': isActive,
      'point_count': pointCount,
      'min_lat': minLat,
      'max_lat': maxLat,
      'min_lng': minLng,
      'max_lng': maxLng,
      'collectivite_name': collectiviteName,
      'collectivite_address': collectiviteAddress,
      'responsable_name': responsableName,
      'responsable_email': responsableEmail,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
      'start_date': startDate?.toIso8601String(),
      'end_date': endDate?.toIso8601String(),
      'metadata': metadata,
    };
  }

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: json['id']?.toString(),
      name: json['name'] ?? 'Sans nom',
      description: json['description'],
      status: json['status'] ?? 'En cours',
      isActive: json['is_active'] ?? true,
      pointCount: json['point_count'],
      minLat: json['min_lat']?.toDouble(),
      maxLat: json['max_lat']?.toDouble(),
      minLng: json['min_lng']?.toDouble(),
      maxLng: json['max_lng']?.toDouble(),
      collectiviteName: json['collectivite_name'],
      collectiviteAddress: json['collectivite_address'],
      responsableName: json['responsable_name'],
      responsableEmail: json['responsable_email'],
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'])
          : null,
      startDate: json['start_date'] != null
          ? DateTime.tryParse(json['start_date'])
          : null,
      endDate: json['end_date'] != null
          ? DateTime.tryParse(json['end_date'])
          : null,
      metadata: json['metadata'] != null
          ? Map<String, dynamic>.from(json['metadata'])
          : null,
    );
  }

  Project copyWith({
    String? id,
    String? name,
    String? description,
    String? status,
    bool? isActive,
    int? pointCount,
    double? minLat,
    double? maxLat,
    double? minLng,
    double? maxLng,
    String? collectiviteName,
    String? collectiviteAddress,
    String? responsableName,
    String? responsableEmail,
    DateTime? createdAt,
    DateTime? updatedAt,
    DateTime? startDate,
    DateTime? endDate,
    Map<String, dynamic>? metadata,
  }) {
    return Project(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      status: status ?? this.status,
      isActive: isActive ?? this.isActive,
      pointCount: pointCount ?? this.pointCount,
      minLat: minLat ?? this.minLat,
      maxLat: maxLat ?? this.maxLat,
      minLng: minLng ?? this.minLng,
      maxLng: maxLng ?? this.maxLng,
      collectiviteName: collectiviteName ?? this.collectiviteName,
      collectiviteAddress: collectiviteAddress ?? this.collectiviteAddress,
      responsableName: responsableName ?? this.responsableName,
      responsableEmail: responsableEmail ?? this.responsableEmail,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      startDate: startDate ?? this.startDate,
      endDate: endDate ?? this.endDate,
      metadata: metadata ?? this.metadata,
    );
  }

  @override
  String toString() => 'Project($name, status: $status, points: $pointCount)';
}

/// Statuts possibles d'un projet
class ProjectStatus {
  static const String enCours = 'En cours';
  static const String termine = 'Terminé';
  static const String archive = 'Archivé';
  static const String suspendu = 'Suspendu';

  static const List<String> all = [enCours, termine, archive, suspendu];
}

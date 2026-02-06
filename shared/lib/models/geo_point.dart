import 'dart:convert';
import 'dart:math';
import 'package:latlong2/latlong.dart';

import 'sync_status.dart';
import 'photo_metadata.dart';

/// Modèle principal pour les points géographiques GéoClic V12 Pro
///
/// Supporte POINT, LINESTRING et POLYGON avec :
/// - Référence au Lexique (code hiérarchique)
/// - Workflow de validation (draft → pending → validated → published)
/// - Photos multiples avec métadonnées EXIF
/// - Propriétés dynamiques (JSONB)
/// - Traçabilité complète (qui, quand, depuis quelle source)
class GeoPoint {
  // ═══════════════════════════════════════════════════════════════════════════
  // IDENTIFICATION
  // ═══════════════════════════════════════════════════════════════════════════

  /// UUID unique (compatible PostGIS)
  final String? id;

  /// Nom/désignation du point
  final String name;

  /// Code du Lexique (ex: "ECLAIRAGE_LUMINAIRE_LED")
  final String? lexiqueCode;

  /// Type principal (legacy, déduit du lexiqueCode)
  final String type;

  /// Sous-type (legacy, déduit du lexiqueCode)
  final String? subtype;

  // ═══════════════════════════════════════════════════════════════════════════
  // GÉOMÉTRIE
  // ═══════════════════════════════════════════════════════════════════════════

  /// Type de géométrie (POINT, LINESTRING, POLYGON)
  final GeometryType geomType;

  /// Liste des coordonnées (1 pour POINT, N pour LINE/POLYGON)
  final List<LatLng> coordinates;

  /// Précision GPS en mètres
  final double? gpsPrecision;

  /// Source GPS (gps, network, manual)
  final String? gpsSource;

  /// Altitude en mètres
  final double? altitude;

  // ═══════════════════════════════════════════════════════════════════════════
  // ÉTAT & WORKFLOW
  // ═══════════════════════════════════════════════════════════════════════════

  /// État physique (Neuf, Bon, Mauvais...)
  final ConditionState condition;

  /// Statut métier (Projet, En cours, Réalisé)
  final PointStatus status;

  /// Statut de synchronisation (draft, pending, validated, published)
  final SyncStatus syncStatus;

  /// Commentaire de rejet (si syncStatus == rejected)
  final String? rejectionComment;

  /// Commentaire général
  final String? comment;

  // ═══════════════════════════════════════════════════════════════════════════
  // PHOTOS
  // ═══════════════════════════════════════════════════════════════════════════

  /// Liste des photos avec métadonnées
  final List<PhotoMetadata> photos;

  /// Chemin legacy (première photo)
  String? get imagePath => photos.isNotEmpty ? photos.first.url : null;

  // ═══════════════════════════════════════════════════════════════════════════
  // ATTRIBUTS TECHNIQUES
  // ═══════════════════════════════════════════════════════════════════════════

  /// Matériau (Acier, Béton, Bois...)
  final String? materiau;

  /// Hauteur en mètres
  final double? hauteur;

  /// Largeur en mètres
  final double? largeur;

  /// Date d'installation
  final DateTime? dateInstallation;

  /// Durée de vie estimée en années
  final int? dureeVieAnnees;

  /// Marque et modèle
  final String? marqueModele;

  // ═══════════════════════════════════════════════════════════════════════════
  // MAINTENANCE
  // ═══════════════════════════════════════════════════════════════════════════

  /// Date de dernière intervention
  final DateTime? dateDerniereIntervention;

  /// Date de prochaine intervention prévue
  final DateTime? dateProchaineIntervention;

  /// Priorité (Urgent, Normal, Faible)
  final String? priorite;

  /// Coût estimé de remplacement
  final double? coutRemplacement;

  // ═══════════════════════════════════════════════════════════════════════════
  // PROPRIÉTÉS DYNAMIQUES (JSONB)
  // ═══════════════════════════════════════════════════════════════════════════

  /// Propriétés personnalisées définies par TypeFieldConfig
  final Map<String, dynamic>? customProperties;

  // ═══════════════════════════════════════════════════════════════════════════
  // CONTEXTE & TRAÇABILITÉ
  // ═══════════════════════════════════════════════════════════════════════════

  /// ID du projet associé
  final String? projectId;

  /// Nom de la zone (jointure spatiale)
  final String zoneName;

  /// Table OGS source (traçabilité import)
  final String? sourceTable;

  /// ID dans la table OGS source
  final String? sourceId;

  /// Créé par (email ou identifiant)
  final String? createdBy;

  /// Modifié par
  final String? updatedBy;

  /// Date de création
  final DateTime createdAt;

  /// Date de modification
  final DateTime? updatedAt;

  // ═══════════════════════════════════════════════════════════════════════════
  // AFFICHAGE
  // ═══════════════════════════════════════════════════════════════════════════

  /// Couleur ARGB pour la carte
  final int? colorValue;

  /// Nom de l'icône
  final String? iconName;

  /// Épaisseur du trait (lignes/polygones)
  final double? strokeWidth;

  // ═══════════════════════════════════════════════════════════════════════════
  // CONSTRUCTEUR
  // ═══════════════════════════════════════════════════════════════════════════

  GeoPoint({
    this.id,
    required this.name,
    this.lexiqueCode,
    required this.type,
    this.subtype,
    required this.geomType,
    required this.coordinates,
    this.gpsPrecision,
    this.gpsSource,
    this.altitude,
    this.condition = ConditionState.neuf,
    this.status = PointStatus.projet,
    this.syncStatus = SyncStatus.draft,
    this.rejectionComment,
    this.comment,
    List<PhotoMetadata>? photos,
    this.materiau,
    this.hauteur,
    this.largeur,
    this.dateInstallation,
    this.dureeVieAnnees,
    this.marqueModele,
    this.dateDerniereIntervention,
    this.dateProchaineIntervention,
    this.priorite,
    this.coutRemplacement,
    this.customProperties,
    this.projectId,
    this.zoneName = 'Default',
    this.sourceTable,
    this.sourceId,
    this.createdBy,
    this.updatedBy,
    DateTime? createdAt,
    this.updatedAt,
    this.colorValue,
    this.iconName,
    this.strokeWidth,
  })  : photos = photos ?? [],
        createdAt = createdAt ?? DateTime.now();

  // ═══════════════════════════════════════════════════════════════════════════
  // CALCULS GÉOMÉTRIQUES
  // ═══════════════════════════════════════════════════════════════════════════

  /// Longueur totale pour les lignes (en mètres)
  double get length {
    if (geomType != GeometryType.line || coordinates.length < 2) return 0.0;
    final distance = const Distance();
    double total = 0.0;
    for (int i = 0; i < coordinates.length - 1; i++) {
      total += distance.as(LengthUnit.Meter, coordinates[i], coordinates[i + 1]);
    }
    return total;
  }

  /// Surface pour les polygones (en m²)
  double get area {
    if (geomType != GeometryType.polygon || coordinates.length < 3) return 0.0;
    const double radius = 6378137.0;
    double area = 0.0;
    List<LatLng> poly = List.from(coordinates);
    if (poly.isNotEmpty && poly.last != poly.first) {
      poly.add(poly.first);
    }
    for (int i = 0; i < poly.length - 1; i++) {
      var p1 = poly[i];
      var p2 = poly[i + 1];
      area += (pi / 180) *
          (p2.longitude - p1.longitude) *
          (2 + sin(p1.latitude * pi / 180) + sin(p2.latitude * pi / 180));
    }
    area = area * radius * radius / 2.0;
    return area.abs();
  }

  /// Centre géométrique
  LatLng get center {
    if (coordinates.isEmpty) return const LatLng(0, 0);
    if (coordinates.length == 1) return coordinates.first;

    double sumLat = 0, sumLng = 0;
    for (var coord in coordinates) {
      sumLat += coord.latitude;
      sumLng += coord.longitude;
    }
    return LatLng(sumLat / coordinates.length, sumLng / coordinates.length);
  }

  /// Latitude (premier point)
  double get latitude => coordinates.isNotEmpty ? coordinates.first.latitude : 0;

  /// Longitude (premier point)
  double get longitude => coordinates.isNotEmpty ? coordinates.first.longitude : 0;

  // ═══════════════════════════════════════════════════════════════════════════
  // CONVERSION WKT (Well-Known Text)
  // ═══════════════════════════════════════════════════════════════════════════

  /// Convertit en WKT pour PostGIS
  String toWKT() {
    if (coordinates.isEmpty) return '';

    switch (geomType) {
      case GeometryType.point:
        return 'POINT(${coordinates[0].longitude} ${coordinates[0].latitude})';
      case GeometryType.line:
        if (coordinates.length < 2) {
          return 'POINT(${coordinates[0].longitude} ${coordinates[0].latitude})';
        }
        final coords =
            coordinates.map((p) => '${p.longitude} ${p.latitude}').join(', ');
        return 'LINESTRING($coords)';
      case GeometryType.polygon:
        if (coordinates.length < 3) {
          if (coordinates.length == 1) {
            return 'POINT(${coordinates[0].longitude} ${coordinates[0].latitude})';
          }
          final coords =
              coordinates.map((p) => '${p.longitude} ${p.latitude}').join(', ');
          return 'LINESTRING($coords)';
        }
        List<LatLng> poly = List.from(coordinates);
        if (poly.first != poly.last) poly.add(poly.first);
        final coords = poly.map((p) => '${p.longitude} ${p.latitude}').join(', ');
        return 'POLYGON(($coords))';
    }
  }

  /// Parse WKT en coordonnées
  static List<LatLng> parseWKT(String wkt) {
    final coords = <LatLng>[];
    final regex = RegExp(r'(-?\d+\.?\d*)\s+(-?\d+\.?\d*)');
    for (final match in regex.allMatches(wkt)) {
      final lng = double.tryParse(match.group(1) ?? '0') ?? 0;
      final lat = double.tryParse(match.group(2) ?? '0') ?? 0;
      coords.add(LatLng(lat, lng));
    }
    return coords;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SÉRIALISATION JSON
  // ═══════════════════════════════════════════════════════════════════════════

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'lexique_code': lexiqueCode,
      'type': type,
      'subtype': subtype,
      'geom_type': geomType.wktType,
      'geom_coords': jsonEncode(
          coordinates.map((p) => [p.latitude, p.longitude]).toList()),
      'gps_precision': gpsPrecision,
      'gps_source': gpsSource,
      'altitude': altitude,
      'condition': condition.label,
      'status': status.label,
      'sync_status': syncStatus.value,
      'rejection_comment': rejectionComment,
      'comment': comment,
      'photos': photos.map((p) => p.toJson()).toList(),
      'materiau': materiau,
      'hauteur': hauteur,
      'largeur': largeur,
      'date_installation': dateInstallation?.toIso8601String(),
      'duree_vie_annees': dureeVieAnnees,
      'marque_modele': marqueModele,
      'date_derniere_intervention': dateDerniereIntervention?.toIso8601String(),
      'date_prochaine_intervention': dateProchaineIntervention?.toIso8601String(),
      'priorite': priorite,
      'cout_remplacement': coutRemplacement,
      'custom_properties': customProperties,
      'project_id': projectId,
      'zone_name': zoneName,
      'source_table': sourceTable,
      'source_id': sourceId,
      'created_by': createdBy,
      'updated_by': updatedBy,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
      'color_value': colorValue,
      'icon_name': iconName,
      'stroke_width': strokeWidth,
    };
  }

  factory GeoPoint.fromJson(Map<String, dynamic> json) {
    // Parse coordinates
    List<LatLng> coords = [];
    if (json['geom_coords'] != null) {
      try {
        final List<dynamic> raw = json['geom_coords'] is String
            ? jsonDecode(json['geom_coords'])
            : json['geom_coords'];
        coords = raw.map((p) => LatLng(p[0].toDouble(), p[1].toDouble())).toList();
      } catch (_) {}
    }

    // Parse photos
    List<PhotoMetadata> photos = [];
    if (json['photos'] != null) {
      try {
        final List<dynamic> rawPhotos =
            json['photos'] is String ? jsonDecode(json['photos']) : json['photos'];
        photos = rawPhotos.map((p) => PhotoMetadata.fromJson(p)).toList();
      } catch (_) {}
    }

    return GeoPoint(
      id: json['id']?.toString(),
      name: json['name'] ?? 'Sans nom',
      lexiqueCode: json['lexique_code'],
      type: json['type'] ?? 'Autre',
      subtype: json['subtype'],
      geomType: GeometryType.fromString(json['geom_type']),
      coordinates: coords,
      gpsPrecision: json['gps_precision']?.toDouble(),
      gpsSource: json['gps_source'],
      altitude: json['altitude']?.toDouble(),
      condition: ConditionState.fromString(json['condition'] ?? json['etat']),
      status: PointStatus.fromString(json['status']),
      syncStatus: SyncStatus.fromString(json['sync_status']),
      rejectionComment: json['rejection_comment'],
      comment: json['comment'],
      photos: photos,
      materiau: json['materiau'],
      hauteur: json['hauteur']?.toDouble(),
      largeur: json['largeur']?.toDouble(),
      dateInstallation: json['date_installation'] != null
          ? DateTime.tryParse(json['date_installation'])
          : null,
      dureeVieAnnees: json['duree_vie_annees'],
      marqueModele: json['marque_modele'],
      dateDerniereIntervention: json['date_derniere_intervention'] != null
          ? DateTime.tryParse(json['date_derniere_intervention'])
          : null,
      dateProchaineIntervention: json['date_prochaine_intervention'] != null
          ? DateTime.tryParse(json['date_prochaine_intervention'])
          : null,
      priorite: json['priorite'],
      coutRemplacement: json['cout_remplacement']?.toDouble(),
      customProperties: json['custom_properties'] != null
          ? Map<String, dynamic>.from(json['custom_properties'] is String
              ? jsonDecode(json['custom_properties'])
              : json['custom_properties'])
          : null,
      projectId: json['project_id']?.toString(),
      zoneName: json['zone_name'] ?? 'Default',
      sourceTable: json['source_table'],
      sourceId: json['source_id']?.toString(),
      createdBy: json['created_by'],
      updatedBy: json['updated_by'],
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'])
          : null,
      colorValue: json['color_value'],
      iconName: json['icon_name'],
      strokeWidth: json['stroke_width']?.toDouble(),
    );
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // COPIE
  // ═══════════════════════════════════════════════════════════════════════════

  GeoPoint copyWith({
    String? id,
    String? name,
    String? lexiqueCode,
    String? type,
    String? subtype,
    GeometryType? geomType,
    List<LatLng>? coordinates,
    double? gpsPrecision,
    String? gpsSource,
    double? altitude,
    ConditionState? condition,
    PointStatus? status,
    SyncStatus? syncStatus,
    String? rejectionComment,
    String? comment,
    List<PhotoMetadata>? photos,
    String? materiau,
    double? hauteur,
    double? largeur,
    DateTime? dateInstallation,
    int? dureeVieAnnees,
    String? marqueModele,
    DateTime? dateDerniereIntervention,
    DateTime? dateProchaineIntervention,
    String? priorite,
    double? coutRemplacement,
    Map<String, dynamic>? customProperties,
    String? projectId,
    String? zoneName,
    String? sourceTable,
    String? sourceId,
    String? createdBy,
    String? updatedBy,
    DateTime? createdAt,
    DateTime? updatedAt,
    int? colorValue,
    String? iconName,
    double? strokeWidth,
  }) {
    return GeoPoint(
      id: id ?? this.id,
      name: name ?? this.name,
      lexiqueCode: lexiqueCode ?? this.lexiqueCode,
      type: type ?? this.type,
      subtype: subtype ?? this.subtype,
      geomType: geomType ?? this.geomType,
      coordinates: coordinates ?? this.coordinates,
      gpsPrecision: gpsPrecision ?? this.gpsPrecision,
      gpsSource: gpsSource ?? this.gpsSource,
      altitude: altitude ?? this.altitude,
      condition: condition ?? this.condition,
      status: status ?? this.status,
      syncStatus: syncStatus ?? this.syncStatus,
      rejectionComment: rejectionComment ?? this.rejectionComment,
      comment: comment ?? this.comment,
      photos: photos ?? this.photos,
      materiau: materiau ?? this.materiau,
      hauteur: hauteur ?? this.hauteur,
      largeur: largeur ?? this.largeur,
      dateInstallation: dateInstallation ?? this.dateInstallation,
      dureeVieAnnees: dureeVieAnnees ?? this.dureeVieAnnees,
      marqueModele: marqueModele ?? this.marqueModele,
      dateDerniereIntervention:
          dateDerniereIntervention ?? this.dateDerniereIntervention,
      dateProchaineIntervention:
          dateProchaineIntervention ?? this.dateProchaineIntervention,
      priorite: priorite ?? this.priorite,
      coutRemplacement: coutRemplacement ?? this.coutRemplacement,
      customProperties: customProperties ?? this.customProperties,
      projectId: projectId ?? this.projectId,
      zoneName: zoneName ?? this.zoneName,
      sourceTable: sourceTable ?? this.sourceTable,
      sourceId: sourceId ?? this.sourceId,
      createdBy: createdBy ?? this.createdBy,
      updatedBy: updatedBy ?? this.updatedBy,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      colorValue: colorValue ?? this.colorValue,
      iconName: iconName ?? this.iconName,
      strokeWidth: strokeWidth ?? this.strokeWidth,
    );
  }

  @override
  String toString() =>
      'GeoPoint($name, $type, sync: ${syncStatus.value}, photos: ${photos.length})';
}

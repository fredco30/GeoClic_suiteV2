import 'dart:convert';

/// Métadonnées d'une photo terrain avec EXIF préservé
///
/// Stocké en JSONB dans la colonne geoclic_photos de la table OGS.
class PhotoMetadata {
  /// URL de la photo (stockage définitif)
  final String url;

  /// URL de la miniature (300px)
  final String? thumbnailUrl;

  /// Nom de fichier original
  final String filename;

  /// Taille en octets
  final int? sizeBytes;

  /// Date/heure de prise de vue (EXIF)
  final DateTime? takenAt;

  /// Latitude GPS (EXIF)
  final double? gpsLatitude;

  /// Longitude GPS (EXIF)
  final double? gpsLongitude;

  /// Précision GPS en mètres
  final double? gpsAccuracy;

  /// Altitude GPS en mètres
  final double? gpsAltitude;

  /// Orientation EXIF (1-8)
  final int? orientation;

  /// Modèle d'appareil
  final String? deviceModel;

  /// Commentaire optionnel
  final String? comment;

  /// Chemin local (pour mode offline)
  final String? localPath;

  /// UUID unique de la photo
  final String id;

  PhotoMetadata({
    required this.url,
    this.thumbnailUrl,
    required this.filename,
    this.sizeBytes,
    this.takenAt,
    this.gpsLatitude,
    this.gpsLongitude,
    this.gpsAccuracy,
    this.gpsAltitude,
    this.orientation,
    this.deviceModel,
    this.comment,
    this.localPath,
    String? id,
  }) : id = id ?? _generateUuid();

  static String _generateUuid() {
    // Simple UUID v4 generation
    final now = DateTime.now().microsecondsSinceEpoch;
    return 'photo_${now}_${now.hashCode.toRadixString(16)}';
  }

  /// Indique si la photo a des coordonnées GPS
  bool get hasGps => gpsLatitude != null && gpsLongitude != null;

  /// Indique si la photo est synchronisée (URL disponible)
  bool get isSynced => url.isNotEmpty && !url.startsWith('file://');

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'url': url,
      'thumbnail_url': thumbnailUrl,
      'filename': filename,
      'size_bytes': sizeBytes,
      'taken_at': takenAt?.toIso8601String(),
      'gps_lat': gpsLatitude,
      'gps_lng': gpsLongitude,
      'gps_accuracy': gpsAccuracy,
      'gps_altitude': gpsAltitude,
      'orientation': orientation,
      'device_model': deviceModel,
      'comment': comment,
      'local_path': localPath,
    };
  }

  factory PhotoMetadata.fromJson(Map<String, dynamic> json) {
    return PhotoMetadata(
      id: json['id'],
      url: json['url'] ?? '',
      thumbnailUrl: json['thumbnail_url'],
      filename: json['filename'] ?? 'photo.jpg',
      sizeBytes: json['size_bytes'],
      takenAt: json['taken_at'] != null ? DateTime.tryParse(json['taken_at']) : null,
      gpsLatitude: json['gps_lat']?.toDouble(),
      gpsLongitude: json['gps_lng']?.toDouble(),
      gpsAccuracy: json['gps_accuracy']?.toDouble(),
      gpsAltitude: json['gps_altitude']?.toDouble(),
      orientation: json['orientation'],
      deviceModel: json['device_model'],
      comment: json['comment'],
      localPath: json['local_path'],
    );
  }

  /// Crée une PhotoMetadata depuis un chemin local (avant upload)
  factory PhotoMetadata.fromLocalFile({
    required String localPath,
    required String filename,
    double? latitude,
    double? longitude,
    double? accuracy,
    String? deviceModel,
  }) {
    return PhotoMetadata(
      url: 'file://$localPath',
      filename: filename,
      takenAt: DateTime.now(),
      gpsLatitude: latitude,
      gpsLongitude: longitude,
      gpsAccuracy: accuracy,
      deviceModel: deviceModel,
      localPath: localPath,
    );
  }

  PhotoMetadata copyWith({
    String? url,
    String? thumbnailUrl,
    String? filename,
    int? sizeBytes,
    DateTime? takenAt,
    double? gpsLatitude,
    double? gpsLongitude,
    double? gpsAccuracy,
    double? gpsAltitude,
    int? orientation,
    String? deviceModel,
    String? comment,
    String? localPath,
  }) {
    return PhotoMetadata(
      id: id,
      url: url ?? this.url,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      filename: filename ?? this.filename,
      sizeBytes: sizeBytes ?? this.sizeBytes,
      takenAt: takenAt ?? this.takenAt,
      gpsLatitude: gpsLatitude ?? this.gpsLatitude,
      gpsLongitude: gpsLongitude ?? this.gpsLongitude,
      gpsAccuracy: gpsAccuracy ?? this.gpsAccuracy,
      gpsAltitude: gpsAltitude ?? this.gpsAltitude,
      orientation: orientation ?? this.orientation,
      deviceModel: deviceModel ?? this.deviceModel,
      comment: comment ?? this.comment,
      localPath: localPath ?? this.localPath,
    );
  }

  @override
  String toString() => 'PhotoMetadata($filename, gps: $hasGps, synced: $isSynced)';
}

/// Extension pour convertir une liste de photos en JSON
extension PhotoListExtension on List<PhotoMetadata> {
  String toJsonString() => jsonEncode(map((p) => p.toJson()).toList());

  static List<PhotoMetadata> fromJsonString(String? json) {
    if (json == null || json.isEmpty) return [];
    try {
      final List<dynamic> list = jsonDecode(json);
      return list.map((e) => PhotoMetadata.fromJson(e)).toList();
    } catch (_) {
      return [];
    }
  }
}

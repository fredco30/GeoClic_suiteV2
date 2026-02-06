import 'dart:math';
import 'package:latlong2/latlong.dart';

/// Utilitaires géométriques pour GéoClic V12 Pro
class GeometryUtils {
  /// Rayon de la Terre en mètres (WGS84)
  static const double earthRadius = 6378137.0;

  /// Calcule la distance entre deux points (en mètres)
  static double distanceBetween(LatLng p1, LatLng p2) {
    const distance = Distance();
    return distance.as(LengthUnit.Meter, p1, p2);
  }

  /// Calcule la longueur totale d'une polyligne (en mètres)
  static double polylineLength(List<LatLng> points) {
    if (points.length < 2) return 0.0;

    double total = 0.0;
    for (int i = 0; i < points.length - 1; i++) {
      total += distanceBetween(points[i], points[i + 1]);
    }
    return total;
  }

  /// Calcule la surface d'un polygone (en m²)
  /// Utilise la formule de Shoelace adaptée aux coordonnées sphériques
  static double polygonArea(List<LatLng> points) {
    if (points.length < 3) return 0.0;

    double area = 0.0;
    List<LatLng> poly = List.from(points);

    // Fermer le polygone si nécessaire
    if (poly.first != poly.last) {
      poly.add(poly.first);
    }

    for (int i = 0; i < poly.length - 1; i++) {
      var p1 = poly[i];
      var p2 = poly[i + 1];
      area += (pi / 180) *
          (p2.longitude - p1.longitude) *
          (2 + sin(p1.latitude * pi / 180) + sin(p2.latitude * pi / 180));
    }

    area = area * earthRadius * earthRadius / 2.0;
    return area.abs();
  }

  /// Calcule le centre géométrique (centroïde)
  static LatLng centroid(List<LatLng> points) {
    if (points.isEmpty) return const LatLng(0, 0);
    if (points.length == 1) return points.first;

    double sumLat = 0, sumLng = 0;
    for (var point in points) {
      sumLat += point.latitude;
      sumLng += point.longitude;
    }
    return LatLng(sumLat / points.length, sumLng / points.length);
  }

  /// Calcule l'emprise (bounding box)
  static Map<String, double> boundingBox(List<LatLng> points) {
    if (points.isEmpty) {
      return {'minLat': 0, 'maxLat': 0, 'minLng': 0, 'maxLng': 0};
    }

    double minLat = points.first.latitude;
    double maxLat = points.first.latitude;
    double minLng = points.first.longitude;
    double maxLng = points.first.longitude;

    for (var point in points) {
      if (point.latitude < minLat) minLat = point.latitude;
      if (point.latitude > maxLat) maxLat = point.latitude;
      if (point.longitude < minLng) minLng = point.longitude;
      if (point.longitude > maxLng) maxLng = point.longitude;
    }

    return {
      'minLat': minLat,
      'maxLat': maxLat,
      'minLng': minLng,
      'maxLng': maxLng,
    };
  }

  /// Vérifie si un point est dans un polygone (algorithme ray casting)
  static bool pointInPolygon(LatLng point, List<LatLng> polygon) {
    if (polygon.length < 3) return false;

    bool inside = false;
    int j = polygon.length - 1;

    for (int i = 0; i < polygon.length; i++) {
      if ((polygon[i].latitude > point.latitude) !=
              (polygon[j].latitude > point.latitude) &&
          point.longitude <
              (polygon[j].longitude - polygon[i].longitude) *
                      (point.latitude - polygon[i].latitude) /
                      (polygon[j].latitude - polygon[i].latitude) +
                  polygon[i].longitude) {
        inside = !inside;
      }
      j = i;
    }

    return inside;
  }

  /// Convertit des degrés en radians
  static double toRadians(double degrees) => degrees * pi / 180;

  /// Convertit des radians en degrés
  static double toDegrees(double radians) => radians * 180 / pi;

  /// Formate une distance pour l'affichage
  static String formatDistance(double meters) {
    if (meters < 1000) {
      return '${meters.round()} m';
    } else {
      return '${(meters / 1000).toStringAsFixed(2)} km';
    }
  }

  /// Formate une surface pour l'affichage
  static String formatArea(double squareMeters) {
    if (squareMeters < 10000) {
      return '${squareMeters.round()} m²';
    } else {
      return '${(squareMeters / 10000).toStringAsFixed(2)} ha';
    }
  }

  /// Simplifie une polyligne (algorithme Douglas-Peucker)
  static List<LatLng> simplifyPolyline(List<LatLng> points, double tolerance) {
    if (points.length < 3) return points;

    double maxDistance = 0;
    int maxIndex = 0;

    final first = points.first;
    final last = points.last;

    for (int i = 1; i < points.length - 1; i++) {
      double distance = _perpendicularDistance(points[i], first, last);
      if (distance > maxDistance) {
        maxDistance = distance;
        maxIndex = i;
      }
    }

    if (maxDistance > tolerance) {
      final left = simplifyPolyline(points.sublist(0, maxIndex + 1), tolerance);
      final right = simplifyPolyline(points.sublist(maxIndex), tolerance);
      return [...left.sublist(0, left.length - 1), ...right];
    } else {
      return [first, last];
    }
  }

  /// Distance perpendiculaire d'un point à une ligne
  static double _perpendicularDistance(LatLng point, LatLng lineStart, LatLng lineEnd) {
    double x = point.longitude;
    double y = point.latitude;
    double x1 = lineStart.longitude;
    double y1 = lineStart.latitude;
    double x2 = lineEnd.longitude;
    double y2 = lineEnd.latitude;

    double A = x - x1;
    double B = y - y1;
    double C = x2 - x1;
    double D = y2 - y1;

    double dot = A * C + B * D;
    double lenSq = C * C + D * D;
    double param = lenSq != 0 ? dot / lenSq : -1;

    double xx, yy;
    if (param < 0) {
      xx = x1;
      yy = y1;
    } else if (param > 1) {
      xx = x2;
      yy = y2;
    } else {
      xx = x1 + param * C;
      yy = y1 + param * D;
    }

    return distanceBetween(point, LatLng(yy, xx));
  }
}

/// Extension pour convertir SRID
class SridUtils {
  /// EPSG:4326 - WGS84 (GPS mondial)
  static const int wgs84 = 4326;

  /// EPSG:2154 - Lambert 93 (France métropolitaine)
  static const int lambert93 = 2154;

  /// EPSG:3857 - Web Mercator (tuiles web)
  static const int webMercator = 3857;

  /// Indique si un SRID est supporté
  static bool isSupported(int srid) {
    return [wgs84, lambert93, webMercator].contains(srid);
  }
}

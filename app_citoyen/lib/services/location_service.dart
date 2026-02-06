import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';

class LocationService extends ChangeNotifier {
  Position? _currentPosition;
  String? _currentAddress;
  bool _loading = false;
  String? _error;

  Position? get currentPosition => _currentPosition;
  String? get currentAddress => _currentAddress;
  bool get loading => _loading;
  String? get error => _error;

  Future<bool> checkPermission() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      _error = 'Services de localisation désactivés';
      notifyListeners();
      return false;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        _error = 'Permission de localisation refusée';
        notifyListeners();
        return false;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      _error = 'Permission de localisation refusée définitivement';
      notifyListeners();
      return false;
    }

    return true;
  }

  Future<Position?> getCurrentPosition() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final hasPermission = await checkPermission();
      if (!hasPermission) {
        _loading = false;
        notifyListeners();
        return null;
      }

      _currentPosition = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 15),
      );

      _loading = false;
      notifyListeners();
      return _currentPosition;
    } catch (e) {
      _error = 'Impossible d\'obtenir la position';
      _loading = false;
      notifyListeners();
      return null;
    }
  }

  void setPosition(double latitude, double longitude) {
    _currentPosition = Position(
      latitude: latitude,
      longitude: longitude,
      timestamp: DateTime.now(),
      accuracy: 0,
      altitude: 0,
      heading: 0,
      speed: 0,
      speedAccuracy: 0,
      altitudeAccuracy: 0,
      headingAccuracy: 0,
    );
    notifyListeners();
  }

  void setAddress(String address) {
    _currentAddress = address;
    notifyListeners();
  }

  void clear() {
    _currentPosition = null;
    _currentAddress = null;
    _error = null;
    notifyListeners();
  }
}

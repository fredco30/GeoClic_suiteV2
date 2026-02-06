import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ConfigService extends ChangeNotifier {
  String? _projectId;
  String _projectName = 'Portail Citoyen';
  Color _primaryColor = const Color(0xFF2563EB);
  String? _logoUrl;
  bool _initialized = false;

  String? get projectId => _projectId;
  String get projectName => _projectName;
  Color get primaryColor => _primaryColor;
  String? get logoUrl => _logoUrl;
  bool get isConfigured => _projectId != null;

  Future<void> initialize() async {
    if (_initialized) return;

    final prefs = await SharedPreferences.getInstance();
    _projectId = prefs.getString('project_id');
    _projectName = prefs.getString('project_name') ?? 'Portail Citoyen';

    final colorHex = prefs.getString('primary_color');
    if (colorHex != null) {
      _primaryColor = Color(int.parse(colorHex.replaceFirst('#', '0xFF')));
    }

    _logoUrl = prefs.getString('logo_url');
    _initialized = true;
    notifyListeners();
  }

  Future<void> configure({
    required String projectId,
    required String projectName,
    Color? primaryColor,
    String? logoUrl,
  }) async {
    final prefs = await SharedPreferences.getInstance();

    _projectId = projectId;
    _projectName = projectName;
    if (primaryColor != null) _primaryColor = primaryColor;
    _logoUrl = logoUrl;

    await prefs.setString('project_id', projectId);
    await prefs.setString('project_name', projectName);
    if (primaryColor != null) {
      await prefs.setString(
        'primary_color',
        '#${primaryColor.value.toRadixString(16).substring(2)}',
      );
    }
    if (logoUrl != null) {
      await prefs.setString('logo_url', logoUrl);
    }

    notifyListeners();
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('project_id');
    await prefs.remove('project_name');
    await prefs.remove('primary_color');
    await prefs.remove('logo_url');

    _projectId = null;
    _projectName = 'Portail Citoyen';
    _primaryColor = const Color(0xFF2563EB);
    _logoUrl = null;

    notifyListeners();
  }
}

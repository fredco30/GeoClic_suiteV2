import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiService extends ChangeNotifier {
  String _baseUrl = 'https://api.geoclic.fr';
  String? _projectId;

  String get baseUrl => _baseUrl;
  String? get projectId => _projectId;

  void configure({required String baseUrl, required String projectId}) {
    _baseUrl = baseUrl;
    _projectId = projectId;
    notifyListeners();
  }

  Future<List<Category>> getCategories() async {
    if (_projectId == null) throw Exception('Project not configured');

    final response = await http.get(
      Uri.parse('$_baseUrl/api/demandes/categories?project_id=$_projectId'),
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((json) => Category.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load categories');
    }
  }

  Future<DemandeResponse> createDemande(DemandeCreate demande) async {
    if (_projectId == null) throw Exception('Project not configured');

    final response = await http.post(
      Uri.parse('$_baseUrl/api/demandes/public/demandes?project_id=$_projectId'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(demande.toJson()),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return DemandeResponse.fromJson(jsonDecode(response.body));
    } else if (response.statusCode == 429) {
      throw Exception('Limite quotidienne atteinte');
    } else {
      throw Exception('Erreur lors de la création');
    }
  }

  Future<DemandeDetail> getDemande(String numeroSuivi, String email) async {
    final response = await http.get(
      Uri.parse('$_baseUrl/api/demandes/public/demandes/$numeroSuivi?email=$email'),
    );

    if (response.statusCode == 200) {
      return DemandeDetail.fromJson(jsonDecode(response.body));
    } else if (response.statusCode == 404) {
      throw Exception('Demande non trouvée');
    } else {
      throw Exception('Erreur de chargement');
    }
  }

  Future<Equipement?> getEquipement(String equipementId) async {
    if (_projectId == null) return null;

    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/api/public/equipements/$equipementId?project_id=$_projectId'),
      );

      if (response.statusCode == 200) {
        return Equipement.fromJson(jsonDecode(response.body));
      }
    } catch (_) {}
    return null;
  }

  Future<String?> uploadPhoto(String filePath) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_baseUrl/api/photos/upload'),
      );
      request.files.add(await http.MultipartFile.fromPath('file', filePath));

      final response = await request.send();
      if (response.statusCode == 200) {
        final responseData = await response.stream.bytesToString();
        final json = jsonDecode(responseData);
        return json['url'] as String?;
      }
    } catch (_) {}
    return null;
  }
}

// Models
class Category {
  final String id;
  final String nom;
  final String? description;
  final String? icone;
  final String? couleur;
  final bool photoObligatoire;
  final int photoMaxCount;

  Category({
    required this.id,
    required this.nom,
    this.description,
    this.icone,
    this.couleur,
    this.photoObligatoire = false,
    this.photoMaxCount = 3,
  });

  factory Category.fromJson(Map<String, dynamic> json) {
    return Category(
      id: json['id'],
      nom: json['nom'],
      description: json['description'],
      icone: json['icone'],
      couleur: json['couleur'],
      photoObligatoire: json['photo_obligatoire'] ?? false,
      photoMaxCount: json['photo_max_count'] ?? 3,
    );
  }
}

class DemandeCreate {
  final String categorieId;
  final String description;
  final String declarantEmail;
  final String? declarantTelephone;
  final String? declarantNom;
  final double? latitude;
  final double? longitude;
  final String? adresse;
  final String? equipementId;
  final List<String>? photos;

  DemandeCreate({
    required this.categorieId,
    required this.description,
    required this.declarantEmail,
    this.declarantTelephone,
    this.declarantNom,
    this.latitude,
    this.longitude,
    this.adresse,
    this.equipementId,
    this.photos,
  });

  Map<String, dynamic> toJson() {
    return {
      'categorie_id': categorieId,
      'description': description,
      'declarant_email': declarantEmail,
      if (declarantTelephone != null) 'declarant_telephone': declarantTelephone,
      if (declarantNom != null) 'declarant_nom': declarantNom,
      if (latitude != null && longitude != null)
        'coordonnees': {'latitude': latitude, 'longitude': longitude},
      if (adresse != null) 'adresse_approximative': adresse,
      if (equipementId != null) 'equipement_id': equipementId,
      if (photos != null && photos!.isNotEmpty) 'photos': photos,
      'source': 'mobile',
      'declarant_langue': 'fr',
    };
  }
}

class DemandeResponse {
  final String numeroSuivi;
  final String statut;
  final String categorieNom;
  final String description;
  final String createdAt;
  final String message;

  DemandeResponse({
    required this.numeroSuivi,
    required this.statut,
    required this.categorieNom,
    required this.description,
    required this.createdAt,
    required this.message,
  });

  factory DemandeResponse.fromJson(Map<String, dynamic> json) {
    return DemandeResponse(
      numeroSuivi: json['numero_suivi'],
      statut: json['statut'],
      categorieNom: json['categorie_nom'],
      description: json['description'],
      createdAt: json['created_at'],
      message: json['message'] ?? 'Signalement créé',
    );
  }
}

class DemandeDetail {
  final String numeroSuivi;
  final String statut;
  final String categorieNom;
  final String description;
  final String? adresse;
  final String createdAt;
  final String? datePriseEnCharge;
  final String? datePlanification;
  final String? dateResolution;
  final List<HistoriqueEntry> historique;

  DemandeDetail({
    required this.numeroSuivi,
    required this.statut,
    required this.categorieNom,
    required this.description,
    this.adresse,
    required this.createdAt,
    this.datePriseEnCharge,
    this.datePlanification,
    this.dateResolution,
    this.historique = const [],
  });

  factory DemandeDetail.fromJson(Map<String, dynamic> json) {
    return DemandeDetail(
      numeroSuivi: json['numero_suivi'],
      statut: json['statut'],
      categorieNom: json['categorie_nom'],
      description: json['description'],
      adresse: json['adresse_approximative'],
      createdAt: json['created_at'],
      datePriseEnCharge: json['date_prise_en_charge'],
      datePlanification: json['date_planification'],
      dateResolution: json['date_resolution'],
      historique: (json['historique'] as List<dynamic>?)
              ?.map((e) => HistoriqueEntry.fromJson(e))
              .toList() ??
          [],
    );
  }
}

class HistoriqueEntry {
  final String id;
  final String action;
  final String? ancienStatut;
  final String? nouveauStatut;
  final String? commentaire;
  final String createdAt;

  HistoriqueEntry({
    required this.id,
    required this.action,
    this.ancienStatut,
    this.nouveauStatut,
    this.commentaire,
    required this.createdAt,
  });

  factory HistoriqueEntry.fromJson(Map<String, dynamic> json) {
    return HistoriqueEntry(
      id: json['id'],
      action: json['action'],
      ancienStatut: json['ancien_statut'],
      nouveauStatut: json['nouveau_statut'],
      commentaire: json['commentaire'],
      createdAt: json['created_at'],
    );
  }
}

class Equipement {
  final String id;
  final String nom;
  final String typeNom;
  final String? adresse;
  final double? latitude;
  final double? longitude;

  Equipement({
    required this.id,
    required this.nom,
    required this.typeNom,
    this.adresse,
    this.latitude,
    this.longitude,
  });

  factory Equipement.fromJson(Map<String, dynamic> json) {
    final coords = json['coordonnees'] as Map<String, dynamic>?;
    return Equipement(
      id: json['id'],
      nom: json['nom'],
      typeNom: json['type_nom'],
      adresse: json['adresse'],
      latitude: coords?['latitude']?.toDouble(),
      longitude: coords?['longitude']?.toDouble(),
    );
  }
}

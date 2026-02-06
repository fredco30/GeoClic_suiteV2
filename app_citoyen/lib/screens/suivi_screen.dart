import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class SuiviScreen extends StatefulWidget {
  const SuiviScreen({super.key});

  @override
  State<SuiviScreen> createState() => _SuiviScreenState();
}

class _SuiviScreenState extends State<SuiviScreen> {
  final _numeroController = TextEditingController();
  final _emailController = TextEditingController();

  DemandeDetail? _demande;
  bool _loading = false;
  String? _error;

  Future<void> _rechercher() async {
    if (_numeroController.text.isEmpty || _emailController.text.isEmpty) {
      setState(() => _error = 'Veuillez remplir tous les champs');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    final api = Provider.of<ApiService>(context, listen: false);

    try {
      final demande = await api.getDemande(
        _numeroController.text.trim(),
        _emailController.text.trim(),
      );
      setState(() {
        _demande = demande;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Demande non trouvée. Vérifiez le numéro et l\'email.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Suivre ma demande'),
      ),
      body: _demande != null ? _buildDetailView() : _buildSearchView(),
    );
  }

  Widget _buildSearchView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Theme.of(context).primaryColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              children: [
                Icon(Icons.search, size: 48, color: Theme.of(context).primaryColor),
                const SizedBox(height: 12),
                const Text(
                  'Rechercher une demande',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Entrez votre numéro de suivi et l\'email utilisé',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Formulaire
          TextField(
            controller: _numeroController,
            decoration: const InputDecoration(
              labelText: 'Numéro de suivi',
              hintText: 'Ex: SIG-2024-000001',
              prefixIcon: Icon(Icons.tag),
            ),
          ),
          const SizedBox(height: 16),

          TextField(
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(
              labelText: 'Email',
              hintText: 'votre@email.fr',
              prefixIcon: Icon(Icons.email),
            ),
          ),

          if (_error != null) ...[
            const SizedBox(height: 16),
            Card(
              color: Colors.red.shade50,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    const Icon(Icons.error, color: Colors.red),
                    const SizedBox(width: 8),
                    Expanded(child: Text(_error!, style: const TextStyle(color: Colors.red))),
                  ],
                ),
              ),
            ),
          ],

          const SizedBox(height: 24),

          ElevatedButton(
            onPressed: _loading ? null : _rechercher,
            child: _loading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Rechercher'),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailView() {
    final demande = _demande!;
    final statusInfo = _getStatusInfo(demande.statut);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header avec statut
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Demande n°', style: TextStyle(color: Colors.grey)),
                          Text(
                            demande.numeroSuivi,
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              fontFamily: 'monospace',
                            ),
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: statusInfo['color'] as Color,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          statusInfo['label'] as String,
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Détails
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Détails',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                  ),
                  const Divider(),
                  _buildDetailRow('Catégorie', demande.categorieNom),
                  _buildDetailRow('Description', demande.description),
                  if (demande.adresse != null) _buildDetailRow('Localisation', demande.adresse!),
                  _buildDetailRow('Créé le', _formatDate(demande.createdAt)),
                  if (demande.datePlanification != null)
                    _buildDetailRow('Intervention prévue', _formatDate(demande.datePlanification!)),
                  if (demande.dateResolution != null)
                    _buildDetailRow('Résolu le', _formatDate(demande.dateResolution!)),
                ],
              ),
            ),
          ),

          // Historique
          if (demande.historique.isNotEmpty) ...[
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Historique',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                    ),
                    const Divider(),
                    ...demande.historique.map((entry) => _buildHistoryItem(entry)),
                  ],
                ),
              ),
            ),
          ],

          const SizedBox(height: 24),
          OutlinedButton(
            onPressed: () {
              setState(() {
                _demande = null;
              });
            },
            child: const Text('Nouvelle recherche'),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label, style: const TextStyle(color: Colors.grey)),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  Widget _buildHistoryItem(HistoriqueEntry entry) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 12,
            height: 12,
            margin: const EdgeInsets.only(top: 4, right: 12),
            decoration: BoxDecoration(
              color: Theme.of(context).primaryColor,
              shape: BoxShape.circle,
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _formatDate(entry.createdAt),
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
                Text(
                  entry.action == 'creation'
                      ? 'Signalement créé'
                      : entry.action == 'changement_statut'
                          ? 'Statut: ${entry.nouveauStatut}'
                          : 'Mise à jour',
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
                if (entry.commentaire != null)
                  Text(entry.commentaire!, style: const TextStyle(fontSize: 13)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Map<String, dynamic> _getStatusInfo(String statut) {
    final statuts = {
      'nouveau': {'label': 'Nouveau', 'color': Colors.blue},
      'en_moderation': {'label': 'En modération', 'color': Colors.orange},
      'accepte': {'label': 'Accepté', 'color': Colors.green},
      'en_cours': {'label': 'En cours', 'color': Colors.purple},
      'planifie': {'label': 'Planifié', 'color': Colors.indigo},
      'traite': {'label': 'Traité', 'color': Colors.green.shade700},
      'rejete': {'label': 'Non retenu', 'color': Colors.red},
      'cloture': {'label': 'Clôturé', 'color': Colors.grey},
    };
    return statuts[statut] ?? {'label': statut, 'color': Colors.grey};
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year} à ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return dateStr;
    }
  }

  @override
  void dispose() {
    _numeroController.dispose();
    _emailController.dispose();
    super.dispose();
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';

class SignalerScreen extends StatefulWidget {
  const SignalerScreen({super.key});

  @override
  State<SignalerScreen> createState() => _SignalerScreenState();
}

class _SignalerScreenState extends State<SignalerScreen> {
  int _currentStep = 0;
  Category? _selectedCategory;
  final _descriptionController = TextEditingController();
  final _emailController = TextEditingController();
  final _nomController = TextEditingController();
  final _telephoneController = TextEditingController();
  final _adresseController = TextEditingController();

  List<Category> _categories = [];
  bool _loading = false;
  bool _submitted = false;
  String? _numeroSuivi;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  Future<void> _loadCategories() async {
    final api = Provider.of<ApiService>(context, listen: false);
    try {
      final categories = await api.getCategories();
      setState(() {
        _categories = categories;
      });
    } catch (e) {
      setState(() {
        _error = 'Erreur de chargement des catégories';
      });
    }
  }

  Future<void> _submit() async {
    if (_selectedCategory == null) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    final api = Provider.of<ApiService>(context, listen: false);
    final location = Provider.of<LocationService>(context, listen: false);

    try {
      final demande = DemandeCreate(
        categorieId: _selectedCategory!.id,
        description: _descriptionController.text,
        declarantEmail: _emailController.text,
        declarantNom: _nomController.text.isNotEmpty ? _nomController.text : null,
        declarantTelephone: _telephoneController.text.isNotEmpty ? _telephoneController.text : null,
        latitude: location.currentPosition?.latitude,
        longitude: location.currentPosition?.longitude,
        adresse: _adresseController.text.isNotEmpty ? _adresseController.text : null,
      );

      final response = await api.createDemande(demande);
      setState(() {
        _submitted = true;
        _numeroSuivi = response.numeroSuivi;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_submitted) {
      return _buildSuccessScreen();
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Signaler un problème'),
      ),
      body: Stepper(
        currentStep: _currentStep,
        onStepContinue: () {
          if (_currentStep < 3) {
            setState(() => _currentStep++);
          } else {
            _submit();
          }
        },
        onStepCancel: () {
          if (_currentStep > 0) {
            setState(() => _currentStep--);
          }
        },
        controlsBuilder: (context, details) {
          return Padding(
            padding: const EdgeInsets.only(top: 16),
            child: Row(
              children: [
                ElevatedButton(
                  onPressed: _loading ? null : details.onStepContinue,
                  child: Text(_currentStep == 3 ? 'Envoyer' : 'Suivant'),
                ),
                if (_currentStep > 0) ...[
                  const SizedBox(width: 12),
                  TextButton(
                    onPressed: details.onStepCancel,
                    child: const Text('Précédent'),
                  ),
                ],
              ],
            ),
          );
        },
        steps: [
          // Step 1: Catégorie
          Step(
            title: const Text('Catégorie'),
            subtitle: _selectedCategory != null ? Text(_selectedCategory!.nom) : null,
            isActive: _currentStep >= 0,
            state: _currentStep > 0 ? StepState.complete : StepState.indexed,
            content: _buildCategoryStep(),
          ),

          // Step 2: Description
          Step(
            title: const Text('Description'),
            isActive: _currentStep >= 1,
            state: _currentStep > 1 ? StepState.complete : StepState.indexed,
            content: _buildDescriptionStep(),
          ),

          // Step 3: Localisation
          Step(
            title: const Text('Localisation'),
            isActive: _currentStep >= 2,
            state: _currentStep > 2 ? StepState.complete : StepState.indexed,
            content: _buildLocationStep(),
          ),

          // Step 4: Contact
          Step(
            title: const Text('Contact'),
            isActive: _currentStep >= 3,
            content: _buildContactStep(),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryStep() {
    if (_categories.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    return Column(
      children: _categories.map((cat) {
        return Card(
          color: _selectedCategory?.id == cat.id
              ? Theme.of(context).primaryColor.withOpacity(0.1)
              : null,
          child: ListTile(
            leading: Text(cat.icone ?? '📌', style: const TextStyle(fontSize: 24)),
            title: Text(cat.nom),
            subtitle: cat.description != null ? Text(cat.description!) : null,
            selected: _selectedCategory?.id == cat.id,
            onTap: () => setState(() => _selectedCategory = cat),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildDescriptionStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _descriptionController,
          maxLines: 5,
          decoration: const InputDecoration(
            labelText: 'Description du problème',
            hintText: 'Décrivez le problème que vous avez constaté...',
            alignLabelWithHint: true,
          ),
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: () {
            // TODO: Implement photo picker
          },
          icon: const Icon(Icons.add_a_photo),
          label: const Text('Ajouter une photo'),
        ),
      ],
    );
  }

  Widget _buildLocationStep() {
    final location = Provider.of<LocationService>(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ElevatedButton.icon(
          onPressed: location.loading
              ? null
              : () async {
                  await location.getCurrentPosition();
                },
          icon: location.loading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.my_location),
          label: Text(location.loading ? 'Localisation...' : 'Utiliser ma position GPS'),
        ),
        if (location.currentPosition != null) ...[
          const SizedBox(height: 12),
          Card(
            color: Colors.green.shade50,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, color: Colors.green),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text('Position GPS enregistrée'),
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 16),
        TextField(
          controller: _adresseController,
          decoration: const InputDecoration(
            labelText: 'Adresse ou précisions (optionnel)',
            hintText: 'Ex: Devant le n°15, près du banc...',
          ),
        ),
      ],
    );
  }

  Widget _buildContactStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _emailController,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(
            labelText: 'Email *',
            hintText: 'votre@email.fr',
            prefixIcon: Icon(Icons.email),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _nomController,
          decoration: const InputDecoration(
            labelText: 'Nom (optionnel)',
            prefixIcon: Icon(Icons.person),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _telephoneController,
          keyboardType: TextInputType.phone,
          decoration: const InputDecoration(
            labelText: 'Téléphone (optionnel)',
            prefixIcon: Icon(Icons.phone),
          ),
        ),
        if (_error != null) ...[
          const SizedBox(height: 16),
          Card(
            color: Colors.red.shade50,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Text(_error!, style: const TextStyle(color: Colors.red)),
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildSuccessScreen() {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 80),
              const SizedBox(height: 24),
              const Text(
                'Signalement envoyé !',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              const Text(
                'Votre demande a bien été enregistrée.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.green),
                ),
                child: Column(
                  children: [
                    const Text('Numéro de suivi', style: TextStyle(color: Colors.grey)),
                    const SizedBox(height: 8),
                    Text(
                      _numeroSuivi ?? '',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        fontFamily: 'monospace',
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Text(
                'Un email de confirmation a été envoyé à ${_emailController.text}',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () => Navigator.popAndPushNamed(context, '/'),
                child: const Text('Retour à l\'accueil'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    _emailController.dispose();
    _nomController.dispose();
    _telephoneController.dispose();
    _adresseController.dispose();
    super.dispose();
  }
}

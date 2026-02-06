import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class ScanQRScreen extends StatefulWidget {
  const ScanQRScreen({super.key});

  @override
  State<ScanQRScreen> createState() => _ScanQRScreenState();
}

class _ScanQRScreenState extends State<ScanQRScreen> {
  MobileScannerController? _controller;
  bool _scanned = false;
  bool _loading = false;
  Equipement? _equipement;
  String? _error;

  @override
  void initState() {
    super.initState();
    _controller = MobileScannerController(
      detectionSpeed: DetectionSpeed.normal,
      facing: CameraFacing.back,
    );
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_scanned || _loading) return;

    final List<Barcode> barcodes = capture.barcodes;
    if (barcodes.isEmpty) return;

    final barcode = barcodes.first;
    if (barcode.rawValue == null) return;

    setState(() {
      _scanned = true;
      _loading = true;
    });

    _controller?.stop();

    // Parse QR code - format attendu: GEOCLIC:<equipement_id> ou URL
    String? equipementId = _parseQRCode(barcode.rawValue!);

    if (equipementId == null) {
      setState(() {
        _error = 'QR code non reconnu';
        _loading = false;
      });
      return;
    }

    // Charger les infos de l'équipement
    final api = Provider.of<ApiService>(context, listen: false);
    final equipement = await api.getEquipement(equipementId);

    setState(() {
      _equipement = equipement;
      _loading = false;
      if (equipement == null) {
        _error = 'Équipement non trouvé';
      }
    });
  }

  String? _parseQRCode(String rawValue) {
    // Format 1: GEOCLIC:<id>
    if (rawValue.startsWith('GEOCLIC:')) {
      return rawValue.substring(8);
    }

    // Format 2: URL avec paramètre id
    try {
      final uri = Uri.parse(rawValue);
      return uri.queryParameters['id'] ?? uri.pathSegments.lastOrNull;
    } catch (_) {}

    // Format 3: UUID direct
    final uuidRegex = RegExp(
      r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
      caseSensitive: false,
    );
    if (uuidRegex.hasMatch(rawValue)) {
      return rawValue;
    }

    return null;
  }

  void _reset() {
    setState(() {
      _scanned = false;
      _loading = false;
      _equipement = null;
      _error = null;
    });
    _controller?.start();
  }

  void _continuerSignalement() {
    if (_equipement == null) return;

    // TODO: Passer l'équipement à l'écran de signalement
    Navigator.pushReplacementNamed(
      context,
      '/signaler',
      arguments: {'equipement': _equipement},
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scanner un QR code'),
        actions: [
          if (_scanned)
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: _reset,
            ),
        ],
      ),
      body: _scanned ? _buildResultView() : _buildScannerView(),
    );
  }

  Widget _buildScannerView() {
    return Stack(
      children: [
        MobileScanner(
          controller: _controller,
          onDetect: _onDetect,
        ),
        // Overlay avec zone de scan
        Container(
          decoration: ShapeDecoration(
            shape: _ScannerOverlayShape(
              borderColor: Theme.of(context).primaryColor,
              borderWidth: 3,
              cutOutSize: 280,
            ),
          ),
        ),
        // Instructions
        Positioned(
          bottom: 100,
          left: 0,
          right: 0,
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 40),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.black54,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              'Positionnez le QR code dans le cadre',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildResultView() {
    if (_loading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Chargement de l\'équipement...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.orange),
              const SizedBox(height: 16),
              Text(
                _error!,
                style: const TextStyle(fontSize: 18),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _reset,
                icon: const Icon(Icons.qr_code_scanner),
                label: const Text('Scanner à nouveau'),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => Navigator.pushReplacementNamed(context, '/signaler'),
                child: const Text('Signalement libre'),
              ),
            ],
          ),
        ),
      );
    }

    if (_equipement != null) {
      return Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle, size: 64, color: Colors.green),
            const SizedBox(height: 16),
            const Text(
              'Équipement identifié',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(
                      _equipement!.nom,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _equipement!.typeNom,
                      style: TextStyle(color: Colors.grey.shade600),
                    ),
                    if (_equipement!.adresse != null) ...[
                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.location_on, size: 16, color: Colors.grey),
                          const SizedBox(width: 4),
                          Flexible(
                            child: Text(
                              _equipement!.adresse!,
                              style: const TextStyle(fontSize: 13),
                              textAlign: TextAlign.center,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'La localisation sera automatiquement renseignée.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _continuerSignalement,
              child: const Text('Signaler un problème'),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: _reset,
              child: const Text('Scanner un autre QR code'),
            ),
          ],
        ),
      );
    }

    return const SizedBox.shrink();
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }
}

// Custom overlay shape for scanner
class _ScannerOverlayShape extends ShapeBorder {
  final Color borderColor;
  final double borderWidth;
  final double cutOutSize;

  const _ScannerOverlayShape({
    this.borderColor = Colors.white,
    this.borderWidth = 3.0,
    this.cutOutSize = 280,
  });

  @override
  EdgeInsetsGeometry get dimensions => EdgeInsets.zero;

  @override
  Path getInnerPath(Rect rect, {TextDirection? textDirection}) => Path();

  @override
  Path getOuterPath(Rect rect, {TextDirection? textDirection}) {
    final cutOutRect = Rect.fromCenter(
      center: rect.center,
      width: cutOutSize,
      height: cutOutSize,
    );

    return Path()
      ..addRect(rect)
      ..addRRect(RRect.fromRectAndRadius(cutOutRect, const Radius.circular(12)))
      ..fillType = PathFillType.evenOdd;
  }

  @override
  void paint(Canvas canvas, Rect rect, {TextDirection? textDirection}) {
    final paint = Paint()
      ..color = Colors.black54
      ..style = PaintingStyle.fill;

    final cutOutRect = Rect.fromCenter(
      center: rect.center,
      width: cutOutSize,
      height: cutOutSize,
    );

    final path = Path()
      ..addRect(rect)
      ..addRRect(RRect.fromRectAndRadius(cutOutRect, const Radius.circular(12)))
      ..fillType = PathFillType.evenOdd;

    canvas.drawPath(path, paint);

    // Draw corner borders
    final borderPaint = Paint()
      ..color = borderColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = borderWidth;

    final cornerLength = 30.0;
    final rrect = RRect.fromRectAndRadius(cutOutRect, const Radius.circular(12));

    // Top-left corner
    canvas.drawLine(
      Offset(rrect.left, rrect.top + cornerLength),
      Offset(rrect.left, rrect.top + 12),
      borderPaint,
    );
    canvas.drawLine(
      Offset(rrect.left + 12, rrect.top),
      Offset(rrect.left + cornerLength, rrect.top),
      borderPaint,
    );

    // Top-right corner
    canvas.drawLine(
      Offset(rrect.right, rrect.top + cornerLength),
      Offset(rrect.right, rrect.top + 12),
      borderPaint,
    );
    canvas.drawLine(
      Offset(rrect.right - 12, rrect.top),
      Offset(rrect.right - cornerLength, rrect.top),
      borderPaint,
    );

    // Bottom-left corner
    canvas.drawLine(
      Offset(rrect.left, rrect.bottom - cornerLength),
      Offset(rrect.left, rrect.bottom - 12),
      borderPaint,
    );
    canvas.drawLine(
      Offset(rrect.left + 12, rrect.bottom),
      Offset(rrect.left + cornerLength, rrect.bottom),
      borderPaint,
    );

    // Bottom-right corner
    canvas.drawLine(
      Offset(rrect.right, rrect.bottom - cornerLength),
      Offset(rrect.right, rrect.bottom - 12),
      borderPaint,
    );
    canvas.drawLine(
      Offset(rrect.right - 12, rrect.bottom),
      Offset(rrect.right - cornerLength, rrect.bottom),
      borderPaint,
    );
  }

  @override
  ShapeBorder scale(double t) => this;
}

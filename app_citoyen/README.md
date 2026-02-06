# App Citoyen GéoClic

Application mobile Android native (Flutter) permettant aux citoyens de signaler des problèmes et de suivre leurs demandes.

## Fonctionnalités

- **Signalement libre** : Créer un signalement avec localisation GPS
- **Signalement via QR code** : Scanner un QR code sur un équipement public
- **Suivi des demandes** : Consulter l'avancement avec le numéro de suivi
- **Photos** : Prendre et joindre des photos au signalement
- **Mode hors-ligne** : Brouillons sauvegardés localement

## Stack technique

- **Flutter 3.x** avec Material 3
- **Provider** pour le state management
- **Hive** pour le stockage local
- **Geolocator** pour la géolocalisation
- **Mobile Scanner** pour le scan QR code
- **Flutter Map** pour la cartographie

## Installation

### Prérequis

1. **Flutter SDK** : https://flutter.dev/docs/get-started/install
2. **Android Studio** (pour le SDK Android)

### Vérification

```bash
flutter doctor
```

### Installation des dépendances

```bash
cd app_citoyen
flutter pub get
```

### Lancement en développement

```bash
flutter run
```

### Compilation de l'APK

```bash
# APK debug
flutter build apk --debug

# APK release
flutter build apk --release

# Bundle pour Play Store
flutter build appbundle --release
```

Les APK générés sont dans `build/app/outputs/flutter-apk/`

## Configuration

### Connexion à l'API

Dans `lib/services/api_service.dart`, configurer l'URL de base :

```dart
void configure({
  required String baseUrl,  // Ex: https://api.maville.fr
  required String projectId // UUID du projet
})
```

### Personnalisation

Le thème (couleurs, logo) est configurable via `ConfigService` :

```dart
await configService.configure(
  projectId: 'uuid-du-projet',
  projectName: 'Mairie de Ville',
  primaryColor: Color(0xFF2563EB),
  logoUrl: 'https://...',
);
```

## Structure

```
lib/
├── main.dart            # Point d'entrée
├── models/              # Modèles de données
├── screens/             # Écrans
│   ├── home_screen.dart
│   ├── signaler_screen.dart
│   ├── suivi_screen.dart
│   └── scan_qr_screen.dart
├── services/            # Services
│   ├── api_service.dart
│   ├── config_service.dart
│   └── location_service.dart
└── widgets/             # Composants réutilisables
```

## Permissions Android

L'application requiert dans `AndroidManifest.xml` :

```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
<uses-permission android:name="android.permission.CAMERA"/>
```

## Publication Play Store

1. Générer une clé de signature : `keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload`
2. Créer `android/key.properties`
3. Builder le bundle : `flutter build appbundle --release`
4. Uploader sur Google Play Console

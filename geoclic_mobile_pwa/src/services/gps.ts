import { ref, computed } from 'vue'

// Types
export interface GpsPosition {
  latitude: number
  longitude: number
  accuracy: number
  altitude: number | null
  altitudeAccuracy: number | null
  heading: number | null
  speed: number | null
  timestamp: number
}

export type GpsStatus = 'inactive' | 'searching' | 'active' | 'error'

export interface GpsError {
  code: number
  message: string
}

// État réactif global du GPS
const position = ref<GpsPosition | null>(null)
const status = ref<GpsStatus>('inactive')
const error = ref<GpsError | null>(null)
const watchId = ref<number | null>(null)
const isSupported = ref(false)
const permissionStatus = ref<PermissionState | null>(null)

// Vérifier le support de la géolocalisation
function checkSupport(): boolean {
  isSupported.value = 'geolocation' in navigator
  return isSupported.value
}

// Vérifier les permissions
async function checkPermission(): Promise<PermissionState | null> {
  if (!navigator.permissions) {
    return null
  }

  try {
    const result = await navigator.permissions.query({ name: 'geolocation' })
    permissionStatus.value = result.state

    // Écouter les changements de permission
    result.addEventListener('change', () => {
      permissionStatus.value = result.state
      if (result.state === 'denied') {
        stopWatching()
        status.value = 'error'
        error.value = { code: 1, message: 'Permission refusée' }
      }
    })

    return result.state
  } catch {
    return null
  }
}

// Obtenir la position actuelle (une seule fois)
async function getCurrentPosition(options?: PositionOptions): Promise<GpsPosition> {
  if (!checkSupport()) {
    throw new Error('Géolocalisation non supportée par ce navigateur')
  }

  status.value = 'searching'
  error.value = null

  const defaultOptions: PositionOptions = {
    enableHighAccuracy: true,
    timeout: 30000,
    maximumAge: 0,
    ...options
  }

  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const gpsPosition: GpsPosition = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          altitude: pos.coords.altitude,
          altitudeAccuracy: pos.coords.altitudeAccuracy,
          heading: pos.coords.heading,
          speed: pos.coords.speed,
          timestamp: pos.timestamp
        }

        position.value = gpsPosition
        status.value = 'active'
        error.value = null
        resolve(gpsPosition)
      },
      (err) => {
        const gpsError = mapGeolocationError(err)
        error.value = gpsError
        status.value = 'error'
        reject(gpsError)
      },
      defaultOptions
    )
  })
}

// Suivre la position en continu
function startWatching(
  onUpdate?: (position: GpsPosition) => void,
  options?: PositionOptions
): number | null {
  if (!checkSupport()) {
    error.value = { code: 0, message: 'Géolocalisation non supportée' }
    status.value = 'error'
    return null
  }

  // Arrêter le suivi précédent si actif
  if (watchId.value !== null) {
    stopWatching()
  }

  status.value = 'searching'
  error.value = null

  const defaultOptions: PositionOptions = {
    enableHighAccuracy: true,
    timeout: 30000,
    maximumAge: 5000,
    ...options
  }

  watchId.value = navigator.geolocation.watchPosition(
    (pos) => {
      const gpsPosition: GpsPosition = {
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
        accuracy: pos.coords.accuracy,
        altitude: pos.coords.altitude,
        altitudeAccuracy: pos.coords.altitudeAccuracy,
        heading: pos.coords.heading,
        speed: pos.coords.speed,
        timestamp: pos.timestamp
      }

      position.value = gpsPosition
      status.value = 'active'
      error.value = null

      if (onUpdate) {
        onUpdate(gpsPosition)
      }
    },
    (err) => {
      const gpsError = mapGeolocationError(err)
      error.value = gpsError
      status.value = 'error'
    },
    defaultOptions
  )

  return watchId.value
}

// Arrêter le suivi
function stopWatching(): void {
  if (watchId.value !== null) {
    navigator.geolocation.clearWatch(watchId.value)
    watchId.value = null
  }
  status.value = 'inactive'
}

// Mapper les erreurs de géolocalisation
function mapGeolocationError(err: GeolocationPositionError): GpsError {
  switch (err.code) {
    case err.PERMISSION_DENIED:
      return {
        code: 1,
        message: 'Accès à la localisation refusé. Veuillez autoriser l\'accès dans les paramètres.'
      }
    case err.POSITION_UNAVAILABLE:
      return {
        code: 2,
        message: 'Position indisponible. Vérifiez que le GPS est activé.'
      }
    case err.TIMEOUT:
      return {
        code: 3,
        message: 'Délai d\'attente dépassé. Réessayez dans un endroit avec meilleure réception.'
      }
    default:
      return {
        code: 0,
        message: 'Erreur de géolocalisation inconnue'
      }
  }
}

// Formater l'accuracy pour l'affichage
function formatAccuracy(accuracy: number): string {
  if (accuracy < 10) {
    return `${Math.round(accuracy)}m (excellent)`
  } else if (accuracy < 30) {
    return `${Math.round(accuracy)}m (bon)`
  } else if (accuracy < 100) {
    return `${Math.round(accuracy)}m (moyen)`
  } else {
    return `${Math.round(accuracy)}m (faible)`
  }
}

// Formater les coordonnées en DMS (Degrés Minutes Secondes)
function formatCoordinateDMS(decimal: number, isLat: boolean): string {
  const direction = isLat
    ? (decimal >= 0 ? 'N' : 'S')
    : (decimal >= 0 ? 'E' : 'W')

  const absolute = Math.abs(decimal)
  const degrees = Math.floor(absolute)
  const minutesFloat = (absolute - degrees) * 60
  const minutes = Math.floor(minutesFloat)
  const seconds = ((minutesFloat - minutes) * 60).toFixed(2)

  return `${degrees}° ${minutes}' ${seconds}" ${direction}`
}

// Calculer la distance entre deux points (Haversine)
function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371e3 // Rayon de la Terre en mètres
  const φ1 = (lat1 * Math.PI) / 180
  const φ2 = (lat2 * Math.PI) / 180
  const Δφ = ((lat2 - lat1) * Math.PI) / 180
  const Δλ = ((lon2 - lon1) * Math.PI) / 180

  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2)

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))

  return R * c // Distance en mètres
}

// Computed
const isWatching = computed(() => watchId.value !== null)
const hasPosition = computed(() => position.value !== null)
const accuracyText = computed(() =>
  position.value ? formatAccuracy(position.value.accuracy) : ''
)

// Export du service GPS
export const gpsService = {
  // État réactif
  position,
  status,
  error,
  isSupported,
  permissionStatus,
  isWatching,
  hasPosition,
  accuracyText,

  // Méthodes
  checkSupport,
  checkPermission,
  getCurrentPosition,
  startWatching,
  stopWatching,
  formatAccuracy,
  formatCoordinateDMS,
  calculateDistance
}

export default gpsService

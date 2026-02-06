<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { gpsService, type GpsPosition } from '@/services/gps'
import type { GeometryType, Coordinate } from '@/services/api'

interface Props {
  geometryType: GeometryType
  modelValue: Coordinate[]
  currentPosition?: { latitude: number; longitude: number } | null
  currentAccuracy?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  currentPosition: null,
  currentAccuracy: null
})

const emit = defineEmits<{
  'update:modelValue': [value: Coordinate[]]
}>()

const mapContainer = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let markersLayer: L.LayerGroup | null = null
let polyline: L.Polyline | null = null
let polygon: L.Polygon | null = null
let userMarker: L.Marker | null = null
let accuracyCircle: L.Circle | null = null

const isRecording = ref(false)
let watchId: number | null = null
let lastRecordedPosition: Coordinate | null = null
const minDistanceMeters = 5 // Distance minimale entre deux points GPS

// Calcul distance entre deux coordonnées en mètres
const calculateDistance = (c1: Coordinate, c2: Coordinate): number => {
  const R = 6371000 // Rayon de la Terre en mètres
  const lat1 = c1.latitude * Math.PI / 180
  const lat2 = c2.latitude * Math.PI / 180
  const deltaLat = (c2.latitude - c1.latitude) * Math.PI / 180
  const deltaLng = (c2.longitude - c1.longitude) * Math.PI / 180

  const a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
            Math.cos(lat1) * Math.cos(lat2) *
            Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))

  return R * c
}

// Calculer la longueur totale
const totalLength = computed(() => {
  if (props.modelValue.length < 2) return 0
  let total = 0
  for (let i = 0; i < props.modelValue.length - 1; i++) {
    total += calculateDistance(props.modelValue[i], props.modelValue[i + 1])
  }
  return total
})

// Calculer l'aire (approximation pour petites surfaces)
const totalArea = computed(() => {
  if (props.modelValue.length < 3) return 0

  // Algorithme du lacet de chaussure
  let area = 0
  const n = props.modelValue.length

  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n
    area += props.modelValue[i].longitude * props.modelValue[j].latitude
    area -= props.modelValue[j].longitude * props.modelValue[i].latitude
  }

  // Conversion approximative en m²
  const avgLat = props.modelValue.reduce((sum, c) => sum + c.latitude, 0) / n
  const metersPerDegreeLat = 111320
  const metersPerDegreeLon = 111320 * Math.cos(avgLat * Math.PI / 180)

  return Math.abs(area / 2) * metersPerDegreeLat * metersPerDegreeLon
})

// Formatage distance
const formatDistance = (meters: number): string => {
  if (meters < 1000) return `${meters.toFixed(1)} m`
  return `${(meters / 1000).toFixed(2)} km`
}

// Formatage surface
const formatArea = (squareMeters: number): string => {
  if (squareMeters < 10000) return `${squareMeters.toFixed(1)} m²`
  return `${(squareMeters / 10000).toFixed(2)} ha`
}

// Initialiser la carte
const initMap = () => {
  if (!mapContainer.value || map) return

  // Position par défaut (France ou position actuelle)
  const center = props.currentPosition
    ? [props.currentPosition.latitude, props.currentPosition.longitude] as L.LatLngExpression
    : [46.603354, 1.888334] as L.LatLngExpression
  const zoom = props.currentPosition ? 18 : 6

  map = L.map(mapContainer.value, {
    center,
    zoom,
    zoomControl: false
  })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap',
    maxZoom: 19
  }).addTo(map)

  // Contrôles zoom
  L.control.zoom({ position: 'topright' }).addTo(map)

  // Couche des marqueurs
  markersLayer = L.layerGroup().addTo(map)

  // Clic sur la carte pour ajouter un point
  map.on('click', (e: L.LeafletMouseEvent) => {
    addPoint({
      latitude: e.latlng.lat,
      longitude: e.latlng.lng
    })
  })

  // Dessiner la géométrie existante
  updateGeometry()
  updateUserMarker()

  // Si des coordonnées existent déjà (mode édition), centrer sur elles
  if (props.modelValue.length > 0) {
    setTimeout(() => fitBounds(), 100)
  }
}

// Mettre à jour la géométrie sur la carte
const updateGeometry = () => {
  if (!map || !markersLayer) return

  // Effacer les couches existantes
  markersLayer.clearLayers()
  if (polyline) {
    map.removeLayer(polyline)
    polyline = null
  }
  if (polygon) {
    map.removeLayer(polygon)
    polygon = null
  }

  const coords = props.modelValue

  // Dessiner les marqueurs
  coords.forEach((coord, index) => {
    const isFirst = index === 0
    const isLast = index === coords.length - 1

    let color = '#FF9800' // Orange par défaut
    if (isFirst) color = '#4CAF50' // Vert pour le premier
    else if (isLast) color = '#F44336' // Rouge pour le dernier

    const marker = L.marker([coord.latitude, coord.longitude], {
      icon: L.divIcon({
        className: 'geom-marker',
        html: `<div class="marker-point" style="background: ${color}">${index + 1}</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      })
    })

    // Supprimer au clic long
    marker.on('contextmenu', () => {
      removePoint(index)
    })

    marker.addTo(markersLayer!)
  })

  // Dessiner la ligne
  if (coords.length >= 2) {
    const latLngs = coords.map(c => [c.latitude, c.longitude] as L.LatLngExpression)

    polyline = L.polyline(latLngs, {
      color: '#2196F3',
      weight: 4,
      opacity: 0.8
    }).addTo(map)

    // Fermer le polygone si besoin
    if (props.geometryType === 'POLYGON' && coords.length >= 3) {
      polygon = L.polygon(latLngs, {
        color: '#2196F3',
        weight: 2,
        fillColor: '#2196F3',
        fillOpacity: 0.2
      }).addTo(map)
    }
  }
}

// Mettre à jour le marqueur utilisateur
const updateUserMarker = () => {
  if (!map || !props.currentPosition) return

  const pos: L.LatLngExpression = [props.currentPosition.latitude, props.currentPosition.longitude]

  if (userMarker) {
    userMarker.setLatLng(pos)
  } else {
    userMarker = L.marker(pos, {
      icon: L.divIcon({
        className: 'user-marker',
        html: '<div class="user-dot"></div>',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      })
    }).addTo(map)
  }

  // Cercle de précision
  if (accuracyCircle) {
    accuracyCircle.setLatLng(pos)
    if (props.currentAccuracy) {
      accuracyCircle.setRadius(props.currentAccuracy)
    }
  } else if (props.currentAccuracy) {
    accuracyCircle = L.circle(pos, {
      radius: props.currentAccuracy,
      color: '#1976D2',
      fillColor: '#1976D2',
      fillOpacity: 0.1,
      weight: 1
    }).addTo(map)
  }
}

// Ajouter un point
const addPoint = (coord: Coordinate) => {
  let newCoords: Coordinate[]

  if (props.geometryType === 'POINT') {
    // Pour un point, remplacer
    newCoords = [coord]
  } else {
    newCoords = [...props.modelValue, coord]
  }

  emit('update:modelValue', newCoords)
}

// Supprimer un point
const removePoint = (index: number) => {
  const newCoords = [...props.modelValue]
  newCoords.splice(index, 1)
  emit('update:modelValue', newCoords)
}

// Supprimer le dernier point
const removeLastPoint = () => {
  if (props.modelValue.length > 0) {
    removePoint(props.modelValue.length - 1)
  }
}

// Effacer tous les points
const clearPoints = () => {
  emit('update:modelValue', [])
}

// Ajouter la position GPS actuelle
const addCurrentPosition = async () => {
  try {
    const position = await gpsService.getCurrentPosition({
      enableHighAccuracy: true,
      timeout: 30000,
      maximumAge: 0
    })

    addPoint({
      latitude: position.latitude,
      longitude: position.longitude
    })

    // Centrer sur la position
    if (map) {
      map.setView([position.latitude, position.longitude], 18)
    }
  } catch (err) {
    console.error('Erreur GPS:', err)
    alert('Impossible d\'obtenir la position GPS')
  }
}

// Démarrer l'enregistrement GPS continu
const startRecording = async () => {
  if (isRecording.value) return

  try {
    isRecording.value = true
    lastRecordedPosition = null

    watchId = gpsService.startWatching((position: GpsPosition) => {
      const newCoord: Coordinate = {
        latitude: position.latitude,
        longitude: position.longitude
      }

      // Vérifier la distance minimale
      if (!lastRecordedPosition ||
          calculateDistance(lastRecordedPosition, newCoord) >= minDistanceMeters) {
        addPoint(newCoord)
        lastRecordedPosition = newCoord

        // Centrer sur la nouvelle position
        if (map) {
          map.setView([newCoord.latitude, newCoord.longitude], map.getZoom())
        }
      }
    })
  } catch (err) {
    console.error('Erreur démarrage GPS:', err)
    isRecording.value = false
  }
}

// Arrêter l'enregistrement
const stopRecording = () => {
  gpsService.stopWatching()
  watchId = null
  isRecording.value = false
}

// Centrer sur la vue actuelle
const centerOnUser = () => {
  if (map && props.currentPosition) {
    map.setView([props.currentPosition.latitude, props.currentPosition.longitude], 18)
  }
}

// Ajuster la vue pour voir tous les points
const fitBounds = () => {
  if (!map || props.modelValue.length === 0) return

  const bounds = L.latLngBounds(
    props.modelValue.map(c => [c.latitude, c.longitude] as L.LatLngExpression)
  )

  if (bounds.isValid()) {
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 18 })
  }
}

// Flag pour savoir si on a déjà centré la carte sur les coordonnées existantes
let hasInitiallyFitBounds = false

// Watchers
watch(() => props.modelValue, (newValue, oldValue) => {
  updateGeometry()

  // Centrer la carte quand les coordonnées sont chargées pour la première fois (mode édition)
  if (!hasInitiallyFitBounds && newValue.length > 0 && (!oldValue || oldValue.length === 0)) {
    hasInitiallyFitBounds = true
    setTimeout(() => fitBounds(), 100)
  }
}, { deep: true })

watch(() => props.currentPosition, () => {
  updateUserMarker()
}, { deep: true })

onMounted(() => {
  initMap()
})

onUnmounted(() => {
  stopRecording()
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="geometry-drawing">
    <!-- Carte -->
    <div ref="mapContainer" class="map-container"></div>

    <!-- Indicateur d'enregistrement -->
    <div v-if="isRecording" class="recording-indicator">
      <span class="recording-dot"></span>
      <span>Enregistrement GPS... ({{ modelValue.length }} points)</span>
      <button class="stop-btn" @click="stopRecording">Stop</button>
    </div>

    <!-- Statistiques -->
    <div v-if="modelValue.length > 0" class="stats-overlay">
      <div class="stat">{{ modelValue.length }} point(s)</div>
      <div v-if="geometryType !== 'POINT' && modelValue.length >= 2" class="stat">
        {{ formatDistance(totalLength) }}
      </div>
      <div v-if="geometryType === 'POLYGON' && modelValue.length >= 3" class="stat">
        {{ formatArea(totalArea) }}
      </div>
    </div>

    <!-- Bouton localisation -->
    <button class="locate-btn" @click="centerOnUser" title="Ma position">
      📍
    </button>

    <!-- Bouton ajuster vue -->
    <button
      v-if="modelValue.length > 0"
      class="fit-btn"
      @click="fitBounds"
      title="Voir tout"
    >
      🔍
    </button>

    <!-- Barre d'outils -->
    <div class="toolbar">
      <button class="tool-btn" @click="addCurrentPosition">
        <span class="tool-icon">📡</span>
        <span class="tool-label">GPS</span>
      </button>

      <button
        v-if="geometryType !== 'POINT'"
        :class="['tool-btn', { recording: isRecording }]"
        @click="isRecording ? stopRecording() : startRecording()"
      >
        <span class="tool-icon">{{ isRecording ? '⏹️' : '⏺️' }}</span>
        <span class="tool-label">{{ isRecording ? 'Stop' : 'Tracer' }}</span>
      </button>

      <button
        class="tool-btn"
        :disabled="modelValue.length === 0"
        @click="removeLastPoint"
      >
        <span class="tool-icon">↩️</span>
        <span class="tool-label">Annuler</span>
      </button>

      <button
        class="tool-btn"
        :disabled="modelValue.length === 0"
        @click="clearPoints"
      >
        <span class="tool-icon">🗑️</span>
        <span class="tool-label">Effacer</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.geometry-drawing {
  position: relative;
  height: 100%;
  min-height: 300px;
  display: flex;
  flex-direction: column;
}

.map-container {
  flex: 1;
  z-index: 1;
}

.recording-indicator {
  position: absolute;
  top: 16px;
  left: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #d32f2f;
  color: white;
  border-radius: var(--radius);
  font-size: 14px;
  z-index: 500;
  box-shadow: var(--shadow-lg);
}

.recording-dot {
  width: 10px;
  height: 10px;
  background: white;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.stop-btn {
  margin-left: auto;
  padding: 6px 12px;
  background: white;
  color: #d32f2f;
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  cursor: pointer;
}

.stats-overlay {
  position: absolute;
  bottom: 80px;
  left: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border-radius: var(--radius-sm);
  font-size: 12px;
  z-index: 500;
}

.locate-btn,
.fit-btn {
  position: absolute;
  width: 44px;
  height: 44px;
  background: var(--surface-color);
  border: none;
  border-radius: 50%;
  box-shadow: var(--shadow);
  font-size: 20px;
  cursor: pointer;
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.locate-btn {
  bottom: 140px;
  right: 16px;
}

.fit-btn {
  bottom: 190px;
  right: 16px;
}

.toolbar {
  display: flex;
  justify-content: space-around;
  padding: 12px 16px;
  background: var(--surface-color);
  border-top: 1px solid var(--border-color);
  z-index: 500;
}

.tool-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: var(--radius);
  transition: background 0.2s;
}

.tool-btn:hover:not(:disabled) {
  background: var(--background-color);
}

.tool-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.tool-btn.recording {
  color: #d32f2f;
}

.tool-icon {
  font-size: 22px;
}

.tool-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.tool-btn.recording .tool-label {
  color: #d32f2f;
}
</style>

<style>
/* Styles globaux pour les marqueurs Leaflet */
.geom-marker {
  background: none;
  border: none;
}

.marker-point {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.user-marker {
  background: none;
  border: none;
}

.user-dot {
  width: 16px;
  height: 16px;
  background: #1976D2;
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
</style>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, onUnmounted } from 'vue'
import { api } from '@/services/api'
import axios from 'axios'

interface Props {
  initialCoords?: { latitude: number; longitude: number } | null
  projectId?: string
  fullscreen?: boolean
}

interface Emits {
  (e: 'select', location: { lat: number; lng: number; address?: string }): void
  (e: 'close'): void
}

const props = withDefaults(defineProps<Props>(), {
  fullscreen: true
})
const emit = defineEmits<Emits>()

const mapContainer = ref<HTMLDivElement | null>(null)
const map = ref<L.Map | null>(null)
const marker = ref<L.Marker | null>(null)
const zonesLayer = ref<L.GeoJSON | null>(null)
const selectedCoords = ref<{ lat: number; lng: number } | null>(null)
const selectedAddress = ref<string>('')
const loading = ref(false)
const gpsLoading = ref(false)
const isReady = ref(false)

// Default center: France
const defaultCenter = { lat: 46.603354, lng: 1.888334 }
const defaultZoom = 6

// Couleurs des zones
const zoneColors: Record<string, string> = {
  quartier: '#3b82f6',
  secteur: '#8b5cf6',
  commune: '#22c55e'
}

onMounted(async () => {
  if (!mapContainer.value) return

  // Import Leaflet dynamically
  const L = await import('leaflet')

  // Initialize map
  map.value = L.map(mapContainer.value).setView(
    props.initialCoords
      ? [props.initialCoords.latitude, props.initialCoords.longitude]
      : [defaultCenter.lat, defaultCenter.lng],
    props.initialCoords ? 18 : defaultZoom
  )

  // Add tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map.value)

  // Force le recalcul de la taille de la carte après le rendu
  await nextTick()
  map.value?.invalidateSize()
  setTimeout(() => map.value?.invalidateSize(), 100)
  setTimeout(() => map.value?.invalidateSize(), 300)

  // Add initial marker if coords provided
  if (props.initialCoords) {
    await addMarker(props.initialCoords.latitude, props.initialCoords.longitude, true)
    selectedCoords.value = { lat: props.initialCoords.latitude, lng: props.initialCoords.longitude }
  } else {
    // Géolocalisation automatique si pas de coords initiales
    await autoGeolocate()
  }

  // Charger les zones après la géolocalisation
  await loadZones()

  // Click handler
  map.value.on('click', async (e: L.LeafletMouseEvent) => {
    const { lat, lng } = e.latlng
    await selectLocation(lat, lng)
  })

  isReady.value = true
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
    map.value = null
  }
})

// Géolocalisation automatique au chargement
async function autoGeolocate() {
  if (!navigator.geolocation) return

  gpsLoading.value = true

  try {
    const position = await new Promise<GeolocationPosition>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 8000,
      })
    })

    const { latitude, longitude } = position.coords

    // Zoomer au maximum sur la position GPS (zoom 18)
    map.value?.setView([latitude, longitude], 18)

    // Forcer le recalcul
    setTimeout(() => map.value?.invalidateSize(), 200)

    // Placer le marqueur et récupérer l'adresse
    await addMarker(latitude, longitude, true)
    selectedCoords.value = { lat: latitude, lng: longitude }

    // Reverse geocode
    const address = await api.reverseGeocode(latitude, longitude)
    selectedAddress.value = address || ''

  } catch (error) {
    // Silencieux - on ne bloque pas si GPS échoue
    console.log('Géolocalisation auto échouée, l\'utilisateur peut cliquer sur la carte')
  } finally {
    gpsLoading.value = false
  }
}

async function loadZones() {
  if (!map.value) return

  try {
    const L = await import('leaflet')
    const params = props.projectId ? `?project_id=${props.projectId}` : ''
    const response = await axios.get(`/api/zones/geojson${params}`)
    const geojson = response.data

    if (!geojson || !geojson.features?.length) return

    // Créer la couche GeoJSON
    zonesLayer.value = L.geoJSON(geojson, {
      style: (feature) => {
        const zoneType = feature?.properties?.zone_type || 'quartier'
        const color = zoneColors[zoneType] || '#6b7280'
        return {
          color: color,
          weight: 2,
          opacity: 0.6,
          fillColor: color,
          fillOpacity: 0.1
        }
      },
      onEachFeature: (feature, layer) => {
        if (feature.properties?.name) {
          layer.bindTooltip(feature.properties.name, {
            permanent: false,
            direction: 'center'
          })
        }
      }
    }).addTo(map.value)

  } catch (error) {
    console.error('Erreur chargement zones:', error)
  }
}

async function selectLocation(lat: number, lng: number) {
  loading.value = true

  try {
    await addMarker(lat, lng, false)
    selectedCoords.value = { lat, lng }

    // Reverse geocode
    const address = await api.reverseGeocode(lat, lng)
    selectedAddress.value = address || ''
  } finally {
    loading.value = false
  }
}

async function addMarker(lat: number, lng: number, centerMap: boolean = true) {
  if (!map.value) return

  const L = await import('leaflet')

  // Remove existing marker
  if (marker.value) {
    marker.value.remove()
  }

  // Add new marker
  marker.value = L.marker([lat, lng], {
    draggable: true,
  }).addTo(map.value)

  // Drag handler
  marker.value.on('dragend', async () => {
    const pos = marker.value?.getLatLng()
    if (pos) {
      selectedCoords.value = { lat: pos.lat, lng: pos.lng }
      loading.value = true
      try {
        const address = await api.reverseGeocode(pos.lat, pos.lng)
        selectedAddress.value = address || ''
      } finally {
        loading.value = false
      }
    }
  })

  // Center map on marker
  if (centerMap) {
    map.value.setView([lat, lng], Math.max(map.value.getZoom(), 16))
  }
}

async function useGPS() {
  if (!navigator.geolocation) {
    alert('La géolocalisation n\'est pas supportée par votre navigateur')
    return
  }

  gpsLoading.value = true

  try {
    const position = await new Promise<GeolocationPosition>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
      })
    })

    const { latitude, longitude } = position.coords

    // Forcer le recalcul de la carte avant de zoomer
    map.value?.invalidateSize()

    // Zoomer au maximum sur la position GPS (zoom 18)
    map.value?.setView([latitude, longitude], 18)

    // Attendre un peu puis forcer encore le recalcul pour charger les tuiles
    setTimeout(() => {
      map.value?.invalidateSize()
    }, 200)

    await selectLocation(latitude, longitude)
  } catch (error) {
    alert('Impossible d\'obtenir votre position GPS')
  } finally {
    gpsLoading.value = false
  }
}

function validatePosition() {
  if (selectedCoords.value) {
    emit('select', {
      lat: selectedCoords.value.lat,
      lng: selectedCoords.value.lng,
      address: selectedAddress.value
    })
  }
}

function closeMap() {
  emit('close')
}

watch(
  () => props.initialCoords,
  (newCoords) => {
    if (newCoords && map.value) {
      addMarker(newCoords.latitude, newCoords.longitude)
      selectedCoords.value = { lat: newCoords.latitude, lng: newCoords.longitude }
    }
  }
)
</script>

<template>
  <div :class="['map-picker', { fullscreen: fullscreen }]">
    <!-- Fullscreen header -->
    <div v-if="fullscreen" class="map-header">
      <button @click="closeMap" class="back-btn" aria-label="Retour">
        <span class="back-icon">&larr;</span>
      </button>
      <div class="address-display">
        <div v-if="loading" class="address-loading">Recherche de l'adresse...</div>
        <div v-else-if="selectedAddress" class="address-text">{{ selectedAddress }}</div>
        <div v-else class="address-placeholder">Cliquez sur la carte pour localiser</div>
      </div>
    </div>

    <!-- Map container -->
    <div ref="mapContainer" class="map-container"></div>

    <!-- GPS button (floating) -->
    <button @click="useGPS" :disabled="gpsLoading" class="gps-btn-floating" aria-label="Ma position">
      <span v-if="gpsLoading" class="gps-icon spinning">&#8987;</span>
      <span v-else class="gps-icon">&#128205;</span>
    </button>

    <!-- Fullscreen footer with validate button -->
    <div v-if="fullscreen" class="map-footer">
      <div class="position-hint" v-if="selectedCoords">
        <span class="check-icon">&#9989;</span>
        Déplacez le marqueur pour ajuster la position
      </div>
      <button
        @click="validatePosition"
        :disabled="!selectedCoords"
        class="validate-btn"
      >
        <span class="validate-icon">&#10003;</span>
        Valider cette position
      </button>
    </div>

    <!-- Non-fullscreen hint -->
    <p v-if="!fullscreen" class="map-hint">
      <span v-if="selectedCoords">
        &#9989; Position sélectionnée. Vous pouvez déplacer le marqueur si nécessaire.
      </span>
      <span v-else>
        Cliquez sur la carte pour indiquer l'emplacement du problème.
      </span>
    </p>
  </div>
</template>

<style scoped>
.map-picker {
  position: relative;
}

.map-picker.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  background: #1f2937;
}

/* Header */
.map-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 10;
}

.back-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: white;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.address-display {
  flex: 1;
  min-width: 0;
}

.address-text {
  color: white;
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.address-loading {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  font-style: italic;
}

.address-placeholder {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
}

/* Map container */
.map-container {
  flex: 1;
  min-height: 0;
}

.map-picker:not(.fullscreen) .map-container {
  height: 350px;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid #e5e7eb;
}

/* GPS floating button */
.gps-btn-floating {
  position: absolute;
  bottom: 120px;
  right: 16px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: white;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.map-picker:not(.fullscreen) .gps-btn-floating {
  bottom: 70px;
  right: 10px;
  width: 44px;
  height: 44px;
}

.gps-btn-floating:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
}

.gps-btn-floating:disabled {
  opacity: 0.7;
  cursor: wait;
}

.gps-icon {
  font-size: 1.5rem;
}

.gps-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Footer */
.map-footer {
  padding: 1rem;
  background: white;
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.position-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #059669;
  margin-bottom: 0.75rem;
}

.check-icon {
  font-size: 1rem;
}

.validate-btn {
  width: 100%;
  padding: 1rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.validate-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.validate-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.validate-icon {
  font-size: 1.2rem;
}

/* Non-fullscreen styles */
.map-picker:not(.fullscreen) .map-controls {
  margin-bottom: 0.5rem;
}

.map-hint {
  font-size: 0.85rem;
  color: #6b7280;
  margin-top: 0.5rem;
}

.map-hint span {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Safe area for devices with notch */
.map-picker.fullscreen .map-header {
  padding-top: max(0.75rem, env(safe-area-inset-top));
}

.map-picker.fullscreen .map-footer {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}
</style>

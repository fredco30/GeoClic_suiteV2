<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import 'leaflet/dist/leaflet.css'

interface Props {
  initialLat?: number
  initialLng?: number
  initialAddress?: string
}

interface Emits {
  (e: 'select', location: { lat: number; lng: number; address: string }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const mapContainer = ref<HTMLDivElement | null>(null)
let map: any = null
let marker: any = null
let L: any = null

const selectedCoords = ref<{ lat: number; lng: number } | null>(null)
const selectedAddress = ref('')
const loading = ref(false)
const searchQuery = ref('')
const searchResults = ref<any[]>([])
const showResults = ref(false)
const searching = ref(false)

// Centre par défaut: France
const defaultCenter = { lat: 43.5614, lng: 3.8936 } // Montpellier (zone sud France)
const defaultZoom = 13

onMounted(async () => {
  if (!mapContainer.value) return

  L = await import('leaflet')

  // Fix icônes Leaflet
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  })

  map = L.map(mapContainer.value).setView(
    [defaultCenter.lat, defaultCenter.lng],
    defaultZoom
  )

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap',
    maxZoom: 19,
  }).addTo(map)

  setTimeout(() => map?.invalidateSize(), 100)
  setTimeout(() => map?.invalidateSize(), 300)

  map.on('click', async (e: any) => {
    await selectLocation(e.latlng.lat, e.latlng.lng)
  })

  // Si des coordonnées initiales sont fournies, placer le marqueur
  if (props.initialLat && props.initialLng) {
    const lat = props.initialLat
    const lng = props.initialLng
    map.setView([lat, lng], 17)
    selectedCoords.value = { lat, lng }
    selectedAddress.value = props.initialAddress || ''
    marker = L.marker([lat, lng], { draggable: true }).addTo(map)
    marker.on('dragend', async () => {
      const pos = marker.getLatLng()
      await selectLocation(pos.lat, pos.lng)
    })
  }
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})

async function selectLocation(lat: number, lng: number) {
  loading.value = true
  selectedCoords.value = { lat, lng }

  // Placer ou déplacer le marqueur
  if (marker) {
    marker.setLatLng([lat, lng])
  } else {
    marker = L.marker([lat, lng], { draggable: true }).addTo(map)
    marker.on('dragend', async () => {
      const pos = marker.getLatLng()
      await selectLocation(pos.lat, pos.lng)
    })
  }

  // Reverse geocode (fetch natif pour ne pas envoyer le token auth)
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
    )
    const data = await res.json()
    selectedAddress.value = data.display_name || ''
  } catch {
    selectedAddress.value = ''
  }

  loading.value = false
  emitSelection()
}

function emitSelection() {
  if (selectedCoords.value) {
    emit('select', {
      lat: selectedCoords.value.lat,
      lng: selectedCoords.value.lng,
      address: selectedAddress.value,
    })
  }
}

async function searchAddress() {
  if (searchQuery.value.length < 3) {
    searchResults.value = []
    showResults.value = false
    return
  }

  searching.value = true
  try {
    // fetch natif pour ne pas envoyer le token auth à Nominatim
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery.value)}&limit=5&countrycodes=fr`
    )
    const data = await res.json()
    searchResults.value = data
    showResults.value = searchResults.value.length > 0
  } catch {
    searchResults.value = []
  }
  searching.value = false
}

async function selectSearchResult(result: any) {
  showResults.value = false
  searchQuery.value = result.display_name
  const lat = parseFloat(result.lat)
  const lng = parseFloat(result.lon)
  map?.setView([lat, lng], 17)
  await selectLocation(lat, lng)
}

let searchTimeout: any = null
function onSearchInput() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(searchAddress, 400)
}

async function onSearchKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    e.stopPropagation()
    // Si des résultats sont affichés, sélectionner le premier
    if (showResults.value && searchResults.value.length > 0) {
      await selectSearchResult(searchResults.value[0])
    } else {
      // Sinon déclencher la recherche immédiatement puis auto-sélectionner
      clearTimeout(searchTimeout)
      await searchAddress()
      if (searchResults.value.length > 0) {
        await selectSearchResult(searchResults.value[0])
      }
    }
  }
}
</script>

<template>
  <div class="map-picker-bo">
    <label class="field-label">Localisation</label>

    <!-- Barre de recherche d'adresse -->
    <div class="search-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Rechercher une adresse..."
        class="search-input"
        @input="onSearchInput"
        @keydown="onSearchKeydown"
        @focus="showResults = searchResults.length > 0"
      />
      <div v-if="showResults" class="search-results">
        <div
          v-for="result in searchResults"
          :key="result.place_id"
          class="search-result-item"
          @click="selectSearchResult(result)"
        >
          {{ result.display_name }}
        </div>
      </div>
    </div>

    <!-- Carte -->
    <div ref="mapContainer" class="map-container"></div>

    <!-- Info position -->
    <div class="map-info">
      <span v-if="loading" class="info-loading">Recherche de l'adresse...</span>
      <span v-else-if="selectedAddress" class="info-address">{{ selectedAddress }}</span>
      <span v-else class="info-hint">Cliquez sur la carte ou recherchez une adresse pour localiser le signalement</span>
    </div>
  </div>
</template>

<style scoped>
.map-picker-bo {
  margin-bottom: 1rem;
}

.field-label {
  display: block;
  font-weight: 600;
  font-size: 0.9rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.search-bar {
  position: relative;
  margin-bottom: 0.5rem;
}

.search-input {
  width: 100%;
  padding: 0.625rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 0 0 8px 8px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 50;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.search-result-item {
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.85rem;
  color: #374151;
  border-bottom: 1px solid #f3f4f6;
}

.search-result-item:hover {
  background: #eff6ff;
}

.search-result-item:last-child {
  border-bottom: none;
}

.map-container {
  height: 350px;
  border-radius: 10px;
  overflow: hidden;
  border: 2px solid #e5e7eb;
}

.map-info {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  min-height: 1.5rem;
}

.info-loading {
  color: #6b7280;
  font-style: italic;
}

.info-address {
  color: #059669;
  display: flex;
  align-items: flex-start;
  gap: 0.25rem;
}

.info-address::before {
  content: '\2713';
  font-weight: 700;
  flex-shrink: 0;
}

.info-hint {
  color: #9ca3af;
}
</style>

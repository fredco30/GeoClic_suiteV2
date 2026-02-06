<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps<{
  latitude: number
  longitude: number
  adresse?: string | null
}>()

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let marker: L.Marker | null = null

// Fix Leaflet default icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

onMounted(() => {
  initMap()
})

watch(() => [props.latitude, props.longitude], () => {
  updateMarker()
})

function initMap() {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value, {
    zoomControl: true,
    scrollWheelZoom: true,
    dragging: true,
    tap: true
  }).setView([props.latitude, props.longitude], 17)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
  }).addTo(map)

  marker = L.marker([props.latitude, props.longitude]).addTo(map)

  setTimeout(() => {
    map?.invalidateSize()
  }, 100)
}

function updateMarker() {
  if (!map || !marker) return
  const latlng: L.LatLngExpression = [props.latitude, props.longitude]
  marker.setLatLng(latlng)
  map.setView(latlng)
}

function openGoogleMaps() {
  const url = `https://www.google.com/maps/dir/?api=1&destination=${props.latitude},${props.longitude}`
  window.open(url, '_blank')
}

function openWaze() {
  const url = `https://www.waze.com/ul?ll=${props.latitude},${props.longitude}&navigate=yes`
  window.open(url, '_blank')
}

function openAppleMaps() {
  const url = `http://maps.apple.com/?daddr=${props.latitude},${props.longitude}`
  window.open(url, '_blank')
}
</script>

<template>
  <div class="mobile-map-container">
    <div ref="mapContainer" class="map"></div>

    <div v-if="adresse" class="address-bar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
        <circle cx="12" cy="10" r="3"/>
      </svg>
      <span>{{ adresse }}</span>
    </div>

    <div class="nav-buttons">
      <button class="nav-btn google" @click="openGoogleMaps">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
        </svg>
        Google Maps
      </button>

      <button class="nav-btn waze" @click="openWaze">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
        Waze
      </button>
    </div>
  </div>
</template>

<style scoped>
.mobile-map-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.map {
  flex: 1;
  min-height: 300px;
}

.address-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--gray-50);
  color: var(--gray-700);
  font-size: 0.875rem;
  border-top: 1px solid var(--gray-200);
}

.address-bar svg {
  color: var(--primary);
  flex-shrink: 0;
}

.address-bar span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-buttons {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: white;
  border-top: 1px solid var(--gray-200);
}

.nav-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem;
  border: none;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.nav-btn:active {
  transform: scale(0.98);
}

.nav-btn.google {
  background: #4285f4;
  color: white;
}

.nav-btn.waze {
  background: #33ccff;
  color: white;
}
</style>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps<{
  latitude: number
  longitude: number
  zoom?: number
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
    scrollWheelZoom: false
  }).setView([props.latitude, props.longitude], props.zoom || 16)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
  }).addTo(map)

  marker = L.marker([props.latitude, props.longitude]).addTo(map)

  // Fix map display issue when container size changes
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
</script>

<template>
  <div ref="mapContainer" class="mini-map"></div>
</template>

<style scoped>
.mini-map {
  width: 100%;
  height: 250px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}
</style>

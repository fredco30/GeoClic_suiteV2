<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePointsStore } from '@/stores/points'
import { gpsService } from '@/services/gps'
import type { GeometryType } from '@/services/api'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const router = useRouter()
const pointsStore = usePointsStore()

const mapContainer = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let markersLayer: L.LayerGroup | null = null
let polylinesLayer: L.LayerGroup | null = null
let polygonsLayer: L.LayerGroup | null = null
let userMarker: L.Marker | null = null

const isLocating = ref(false)
const showFilters = ref(false)
const showCreateMenu = ref(false)

// Initialiser la carte
const initMap = () => {
  if (!mapContainer.value || map) return

  // Position par défaut (France)
  const defaultCenter: L.LatLngExpression = [46.603354, 1.888334]
  const defaultZoom = 6

  map = L.map(mapContainer.value, {
    center: defaultCenter,
    zoom: defaultZoom,
    zoomControl: false
  })

  // Ajouter les tuiles OpenStreetMap
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19
  }).addTo(map)

  // Ajouter les contrôles de zoom en bas à droite
  L.control.zoom({ position: 'bottomright' }).addTo(map)

  // Couches pour les géométries
  polygonsLayer = L.layerGroup().addTo(map)  // Polygones en dessous
  polylinesLayer = L.layerGroup().addTo(map) // Lignes au milieu
  markersLayer = L.layerGroup().addTo(map)   // Marqueurs au-dessus

  // Charger les géométries
  loadGeometries()
}

// Obtenir la couleur d'une géométrie
const getGeomColor = (point: typeof pointsStore.points[0]): string => {
  // Utiliser la couleur du lexique si disponible
  if (point.lexique_code) {
    const item = pointsStore.lexiqueTree.find(l => l.code === point.lexique_code)
    if (item?.color_value != null) {
      if (typeof item.color_value === 'string') {
        return item.color_value.startsWith('#') ? item.color_value : `#${item.color_value}`
      }
      if (typeof item.color_value === 'number') {
        const r = (item.color_value >> 16) & 0xFF
        const g = (item.color_value >> 8) & 0xFF
        const b = item.color_value & 0xFF
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
      }
    }
  }
  // Couleurs par défaut selon le type
  const geomType = point.geom_type || 'POINT'
  switch (geomType) {
    case 'LINESTRING': return '#4CAF50'
    case 'POLYGON': return '#FF9800'
    default: return '#2196F3'
  }
}

// Obtenir l'icône pour le type de géométrie
const getGeomIcon = (geomType: string): string => {
  switch (geomType) {
    case 'LINESTRING': return '📏'
    case 'POLYGON': return '⬛'
    default: return '📍'
  }
}

// Charger toutes les géométries
const loadGeometries = () => {
  if (!markersLayer || !polylinesLayer || !polygonsLayer || !map) return

  markersLayer.clearLayers()
  polylinesLayer.clearLayers()
  polygonsLayer.clearLayers()

  const allCoords: L.LatLngExpression[] = []

  pointsStore.points.forEach(point => {
    if (!point.coordinates?.length) return

    const geomType = (point.geom_type || 'POINT').toUpperCase()
    const color = getGeomColor(point)
    const id = point.id || point._localId

    // Collecter les coordonnées pour ajuster la vue
    point.coordinates.forEach(c => {
      allCoords.push([c.latitude, c.longitude])
    })

    if (geomType === 'POLYGON' && point.coordinates.length >= 3) {
      // Dessiner le polygone
      const latLngs = point.coordinates.map(c => [c.latitude, c.longitude] as L.LatLngExpression)

      const polygon = L.polygon(latLngs, {
        color: color,
        weight: 2,
        fillColor: color,
        fillOpacity: 0.2
      })

      polygon.bindPopup(`
        <div class="marker-popup">
          <strong>⬛ ${point.name || 'Sans nom'}</strong>
          ${point.lexique_code ? `<br><small>${pointsStore.getLexiqueLabel(point.lexique_code)}</small>` : ''}
          ${point._pendingSync ? '<br><em style="color: orange;">⏳ À synchroniser</em>' : ''}
        </div>
      `)

      polygon.on('click', () => {
        if (id) {
          setTimeout(() => router.push(`/geometry/${id}`), 300)
        }
      })

      polygon.addTo(polygonsLayer!)

      // Marqueur au centre
      const center = polygon.getBounds().getCenter()
      const centerMarker = L.marker(center, {
        icon: L.divIcon({
          className: 'geom-center-marker',
          html: `<div class="center-pin" style="background: ${color}">⬛</div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        })
      })
      centerMarker.on('click', () => {
        if (id) router.push(`/geometry/${id}`)
      })
      centerMarker.addTo(markersLayer!)

    } else if (geomType === 'LINESTRING' && point.coordinates.length >= 2) {
      // Dessiner la ligne
      const latLngs = point.coordinates.map(c => [c.latitude, c.longitude] as L.LatLngExpression)

      const polyline = L.polyline(latLngs, {
        color: color,
        weight: 4,
        opacity: 0.8
      })

      polyline.bindPopup(`
        <div class="marker-popup">
          <strong>📏 ${point.name || 'Sans nom'}</strong>
          ${point.lexique_code ? `<br><small>${pointsStore.getLexiqueLabel(point.lexique_code)}</small>` : ''}
          ${point._pendingSync ? '<br><em style="color: orange;">⏳ À synchroniser</em>' : ''}
        </div>
      `)

      polyline.on('click', () => {
        if (id) {
          setTimeout(() => router.push(`/geometry/${id}`), 300)
        }
      })

      polyline.addTo(polylinesLayer!)

      // Marqueur au début de la ligne
      const startMarker = L.marker(latLngs[0], {
        icon: L.divIcon({
          className: 'geom-start-marker',
          html: `<div class="start-pin" style="background: ${color}">📏</div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        })
      })
      startMarker.on('click', () => {
        if (id) router.push(`/geometry/${id}`)
      })
      startMarker.addTo(markersLayer!)

    } else {
      // Point simple
      const { latitude, longitude } = point.coordinates[0]

      const marker = L.marker([latitude, longitude], {
        icon: L.divIcon({
          className: 'custom-marker',
          html: `<div class="marker-pin ${point._pendingSync ? 'pending' : ''}" style="color: ${color}">📍</div>`,
          iconSize: [30, 42],
          iconAnchor: [15, 42]
        })
      })

      marker.bindPopup(`
        <div class="marker-popup">
          <strong>${point.name || 'Sans nom'}</strong>
          ${point.lexique_code ? `<br><small>${pointsStore.getLexiqueLabel(point.lexique_code)}</small>` : ''}
          ${point._pendingSync ? '<br><em style="color: orange;">⏳ À synchroniser</em>' : ''}
        </div>
      `)

      marker.on('click', () => {
        if (id) {
          setTimeout(() => router.push(`/geometry/${id}`), 300)
        }
      })

      marker.addTo(markersLayer!)
    }
  })

  // Ajuster la vue si des géométries existent
  if (allCoords.length > 0) {
    const bounds = L.latLngBounds(allCoords)
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 })
    }
  }
}

// Centrer sur la position GPS
const centerOnUser = async () => {
  if (!map) return

  isLocating.value = true

  try {
    const position = await gpsService.getCurrentPosition()

    // Centrer la carte
    map.setView([position.latitude, position.longitude], 17)

    // Mettre à jour ou créer le marqueur utilisateur
    if (userMarker) {
      userMarker.setLatLng([position.latitude, position.longitude])
    } else {
      userMarker = L.marker([position.latitude, position.longitude], {
        icon: L.divIcon({
          className: 'user-marker',
          html: '<div class="user-dot"></div>',
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        })
      }).addTo(map)
    }

    // Cercle de précision
    L.circle([position.latitude, position.longitude], {
      radius: position.accuracy,
      color: '#1976D2',
      fillColor: '#1976D2',
      fillOpacity: 0.1,
      weight: 1
    }).addTo(map)

  } catch (err) {
    console.error('Erreur localisation:', err)
    alert('Impossible d\'obtenir la position GPS')
  } finally {
    isLocating.value = false
  }
}

// Créer une géométrie
const createGeometry = (type: GeometryType) => {
  showCreateMenu.value = false
  router.push({ name: 'geometry-new', query: { type } })
}

// Afficher le menu de création
const showGeometryMenu = () => {
  showCreateMenu.value = true
}

// Watch pour recharger les géométries quand les points changent
watch(() => pointsStore.points, () => {
  loadGeometries()
}, { deep: true })

onMounted(async () => {
  await pointsStore.loadPoints()
  initMap()
})

// Fermer le menu si on clique ailleurs
const closeCreateMenu = () => {
  showCreateMenu.value = false
}

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="map-page">
    <!-- Carte -->
    <div ref="mapContainer" class="map-container"></div>

    <!-- Bouton localisation -->
    <button
      class="locate-btn"
      :disabled="isLocating"
      @click="centerOnUser"
    >
      {{ isLocating ? '⏳' : '📍' }}
    </button>

    <!-- FAB Nouveau -->
    <button class="fab create-btn" @click="showGeometryMenu">
      ➕
    </button>

    <!-- Menu de création -->
    <Teleport to="body">
      <div v-if="showCreateMenu" class="create-menu-overlay" @click.self="closeCreateMenu">
        <div class="create-menu">
          <h3>Nouvelle géométrie</h3>
          <button class="menu-item" @click="createGeometry('POINT')">
            <span class="menu-icon point-icon">📍</span>
            <div class="menu-text">
              <span class="menu-label">Point</span>
              <span class="menu-desc">Un seul emplacement GPS</span>
            </div>
          </button>
          <button class="menu-item" @click="createGeometry('LINESTRING')">
            <span class="menu-icon line-icon">📏</span>
            <div class="menu-text">
              <span class="menu-label">Ligne</span>
              <span class="menu-desc">Tracé linéaire (chemin, réseau...)</span>
            </div>
          </button>
          <button class="menu-item" @click="createGeometry('POLYGON')">
            <span class="menu-icon polygon-icon">⬛</span>
            <div class="menu-text">
              <span class="menu-label">Zone</span>
              <span class="menu-desc">Surface fermée (parcelle, espace...)</span>
            </div>
          </button>
          <button class="cancel-btn" @click="closeCreateMenu">Annuler</button>
        </div>
      </div>
    </Teleport>

    <!-- Infos -->
    <div class="map-info">
      <span class="point-count">{{ pointsStore.points.length }} point(s)</span>
      <span v-if="!pointsStore.isOnline" class="offline-badge">Hors ligne</span>
    </div>
  </div>
</template>

<style scoped>
.map-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.map-container {
  flex: 1;
  z-index: 1;
}

.locate-btn {
  position: absolute;
  bottom: calc(var(--bottom-nav-height) + var(--safe-area-inset-bottom) + 80px);
  right: 16px;
  width: 48px;
  height: 48px;
  background: var(--surface-color);
  border: none;
  border-radius: 50%;
  box-shadow: var(--shadow-lg);
  font-size: 22px;
  cursor: pointer;
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.locate-btn:disabled {
  opacity: 0.7;
}

.create-btn {
  bottom: calc(var(--bottom-nav-height) + var(--safe-area-inset-bottom) + 16px);
}

/* Menu de création */
.create-menu-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
}

.create-menu {
  background: var(--surface-color);
  border-radius: var(--radius) var(--radius) 0 0;
  padding: 20px;
  padding-bottom: calc(env(safe-area-inset-bottom, 20px) + 20px);
  width: 100%;
  max-width: 500px;
}

.create-menu h3 {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 600;
  text-align: center;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 14px;
  background: var(--background-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  text-align: left;
  margin-bottom: 10px;
  transition: background 0.2s;
}

.menu-item:hover {
  background: rgba(var(--primary-rgb), 0.05);
  border-color: var(--primary-light);
}

.menu-icon {
  font-size: 28px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
}

.point-icon { background: rgba(33, 150, 243, 0.15); }
.line-icon { background: rgba(76, 175, 80, 0.15); }
.polygon-icon { background: rgba(255, 152, 0, 0.15); }

.menu-text {
  flex: 1;
}

.menu-label {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.menu-desc {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.cancel-btn {
  width: 100%;
  padding: 14px;
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 16px;
  color: var(--text-secondary);
  cursor: pointer;
  margin-top: 6px;
}

.map-info {
  position: absolute;
  top: calc(env(safe-area-inset-top, 0px) + 16px);
  left: 16px;
  display: flex;
  gap: 8px;
  z-index: 500;
}

.point-count {
  background: var(--surface-color);
  padding: 8px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: var(--shadow);
}

.offline-badge {
  background: var(--warning-color);
  color: white;
  padding: 8px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}
</style>

<style>
/* Styles globaux pour les marqueurs Leaflet */
.custom-marker {
  background: none;
  border: none;
}

.marker-pin {
  font-size: 28px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
  transition: transform 0.2s;
}

.marker-pin:hover {
  transform: scale(1.2);
}

.marker-pin.pending {
  filter: drop-shadow(0 2px 4px rgba(255, 152, 0, 0.5));
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
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.marker-popup {
  font-size: 14px;
  line-height: 1.4;
}

.leaflet-popup-content-wrapper {
  border-radius: 12px !important;
}

.leaflet-popup-content {
  margin: 12px 14px !important;
}

/* Marqueurs pour lignes et polygones */
.geom-start-marker,
.geom-center-marker {
  background: none;
  border: none;
}

.start-pin,
.center-pin {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 2px solid white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}
</style>

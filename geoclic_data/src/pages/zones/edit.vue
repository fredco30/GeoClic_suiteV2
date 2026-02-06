<template>
  <div class="zone-editor">
    <!-- Top Bar -->
    <div class="editor-toolbar">
      <div class="d-flex align-center">
        <v-btn icon="mdi-arrow-left" variant="text" @click="goBack" />
        <h2 class="text-h6 ml-2">
          {{ isEditMode ? 'Modifier la zone' : 'Créer une zone' }}
          <HelpButton page-key="zoneEdit" size="sm" />
        </h2>
      </div>

      <div class="d-flex align-center gap-3">
        <v-btn variant="text" @click="goBack">Annuler</v-btn>
        <v-btn
          v-if="hasGeometry"
          color="primary"
          @click="showSaveDialog = true"
        >
          {{ isEditMode ? 'Enregistrer' : 'Enregistrer la zone' }}
        </v-btn>
      </div>
    </div>

    <!-- Save Dialog -->
    <v-dialog v-model="showSaveDialog" max-width="450" persistent>
      <v-card>
        <v-card-title class="text-h6">
          {{ isEditMode ? 'Modifier la zone' : 'Enregistrer la zone' }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="zoneName"
            label="Nom de la zone *"
            variant="outlined"
            density="compact"
            class="mb-3"
            :rules="[v => !!v || 'Le nom est requis']"
            autofocus
          />

          <v-select
            v-model="zoneLevel"
            :items="levelOptions"
            label="Niveau hiérarchique *"
            variant="outlined"
            density="compact"
            class="mb-3"
          />

          <v-select
            v-model="zoneParentId"
            :items="parentOptions"
            label="Zone parente"
            variant="outlined"
            density="compact"
            class="mb-3"
            clearable
            :hint="parentHint"
            persistent-hint
          />

          <v-select
            v-model="zoneType"
            :items="zoneTypes"
            label="Type de zone"
            variant="outlined"
            density="compact"
            class="mb-3"
          />

          <v-text-field
            v-model="zoneCode"
            label="Code (optionnel)"
            variant="outlined"
            density="compact"
            hint="Ex: Q01, SEC-NORD..."
            persistent-hint
            class="mb-3"
          />

          <v-checkbox
            v-model="zoneIsGlobal"
            label="Zone globale (partagée par tous les projets)"
            density="compact"
            hide-details
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="cancelSave">Annuler</v-btn>
          <v-btn
            color="primary"
            :loading="saving"
            :disabled="!zoneName.trim()"
            @click="saveZone"
          >
            {{ isEditMode ? 'Enregistrer' : 'Créer la zone' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Map Container -->
    <div class="map-container" ref="mapContainer">
      <!-- Map Controls Overlay -->
      <div class="map-controls">
        <v-card class="control-card" elevation="2">
          <v-btn-toggle v-model="currentBasemap" mandatory density="compact">
            <v-btn value="osm" size="small">
              <v-icon size="small">mdi-map</v-icon>
              <span class="ml-1">OSM</span>
            </v-btn>
            <v-btn value="satellite" size="small">
              <v-icon size="small">mdi-satellite-variant</v-icon>
              <span class="ml-1">Satellite</span>
            </v-btn>
            <v-btn value="cadastre" size="small">
              <v-icon size="small">mdi-vector-square</v-icon>
              <span class="ml-1">Cadastre</span>
            </v-btn>
          </v-btn-toggle>
        </v-card>

        <v-card class="control-card mt-2" elevation="2">
          <div class="d-flex flex-column gap-1 pa-1">
            <v-btn
              :color="isDrawing ? 'primary' : undefined"
              :variant="isDrawing ? 'flat' : 'text'"
              size="small"
              @click.stop="toggleDraw"
            >
              <v-icon size="small">mdi-vector-polygon</v-icon>
              <span class="ml-1">Dessiner</span>
            </v-btn>
            <v-btn
              v-if="hasGeometry"
              variant="text"
              size="small"
              @click.stop="editGeometry"
            >
              <v-icon size="small">mdi-pencil</v-icon>
              <span class="ml-1">Modifier</span>
            </v-btn>
            <v-btn
              v-if="hasGeometry"
              variant="text"
              size="small"
              color="error"
              @click.stop="clearGeometry"
            >
              <v-icon size="small">mdi-delete</v-icon>
              <span class="ml-1">Effacer</span>
            </v-btn>
          </div>
        </v-card>
      </div>

      <!-- Drawing Instructions -->
      <div class="drawing-instructions" v-if="isDrawing">
        <v-alert type="info" variant="tonal" density="compact">
          <div><strong>Mode dessin actif</strong> - Cliquez pour ajouter des points. Double-cliquez pour terminer le polygone.</div>
          <div class="mt-1" style="font-size: 0.85em; opacity: 0.9;">Maintenez le clic droit pour déplacer la carte.</div>
        </v-alert>
      </div>

      <!-- Overlap Warning -->
      <div class="overlap-warning" v-if="overlapWarning">
        <v-alert type="warning" variant="tonal" density="compact" closable @click:close="overlapWarning = ''">
          <strong>Chevauchement détecté</strong> - {{ overlapWarning }}
        </v-alert>
      </div>

      <!-- Snap Info -->
      <div class="snap-info" v-if="snapEnabled">
        <v-chip size="small" color="success" variant="flat">
          <v-icon size="small" start>mdi-magnet</v-icon>
          Accrochage actif
        </v-chip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import '@geoman-io/leaflet-geoman-free'
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css'
import api from '@/services/api'
import HelpButton from '@/components/help/HelpButton.vue'

const route = useRoute()
const router = useRouter()

// State
const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let drawnLayer: L.Polygon | null = null
let existingZonesLayer: L.GeoJSON | null = null

const zoneName = ref('')
const zoneCode = ref('')
const zoneType = ref('quartier')
const zoneLevel = ref(2)
const zoneParentId = ref<string | null>(null)
const zoneIsGlobal = ref(true)
const currentBasemap = ref('osm')
const isDrawing = ref(false)
const saving = ref(false)
const overlapWarning = ref('')
const snapEnabled = ref(true)
const showSaveDialog = ref(false)
const availableParents = ref<Array<{ id: string; name: string; level: number }>>([])

// Right-click pan state
let isRightClickPanning = false
let panStartPoint: { x: number; y: number } | null = null

const zoneTypes = [
  { title: 'Quartier', value: 'quartier' },
  { title: 'Commune', value: 'commune' },
  { title: 'Secteur', value: 'secteur' },
]

const levelOptions = [
  { title: 'Niveau 1 - Commune', value: 1 },
  { title: 'Niveau 2 - Quartier', value: 2 },
  { title: 'Niveau 3 - Secteur', value: 3 },
]

// Options de parent filtrées selon le niveau sélectionné
const parentOptions = computed(() => {
  // Un parent doit être de niveau inférieur (level - 1)
  const requiredParentLevel = zoneLevel.value - 1
  if (requiredParentLevel < 1) {
    return [] // Les communes (niveau 1) n'ont pas de parent
  }
  return availableParents.value
    .filter(z => z.level === requiredParentLevel)
    .map(z => ({ title: z.name, value: z.id }))
})

const parentHint = computed(() => {
  if (zoneLevel.value === 1) {
    return 'Les communes n\'ont pas de parent'
  } else if (zoneLevel.value === 2) {
    return 'Sélectionnez la commune parente'
  } else {
    return 'Sélectionnez le quartier parent'
  }
})

// Basemap layers
const basemaps: Record<string, L.TileLayer> = {}

// Computed
const isEditMode = computed(() => !!route.params.id)
const hasGeometry = computed(() => drawnLayer !== null)
const canSave = computed(() => zoneName.value.trim() !== '' && hasGeometry.value)

// Methods
function goBack() {
  router.push('/zones')
}

function initMap() {
  if (!mapContainer.value) return

  // Create map
  map = L.map(mapContainer.value, {
    center: [46.603354, 1.888334], // France center
    zoom: 6,
    zoomControl: false,
  })

  // Add zoom control to bottom right
  L.control.zoom({ position: 'bottomright' }).addTo(map)

  // Create basemap layers
  basemaps.osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 19,
  })

  basemaps.satellite = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    {
      attribution: '© Esri',
      maxZoom: 19,
    }
  )

  basemaps.cadastre = L.tileLayer(
    'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&TILEMATRIXSET=PM&TILEMATRIX={z}&TILECOL={x}&TILEROW={y}&LAYER=CADASTRALPARCELS.PARCELLAIRE_EXPRESS&FORMAT=image/png&STYLE=normal',
    {
      attribution: '© IGN',
      maxZoom: 19,
    }
  )

  // Add default basemap
  basemaps.osm.addTo(map)

  // Initialize Geoman
  map.pm.addControls({
    position: 'topleft',
    drawControls: false, // We use our own UI
    editControls: false,
    optionsControls: false,
    customControls: false,
  })

  // Enable snapping globally
  map.pm.setGlobalOptions({
    snappable: true,
    snapDistance: 15,
    snapSegment: true,
    allowSelfIntersection: false,
  })

  // Event handlers
  map.on('pm:create', (e: any) => {
    // Remove any existing drawn layer
    if (drawnLayer) {
      map!.removeLayer(drawnLayer)
    }
    drawnLayer = e.layer as L.Polygon
    isDrawing.value = false

    // Check for overlaps
    checkOverlap()

    // Open save dialog (only in create mode)
    if (!isEditMode.value) {
      showSaveDialog.value = true
    }
  })

  map.on('pm:drawstart', () => {
    isDrawing.value = true
  })

  map.on('pm:drawend', () => {
    isDrawing.value = false
  })

  // Prevent click propagation from map controls to the map
  const mapControlsEl = mapContainer.value?.querySelector('.map-controls')
  if (mapControlsEl) {
    L.DomEvent.disableClickPropagation(mapControlsEl as HTMLElement)
  }

  // Right-click pan during drawing mode
  const mapEl = map.getContainer()

  mapEl.addEventListener('mousedown', (e: MouseEvent) => {
    if (e.button === 2 && isDrawing.value) {
      isRightClickPanning = true
      panStartPoint = { x: e.clientX, y: e.clientY }
      mapEl.style.cursor = 'grabbing'
      e.preventDefault()
    }
  })

  mapEl.addEventListener('mousemove', (e: MouseEvent) => {
    if (isRightClickPanning && panStartPoint && map) {
      const dx = panStartPoint.x - e.clientX
      const dy = panStartPoint.y - e.clientY
      map.panBy([dx, dy], { animate: false })
      panStartPoint = { x: e.clientX, y: e.clientY }
    }
  })

  mapEl.addEventListener('mouseup', (e: MouseEvent) => {
    if (e.button === 2) {
      isRightClickPanning = false
      panStartPoint = null
      mapEl.style.cursor = ''
    }
  })

  mapEl.addEventListener('mouseleave', () => {
    isRightClickPanning = false
    panStartPoint = null
    mapEl.style.cursor = ''
  })

  // Disable context menu on right-click during drawing
  mapEl.addEventListener('contextmenu', (e: MouseEvent) => {
    if (isDrawing.value) {
      e.preventDefault()
    }
  })

  // Load existing zones for snapping
  loadExistingZones()
}

async function loadExistingZones() {
  try {
    const response = await api.get('/zones/geojson')
    const geojson = response.data

    // Filter out current zone if editing
    if (isEditMode.value && route.params.id) {
      geojson.features = geojson.features.filter(
        (f: any) => f.id !== route.params.id
      )
    }

    existingZonesLayer = L.geoJSON(geojson, {
      style: {
        color: '#666',
        weight: 2,
        fillOpacity: 0.1,
        dashArray: '5, 5',
      },
      pmIgnore: false, // Enable snapping to these layers
    }).addTo(map!)

    // Fit to bounds if there are existing zones
    if (geojson.features.length > 0) {
      map!.fitBounds(existingZonesLayer.getBounds(), { padding: [50, 50] })
    }
  } catch (error) {
    console.error('Erreur chargement zones:', error)
  }
}

async function loadAvailableParents() {
  try {
    const response = await api.get('/zones')
    availableParents.value = response.data
      .filter((z: any) => z.id !== route.params.id) // Exclude self in edit mode
      .map((z: any) => ({
        id: z.id,
        name: z.name,
        level: z.level || 2
      }))
  } catch (error) {
    console.error('Erreur chargement zones parentes:', error)
  }
}

async function loadZoneForEdit() {
  if (!isEditMode.value || !route.params.id) return

  try {
    const response = await api.get(`/zones/${route.params.id}`)
    const zone = response.data

    zoneName.value = zone.name
    zoneCode.value = zone.code || ''
    zoneType.value = zone.zone_type || 'quartier'
    zoneLevel.value = zone.level || 2
    zoneParentId.value = zone.parent_id || null
    zoneIsGlobal.value = zone.is_global !== false

    if (zone.geojson) {
      // Add the geometry to the map
      drawnLayer = L.geoJSON(zone.geojson).getLayers()[0] as L.Polygon
      drawnLayer.setStyle({
        color: '#1976d2',
        weight: 3,
        fillOpacity: 0.2,
      })
      drawnLayer.addTo(map!)

      // Enable editing on this layer
      drawnLayer.pm.enable()

      // Fit to zone bounds
      if (zone.bbox) {
        map!.fitBounds([
          [zone.bbox[1], zone.bbox[0]],
          [zone.bbox[3], zone.bbox[2]],
        ], { padding: [50, 50] })
      }
    }
  } catch (error) {
    console.error('Erreur chargement zone:', error)
  }
}

function toggleDraw() {
  if (!map) return

  if (isDrawing.value) {
    map.pm.disableDraw()
    isDrawing.value = false
  } else {
    // Clear existing if any
    if (drawnLayer) {
      map.removeLayer(drawnLayer)
      drawnLayer = null
    }
    map.pm.enableDraw('Polygon', {
      snappable: true,
      snapDistance: 15,
      allowSelfIntersection: false,
    })
    isDrawing.value = true
  }
}

function editGeometry() {
  if (!drawnLayer) return
  drawnLayer.pm.enable()
}

function clearGeometry() {
  if (!drawnLayer || !map) return
  map.removeLayer(drawnLayer)
  drawnLayer = null
  overlapWarning.value = ''
}

function cancelSave() {
  showSaveDialog.value = false
  // Reset form if it was a new zone
  if (!isEditMode.value) {
    zoneName.value = ''
    zoneCode.value = ''
    zoneType.value = 'quartier'
    zoneLevel.value = 2
    zoneParentId.value = null
    zoneIsGlobal.value = true
  }
}

async function checkOverlap() {
  if (!drawnLayer) return

  try {
    const geojson = drawnLayer.toGeoJSON().geometry

    const response = await api.post('/zones/check-overlap', geojson, {
      params: isEditMode.value ? { exclude_zone_id: route.params.id } : {},
    })

    if (response.data.has_overlap) {
      overlapWarning.value = `Zones concernées: ${response.data.overlapping_zones.join(', ')}`
    } else {
      overlapWarning.value = ''
    }
  } catch (error) {
    console.error('Erreur vérification chevauchement:', error)
  }
}

async function saveZone() {
  if (!zoneName.value.trim() || !drawnLayer) return

  saving.value = true

  try {
    const geojson = drawnLayer.toGeoJSON().geometry

    const payload = {
      name: zoneName.value.trim(),
      code: zoneCode.value.trim() || null,
      zone_type: zoneType.value,
      level: zoneLevel.value,
      parent_id: zoneLevel.value > 1 ? zoneParentId.value : null,
      is_global: zoneIsGlobal.value,
      geojson,
    }

    if (isEditMode.value) {
      await api.put(`/zones/${route.params.id}`, payload)
    } else {
      await api.post('/zones', payload)
    }

    showSaveDialog.value = false
    router.push('/zones')
  } catch (error: any) {
    console.error('Erreur sauvegarde:', error)
    alert(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
  } finally {
    saving.value = false
  }
}

// Watch basemap changes
watch(currentBasemap, (newValue, oldValue) => {
  if (!map) return
  basemaps[oldValue]?.remove()
  basemaps[newValue]?.addTo(map)
})

// Clear parent when level changes to 1 (communes have no parent)
watch(zoneLevel, (newLevel) => {
  if (newLevel === 1) {
    zoneParentId.value = null
  }
})

// Lifecycle
onMounted(async () => {
  await nextTick()
  initMap()
  await loadAvailableParents()
  if (isEditMode.value) {
    await loadZoneForEdit()
  }
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.zone-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  background: white;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  z-index: 1001;
}

.map-container {
  flex: 1;
  position: relative;
}

.map-container :deep(.leaflet-container) {
  height: 100%;
  width: 100%;
}

.map-controls {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 1000;
}

.control-card {
  padding: 4px;
}

.drawing-instructions {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}

.overlap-warning {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 400px;
}

.snap-info {
  position: absolute;
  bottom: 16px;
  right: 16px;
  z-index: 1000;
}

.gap-3 {
  gap: 12px;
}

.gap-1 {
  gap: 4px;
}
</style>

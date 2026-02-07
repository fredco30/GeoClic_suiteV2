<template>
  <div class="carte-container">
    <!-- Toolbar -->
    <v-card class="toolbar-card mb-4">
      <v-card-text class="py-2">
        <v-row align="center" dense>
          <v-col cols="12" md="3">
            <v-select
              v-model="selectedProjet"
              label="Projet"
              :items="projets"
              item-title="nom"
              item-value="id"
              clearable
              hide-details
              density="compact"
              @update:model-value="filterPoints"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="selectedCategorie"
              label="Catégorie"
              :items="categories"
              item-title="libelle"
              item-value="id"
              clearable
              hide-details
              density="compact"
              @update:model-value="filterPoints"
            />
          </v-col>
          <v-col cols="12" md="2">
            <v-text-field
              v-model="searchText"
              label="Rechercher"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
              density="compact"
              @keyup.enter="filterPoints"
            />
          </v-col>
          <v-col v-if="zones.length > 0" cols="12" md="2">
            <v-select
              v-model="selectedZoneFilter"
              label="Zone"
              :items="zoneFilterItems"
              item-title="name"
              item-value="id"
              clearable
              hide-details
              density="compact"
              prepend-inner-icon="mdi-map-marker-radius"
              @update:model-value="onZoneFilterChange"
            />
          </v-col>
          <v-col cols="12" md="4" class="d-flex justify-end gap-2">
            <v-btn-toggle v-model="mapStyle" mandatory density="compact">
              <v-btn value="streets" size="small">
                <v-icon>mdi-map</v-icon>
              </v-btn>
              <v-btn value="satellite" size="small">
                <v-icon>mdi-satellite-variant</v-icon>
              </v-btn>
            </v-btn-toggle>
            <v-btn
              :color="showZones ? 'primary' : undefined"
              :variant="showZones ? 'elevated' : 'outlined'"
              size="small"
              @click="toggleZones"
            >
              <v-icon start>mdi-map-marker-radius</v-icon>
              Zones
            </v-btn>
            <v-btn color="primary" size="small" @click="startCreate">
              <v-icon start>mdi-map-marker-plus</v-icon>
              Nouveau point
            </v-btn>
            <v-btn size="small" @click="exportData">
              <v-icon start>mdi-download</v-icon>
              Export
            </v-btn>
            <HelpButton page-key="carte" size="sm" />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Map -->
    <v-card class="map-card">
      <div ref="mapContainer" class="map-container" />

      <!-- Create mode overlay -->
      <v-fade-transition>
        <div v-if="createMode" class="create-overlay">
          <v-alert type="info" variant="tonal" class="ma-4" closable @click:close="cancelCreate">
            <v-icon start>mdi-crosshairs-gps</v-icon>
            Cliquez sur la carte pour placer le nouveau point
          </v-alert>
        </div>
      </v-fade-transition>

      <!-- Duplicate warning overlay -->
      <v-fade-transition>
        <div v-if="duplicateWarning" class="duplicate-overlay">
          <v-alert type="warning" variant="elevated" class="ma-4">
            <v-icon start>mdi-alert</v-icon>
            <strong>Doublon potentiel détecté !</strong>
            <p class="mb-2">
              Un point existe à {{ duplicateDistance.toFixed(1) }}m de cette position.
            </p>
            <div class="d-flex gap-2">
              <v-btn size="small" color="warning" @click="forceCreate">
                Créer quand même
              </v-btn>
              <v-btn size="small" variant="outlined" @click="cancelCreate">
                Annuler
              </v-btn>
              <v-btn size="small" variant="text" @click="showDuplicatePoint">
                Voir le point existant
              </v-btn>
            </div>
          </v-alert>
        </div>
      </v-fade-transition>
    </v-card>

    <!-- Side panel for point details -->
    <v-navigation-drawer
      v-model="showPanel"
      location="right"
      width="400"
      temporary
    >
      <template v-if="selectedPoint">
        <v-card flat>
          <v-card-title class="d-flex align-center">
            <v-icon :color="selectedPoint.couleur || undefined" class="mr-2">
              {{ selectedPoint.icone || 'mdi-map-marker' }}
            </v-icon>
            {{ selectedPoint.nom }}
            <v-spacer />
            <v-btn icon size="small" variant="text" @click="showPanel = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-card-title>

          <v-card-text>
            <v-img
              v-if="selectedPoint.photos?.length"
              :src="getPhotoUrl(selectedPoint.photos[0])"
              height="200"
              cover
              class="rounded mb-4 cursor-pointer"
              @click="openPhotoInNewTab(selectedPoint.photos[0])"
            />

            <!-- Classification -->
            <div class="mb-4" v-if="getPointHierarchy(selectedPoint).famille">
              <v-row dense>
                <v-col cols="6">
                  <div class="text-caption text-grey">Famille</div>
                  <div>{{ getPointHierarchy(selectedPoint).famille }}</div>
                </v-col>
                <v-col cols="6">
                  <div class="text-caption text-grey">Catégorie</div>
                  <div>{{ getPointHierarchy(selectedPoint).categorie || '-' }}</div>
                </v-col>
              </v-row>
              <v-row dense class="mt-1">
                <v-col cols="6">
                  <div class="text-caption text-grey">Type</div>
                  <v-chip size="small" :color="selectedPoint.couleur || 'primary'">
                    {{ getPointHierarchy(selectedPoint).type || '-' }}
                  </v-chip>
                </v-col>
                <v-col cols="6">
                  <div class="text-caption text-grey">Projet</div>
                  <div>{{ getPointProjet(selectedPoint) }}</div>
                </v-col>
              </v-row>
            </div>

            <v-divider class="my-3" v-if="getPointHierarchy(selectedPoint).famille" />

            <div class="mb-4">
              <div class="text-caption text-grey">Description</div>
              <div>{{ selectedPoint.description || 'Aucune description' }}</div>
            </div>

            <v-row dense>
              <v-col cols="6">
                <div class="text-caption text-grey">Latitude</div>
                <div>{{ selectedPoint.latitude.toFixed(6) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-grey">Longitude</div>
                <div>{{ selectedPoint.longitude.toFixed(6) }}</div>
              </v-col>
            </v-row>

            <v-divider class="my-4" />

            <div class="text-subtitle-2 mb-2">Données techniques</div>
            <v-list density="compact">
              <v-list-item
                v-for="(value, key) in selectedPoint.donnees_techniques"
                :key="key"
              >
                <v-list-item-title>{{ key }}</v-list-item-title>
                <v-list-item-subtitle>
                  <template v-if="isColorValue(String(value))">
                    <span class="color-swatch" :style="{ backgroundColor: String(value) }"></span>
                    {{ value }}
                  </template>
                  <template v-else>
                    {{ formatValue(value) }}
                  </template>
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="!Object.keys(selectedPoint.donnees_techniques || {}).length">
                <v-list-item-subtitle class="text-grey">
                  Aucune donnée technique
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>

            <v-divider class="my-4" />

            <div class="text-caption text-grey">
              Créé le {{ formatDate(selectedPoint.created_at) }}
            </div>
          </v-card-text>

          <v-card-actions>
            <v-btn color="primary" variant="text" @click="editPoint">
              <v-icon start>mdi-pencil</v-icon>
              Modifier
            </v-btn>
            <v-btn color="info" variant="text" @click="generateQR">
              <v-icon start>mdi-qrcode</v-icon>
              QR Code
            </v-btn>
            <v-spacer />
            <v-btn color="error" variant="text" @click="confirmDeletePoint">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </template>
    </v-navigation-drawer>

    <!-- Create/Edit dialog -->
    <v-dialog v-model="showEditDialog" max-width="700" persistent>
      <v-card>
        <v-card-title>
          {{ editingPoint ? 'Modifier le point' : 'Nouveau point' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <v-text-field
              v-model="pointForm.name"
              label="Nom du point *"
              :rules="[v => !!v || 'Nom requis']"
            />
            <v-textarea
              v-model="pointForm.comment"
              label="Description"
              rows="2"
              class="mt-4"
            />
            <v-row class="mt-4">
              <v-col cols="6">
                <v-text-field
                  v-model.number="pointForm.latitude"
                  label="Latitude *"
                  type="number"
                  step="0.000001"
                  :rules="[v => !!v || 'Latitude requise']"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="pointForm.longitude"
                  label="Longitude *"
                  type="number"
                  step="0.000001"
                  :rules="[v => !!v || 'Longitude requise']"
                />
              </v-col>
            </v-row>
            <v-select
              v-model="pointForm.lexique_code"
              label="Catégorie *"
              :items="allCategories"
              item-title="libelle"
              item-value="code"
              :rules="[v => !!v || 'Catégorie requise']"
              class="mt-4"
            />
            <v-select
              v-model="pointForm.project_id"
              label="Projet *"
              :items="projets"
              item-title="nom"
              item-value="id"
              :rules="[v => !!v || 'Projet requis']"
              class="mt-4"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeEditDialog">Annuler</v-btn>
          <v-btn color="primary" :disabled="!formValid" @click="savePoint">
            {{ editingPoint ? 'Modifier' : 'Créer' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete confirmation -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">Supprimer le point</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer le point
          <strong>{{ selectedPoint?.nom }}</strong> ?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Annuler</v-btn>
          <v-btn color="error" @click="deletePoint">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Anti-duplicate settings -->
    <v-dialog v-model="showDuplicateSettings" max-width="400">
      <v-card>
        <v-card-title>Paramètres anti-doublon</v-card-title>
        <v-card-text>
          <v-slider
            v-model="duplicateRadius"
            label="Rayon de détection"
            :min="1"
            :max="50"
            :step="1"
            thumb-label="always"
          >
            <template v-slot:append>
              <span class="text-body-2">{{ duplicateRadius }}m</span>
            </template>
          </v-slider>
          <p class="text-caption text-grey">
            Un avertissement sera affiché si un point existe dans ce rayon.
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="showDuplicateSettings = false">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { usePointsStore, type Point } from '@/stores/points'
import HelpButton from '@/components/help/HelpButton.vue'
import { useLexiqueStore } from '@/stores/lexique'
import { projetsAPI, qrcodesAPI } from '@/services/api'
import api from '@/services/api'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

defineOptions({
  meta: {
    layout: 'admin',
  },
})

const pointsStore = usePointsStore()
const lexiqueStore = useLexiqueStore()

// Map refs
const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let markersLayer: L.LayerGroup | null = null
let zonesLayer: L.LayerGroup | null = null
let tempMarker: L.Marker | null = null

// State
const selectedProjet = ref<string | null>(null)
const selectedCategorie = ref<string | null>(null)
const searchText = ref('')
const mapStyle = ref('streets')
const projets = ref<any[]>([])
const showPanel = ref(false)
const selectedPoint = ref<Point | null>(null)
const createMode = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showDuplicateSettings = ref(false)
const editingPoint = ref<Point | null>(null)
const formValid = ref(false)
const duplicateRadius = ref(5)
const duplicateWarning = ref(false)
const duplicateDistance = ref(0)
const nearbyPoints = ref<Point[]>([])
const pendingCoords = ref<{ lat: number; lng: number } | null>(null)
const hasMainZone = ref(false)
const showZones = ref(false)
const zones = ref<any[]>([])
const selectedZoneFilter = ref<string | null>(null)

const pointForm = ref({
  name: '',
  comment: '',
  latitude: 0,
  longitude: 0,
  lexique_code: '',
  project_id: '',
  type: 'Point',  // Type requis par l'API
})

// Computed
const categories = computed(() => lexiqueStore.entries.filter(e => e.niveau === 1))
const allCategories = computed(() => lexiqueStore.entries)
const points = computed(() => pointsStore.points)
const zoneFilterItems = computed(() => {
  // Grouper par type avec séparateurs
  const items: any[] = []
  const communes = zones.value.filter(z => z.zone_type === 'commune')
  const quartiers = zones.value.filter(z => z.zone_type === 'quartier')
  const secteurs = zones.value.filter(z => z.zone_type === 'secteur')

  if (communes.length > 0) {
    items.push({ name: '--- Communes ---', id: null, disabled: true })
    items.push(...communes.map(z => ({ name: z.name, id: z.id })))
  }
  if (quartiers.length > 0) {
    items.push({ name: '--- Quartiers ---', id: null, disabled: true })
    items.push(...quartiers.map(z => ({ name: z.name, id: z.id })))
  }
  if (secteurs.length > 0) {
    items.push({ name: '--- Secteurs ---', id: null, disabled: true })
    items.push(...secteurs.map(z => ({ name: z.name, id: z.id })))
  }

  return items
})

// Tile layers
const tileLayers = {
  streets: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }),
  satellite: L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    {
      attribution: '&copy; Esri',
    }
  ),
}

// Methods
function initMap() {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value).setView([46.603354, 1.888334], 6) // Centre de la France
  zonesLayer = L.layerGroup().addTo(map)
  markersLayer = L.layerGroup().addTo(map)

  tileLayers.streets.addTo(map)

  // Click handler for creating points
  map.on('click', onMapClick)
}

async function centerOnMainZone() {
  try {
    const response = await api.get('/zones')
    zones.value = response.data

    // Chercher la zone principale (commune) ou la première zone disponible
    const mainZone = zones.value.find((z: any) => z.zone_type === 'commune') || zones.value[0]

    if (mainZone?.id && map) {
      // Récupérer les détails de la zone pour obtenir le bbox
      const detailResponse = await api.get(`/zones/${mainZone.id}`)
      const zoneWithBbox = detailResponse.data

      if (zoneWithBbox.bbox) {
        // bbox format: [minLng, minLat, maxLng, maxLat]
        map.fitBounds([
          [zoneWithBbox.bbox[1], zoneWithBbox.bbox[0]],
          [zoneWithBbox.bbox[3], zoneWithBbox.bbox[2]],
        ], { padding: [50, 50] })
        hasMainZone.value = true
      }
    }
  } catch (error) {
    console.error('Erreur chargement zones:', error)
  }
}

// Zone colors by type
const zoneColors: Record<string, string> = {
  commune: '#1976D2',
  quartier: '#43A047',
  secteur: '#FF9800',
}

function toggleZones() {
  showZones.value = !showZones.value
  if (showZones.value) {
    loadZonesGeoJson()
  } else {
    zonesLayer?.clearLayers()
  }
}

async function loadZonesGeoJson() {
  if (!map || !zonesLayer) return

  try {
    const response = await api.get('/zones/geojson')
    const geojson = response.data

    zonesLayer.clearLayers()

    if (geojson.features && geojson.features.length > 0) {
      const geoJsonLayer = L.geoJSON(geojson, {
        style: (feature) => {
          const zoneType = feature?.properties?.zone_type || 'quartier'
          const color = zoneColors[zoneType] || '#666'
          const isSelected = selectedZoneFilter.value === feature?.id

          return {
            color: color,
            weight: isSelected ? 3 : 2,
            opacity: isSelected ? 1 : 0.7,
            fillColor: color,
            fillOpacity: isSelected ? 0.25 : 0.1,
            dashArray: isSelected ? '' : '5, 5',
          }
        },
        onEachFeature: (feature, layer) => {
          // Popup avec nom et type
          const props = feature.properties || {}
          const popupContent = `
            <div style="min-width: 150px;">
              <strong>${props.name || 'Zone'}</strong>
              <br>
              <span style="color: ${zoneColors[props.zone_type] || '#666'}; font-size: 11px;">
                ${props.zone_type === 'commune' ? 'Commune' : props.zone_type === 'quartier' ? 'Quartier' : 'Secteur'}
              </span>
              ${props.code ? `<br><span style="font-size: 10px; color: #888;">Code: ${props.code}</span>` : ''}
            </div>
          `
          layer.bindPopup(popupContent)

          // Click pour filtrer par zone
          layer.on('click', () => {
            if (selectedZoneFilter.value === feature.id) {
              selectedZoneFilter.value = null
            } else {
              selectedZoneFilter.value = feature.id as string
            }
            // Rafraichir le style des zones
            loadZonesGeoJson()
          })
        },
      })

      zonesLayer.addLayer(geoJsonLayer)
    }
  } catch (error) {
    console.error('Erreur chargement zones GeoJSON:', error)
  }
}

async function onZoneFilterChange(zoneId: string | null) {
  // Rafraichir l'affichage des zones si visible
  if (showZones.value) {
    loadZonesGeoJson()
  }

  // Zoomer sur la zone sélectionnée
  if (zoneId && map) {
    try {
      const response = await api.get(`/zones/${zoneId}`)
      const zone = response.data

      if (zone.bbox) {
        map.fitBounds([
          [zone.bbox[1], zone.bbox[0]],
          [zone.bbox[3], zone.bbox[2]],
        ], { padding: [50, 50] })
      }
    } catch (error) {
      console.error('Erreur zoom zone:', error)
    }
  }

  // Note: Le filtrage des points par zone nécessiterait une modification de l'API
  // pour supporter le filtrage par intersection spatiale
}

function onMapClick(e: L.LeafletMouseEvent) {
  if (!createMode.value) return

  const { lat, lng } = e.latlng
  pendingCoords.value = { lat, lng }

  // Check for duplicates
  checkDuplicate(lat, lng)
}

async function checkDuplicate(lat: number, lng: number) {
  const result = await pointsStore.checkDuplicate(lat, lng)

  if (result.hasDuplicate) {
    duplicateWarning.value = true
    duplicateDistance.value = result.distance
    nearbyPoints.value = result.nearbyPoints

    // Show temp marker
    if (tempMarker) {
      map?.removeLayer(tempMarker)
    }
    tempMarker = L.marker([lat, lng], {
      icon: L.divIcon({
        className: 'temp-marker',
        html: '<div class="temp-marker-icon warning"></div>',
      }),
    }).addTo(map!)
  } else {
    // No duplicate, open create dialog
    openCreateDialog(lat, lng)
  }
}

function forceCreate() {
  if (pendingCoords.value) {
    duplicateWarning.value = false
    openCreateDialog(pendingCoords.value.lat, pendingCoords.value.lng)
  }
}

function openCreateDialog(lat: number, lng: number) {
  editingPoint.value = null
  pointForm.value = {
    name: '',
    comment: '',
    latitude: lat,
    longitude: lng,
    lexique_code: '',
    project_id: selectedProjet.value || '',
    type: 'Point',
  }
  createMode.value = false
  duplicateWarning.value = false
  showEditDialog.value = true
}

function startCreate() {
  createMode.value = true
  duplicateWarning.value = false
}

function cancelCreate() {
  createMode.value = false
  duplicateWarning.value = false
  pendingCoords.value = null
  if (tempMarker) {
    map?.removeLayer(tempMarker)
    tempMarker = null
  }
}

function showDuplicatePoint() {
  const firstPoint = nearbyPoints.value[0]
  if (firstPoint) {
    selectPoint(firstPoint)
    cancelCreate()
  }
}

function closeEditDialog() {
  showEditDialog.value = false
  editingPoint.value = null
  if (tempMarker) {
    map?.removeLayer(tempMarker)
    tempMarker = null
  }
}

async function savePoint() {
  // Transformer les données pour l'API
  const apiData = {
    name: pointForm.value.name,
    type: pointForm.value.type || 'Point',
    lexique_code: pointForm.value.lexique_code,
    project_id: pointForm.value.project_id,
    comment: pointForm.value.comment,
    coordinates: [
      {
        latitude: pointForm.value.latitude,
        longitude: pointForm.value.longitude,
      }
    ],
    geom_type: 'POINT',
  }

  if (editingPoint.value) {
    await pointsStore.updatePoint(editingPoint.value.id, apiData)
  } else {
    await pointsStore.createPoint(apiData)
  }
  closeEditDialog()
  await loadPoints()
}

function editPoint() {
  if (!selectedPoint.value) return
  editingPoint.value = selectedPoint.value
  pointForm.value = {
    name: selectedPoint.value.nom || selectedPoint.value.name || '',
    comment: selectedPoint.value.description || selectedPoint.value.comment || '',
    latitude: selectedPoint.value.latitude,
    longitude: selectedPoint.value.longitude,
    lexique_code: selectedPoint.value.lexique_id || selectedPoint.value.lexique_code || '',
    project_id: selectedPoint.value.projet_id || selectedPoint.value.project_id || '',
    type: selectedPoint.value.type || 'Point',
  }
  showEditDialog.value = true
}

function confirmDeletePoint() {
  showDeleteDialog.value = true
}

async function deletePoint() {
  if (!selectedPoint.value) return
  await pointsStore.deletePoint(selectedPoint.value.id)
  showDeleteDialog.value = false
  showPanel.value = false
  selectedPoint.value = null
  await loadPoints()
}

function selectPoint(point: Point) {
  selectedPoint.value = point
  showPanel.value = true

  // Center map on point
  if (map) {
    map.setView([point.latitude, point.longitude], 17)
  }
}

async function loadPoints() {
  pointsStore.setFilters({
    projet_id: selectedProjet.value,
    lexique_id: selectedCategorie.value,
    search: searchText.value,
  })
  await pointsStore.fetchPoints()
  updateMarkers()
}

function filterPoints() {
  loadPoints()
}

function updateMarkers() {
  if (!markersLayer) return

  markersLayer.clearLayers()

  points.value.forEach(point => {
    const lexiqueCode = point.lexique_code || point.lexique_id
    const category = lexiqueCode ? lexiqueStore.getByCode(lexiqueCode) : null
    const bgColor = category?.couleur || point.couleur || '#1976D2'
    const iconClass = category?.icone || point.icone || 'mdi-map-marker'
    const marker = L.marker([point.latitude, point.longitude], {
      icon: L.divIcon({
        className: 'custom-marker',
        iconSize: [36, 36],
        iconAnchor: [18, 36],
        popupAnchor: [0, -36],
        html: `<div class="marker-icon" style="background-color: ${bgColor}">
          <i class="mdi ${iconClass}"></i>
        </div>`,
      }),
    })

    marker.on('click', () => selectPoint(point))
    const pointName = point.name || point.nom || 'Point'
    marker.bindTooltip(pointName, { direction: 'top', offset: [0, -36] })
    markersLayer!.addLayer(marker)
  })

  // Fit bounds if we have points and no main zone was set
  if (points.value.length > 0 && !hasMainZone.value) {
    const bounds = L.latLngBounds(
      points.value.map(p => [p.latitude, p.longitude])
    )
    map?.fitBounds(bounds, { padding: [50, 50] })
  }
}

async function exportData() {
  const blob = await pointsStore.exportCSV()
  if (blob) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'points_export.csv'
    a.click()
    URL.revokeObjectURL(url)
  }
}

async function generateQR() {
  if (!selectedPoint.value) return

  try {
    const blob = await qrcodesAPI.generateForPoint(selectedPoint.value.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `qr_${selectedPoint.value.nom}.png`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Erreur génération QR:', e)
  }
}

function getPhotoUrl(photo: any): string {
  if (!photo) return ''
  if (typeof photo === 'string') return photo
  // Thumbnail désactivée - on utilise toujours l'URL principale
  return photo.url || ''
}

function openPhotoInNewTab(photo: any) {
  const url = photo?.url || photo
  if (typeof url === 'string') {
    window.open(url, '_blank')
  }
}

function getPointHierarchy(point: Point): { famille: string | null, categorie: string | null, type: string | null } {
  const lexiqueCode = point.lexique_code || point.lexique_id
  if (!lexiqueCode) return { famille: null, categorie: null, type: null }

  const entry = lexiqueStore.getByCode(lexiqueCode)
  if (!entry) return { famille: null, categorie: null, type: null }

  // Remonter la hiérarchie
  const hierarchy: any[] = [entry]
  let current = entry
  while (current.parent_id) {
    const parent = lexiqueStore.getByCode(current.parent_id) || lexiqueStore.getById(current.parent_id)
    if (parent) {
      hierarchy.unshift(parent)
      current = parent
    } else {
      break
    }
  }

  return {
    famille: hierarchy.find((h: any) => h.niveau === 0)?.libelle || null,
    categorie: hierarchy.find((h: any) => h.niveau === 1)?.libelle || null,
    type: hierarchy.find((h: any) => h.niveau === 2)?.libelle || null,
  }
}

function getPointProjet(point: Point): string {
  const projetId = point.project_id || point.projet_id
  if (!projetId) return '-'
  const projet = projets.value.find((p: any) => p.id === projetId)
  return projet?.nom || projet?.name || '-'
}

function isColorValue(value: string): boolean {
  return /^#[0-9A-Fa-f]{3,8}$/.test(value)
}

function formatValue(value: any): string {
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'boolean') return value ? 'Oui' : 'Non'
  return String(value)
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

// Watch for map style changes
watch(mapStyle, (newStyle) => {
  if (!map) return
  Object.values(tileLayers).forEach(layer => map!.removeLayer(layer))
  tileLayers[newStyle as keyof typeof tileLayers].addTo(map)
})

// Watch for duplicate radius changes
watch(duplicateRadius, (radius) => {
  pointsStore.setDuplicateRadius(radius)
})

// Lifecycle
onMounted(async () => {
  initMap()
  await centerOnMainZone()
  await lexiqueStore.fetchAll()
  try {
    projets.value = await projetsAPI.getAll()
  } catch (e) {
    console.error('Erreur chargement projets:', e)
  }
  await loadPoints()
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style>
.cursor-pointer {
  cursor: pointer;
}

.carte-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
}

.map-card {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
}

.create-overlay,
.duplicate-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.custom-marker {
  background: transparent;
  border: none;
}

.marker-icon {
  width: 36px;
  height: 36px;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.4);
  border: 2px solid white;
}

.marker-icon i {
  transform: rotate(45deg);
  color: white;
  font-size: 18px;
}

.temp-marker-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #1976D2;
  border: 3px solid white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.temp-marker-icon.warning {
  background: #FFC107;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

.color-swatch {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid rgba(0,0,0,0.2);
  vertical-align: middle;
  margin-right: 6px;
}
</style>

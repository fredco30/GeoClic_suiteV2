<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDemandesStore, type StatutDemande } from '../stores/demandes'
import { useZonesStore } from '../stores/zones'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.heat'
import HelpButton from '@/components/help/HelpButton.vue'

const router = useRouter()
const demandesStore = useDemandesStore()
const zonesStore = useZonesStore()

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let markersLayer: L.LayerGroup | null = null
let heatLayer: any = null
let zonesLayer: L.GeoJSON | null = null

const heatmapMode = ref(false)

const selectedStatuts = ref<StatutDemande[]>(['nouveau', 'en_moderation', 'envoye', 'accepte', 'en_cours', 'planifie'])

const statutColors: Record<string, string> = {
  nouveau: '#3b82f6',
  en_moderation: '#f59e0b',
  envoye: '#0ea5e9',
  accepte: '#22c55e',
  en_cours: '#8b5cf6',
  planifie: '#6366f1',
  traite: '#059669',
  rejete: '#ef4444',
  cloture: '#6b7280'
}

const statutLabels: Record<string, string> = {
  nouveau: 'Nouveau',
  en_moderation: 'En modération',
  envoye: 'Envoyé au service',
  accepte: 'Accepté',
  en_cours: 'En cours',
  planifie: 'Planifié',
  traite: 'Traité',
  rejete: 'Non retenu',
  cloture: 'Clôturé'
}

// Couleurs par niveau hiérarchique
const levelColors: Record<number, string> = {
  1: '#22c55e',  // Commune - Vert
  2: '#3b82f6',  // Quartier - Bleu
  3: '#f97316'   // Secteur - Orange
}

const showZones = ref(true)

onMounted(async () => {
  initMap()
  await Promise.all([
    loadZones(),
    loadDemandes()
  ])
})

watch(selectedStatuts, () => {
  loadDemandes()
}, { deep: true })

watch(showZones, () => {
  if (zonesLayer && map) {
    if (showZones.value) {
      zonesLayer.addTo(map)
    } else {
      zonesLayer.removeFrom(map)
    }
  }
})

watch(heatmapMode, () => {
  updateMarkers()
})

function initMap() {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value).setView([46.603354, 1.888334], 6) // Centre France

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map)

  markersLayer = L.layerGroup().addTo(map)
}

async function loadZones() {
  // Charger les zones pour la légende et le GeoJSON pour l'affichage
  const [, geojson] = await Promise.all([
    zonesStore.fetchZones(),
    zonesStore.fetchZonesGeoJSON()
  ])

  if (!geojson || !map) return

  // Créer la couche GeoJSON pour les zones
  zonesLayer = L.geoJSON(geojson, {
    style: (feature) => {
      const level = feature?.properties?.level || 2
      const color = levelColors[level] || '#6b7280'
      return {
        color: color,
        weight: 2,
        opacity: 0.8,
        fillColor: color,
        fillOpacity: 0.15
      }
    },
    onEachFeature: (feature, layer) => {
      if (feature.properties?.name) {
        layer.bindTooltip(feature.properties.name, {
          permanent: false,
          direction: 'center',
          className: 'zone-tooltip'
        })
      }
    }
  })

  if (showZones.value) {
    zonesLayer.addTo(map)
  }

  // Zoom automatique sur l'emprise des zones
  const bounds = zonesLayer.getBounds()
  if (bounds.isValid()) {
    map.fitBounds(bounds, { padding: [30, 30] })
  }
}

async function loadDemandes() {
  await demandesStore.fetchDemandes({
    statut: selectedStatuts.value.length > 0 ? selectedStatuts.value : undefined
  })

  updateMarkers()
}

function updateMarkers() {
  if (!map || !markersLayer) return

  markersLayer.clearLayers()

  // Nettoyer la heatmap précédente
  if (heatLayer) {
    map.removeLayer(heatLayer)
    heatLayer = null
  }

  const demandesWithCoords = demandesStore.demandes.filter(
    d => d.latitude && d.longitude
  )

  if (demandesWithCoords.length === 0) return

  const bounds = L.latLngBounds([])
  demandesWithCoords.forEach(d => bounds.extend([d.latitude!, d.longitude!]))

  if (heatmapMode.value) {
    // Mode heatmap : carte thermique
    const prioriteWeight: Record<string, number> = {
      urgente: 1.0,
      haute: 0.8,
      normale: 0.5,
      basse: 0.3
    }

    const heatPoints = demandesWithCoords.map(d => [
      d.latitude!,
      d.longitude!,
      prioriteWeight[d.priorite] || 0.5
    ])

    heatLayer = (L as any).heatLayer(heatPoints, {
      radius: 30,
      blur: 20,
      maxZoom: 17,
      max: 1.0,
      gradient: {
        0.2: '#3b82f6',
        0.4: '#22c55e',
        0.6: '#f59e0b',
        0.8: '#f97316',
        1.0: '#ef4444'
      }
    }).addTo(map)
  } else {
    // Mode marqueurs classiques
    demandesWithCoords.forEach(demande => {
      const color = statutColors[demande.statut] || '#6b7280'

      const icon = L.divIcon({
        className: 'custom-marker',
        html: `
          <div style="
            background: ${color};
            width: 32px;
            height: 32px;
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            border: 2px solid white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <span style="transform: rotate(45deg); font-size: 14px;">
              ${demande.categorie_icone || '📌'}
            </span>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 32]
      })

      const marker = L.marker([demande.latitude!, demande.longitude!], { icon })

      marker.bindPopup(`
        <div style="min-width: 200px;">
          <div style="font-weight: 600; margin-bottom: 8px;">
            ${demande.numero_suivi}
          </div>
          <div style="
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 12px;
            background: ${color}20;
            color: ${color};
            margin-bottom: 8px;
          ">
            ${statutLabels[demande.statut]}
          </div>
          <div style="color: #6b7280; font-size: 13px; margin-bottom: 8px;">
            ${demande.categorie_nom}
          </div>
          <div style="font-size: 14px; margin-bottom: 12px;">
            ${demande.description.substring(0, 100)}${demande.description.length > 100 ? '...' : ''}
          </div>
          <button
            onclick="window.dispatchEvent(new CustomEvent('open-demande', { detail: '${demande.id}' }))"
            style="
              background: #3b82f6;
              color: white;
              border: none;
              padding: 6px 12px;
              border-radius: 6px;
              cursor: pointer;
              font-size: 13px;
            "
          >
            Voir détails
          </button>
        </div>
      `)

      markersLayer!.addLayer(marker)
    })
  }

  if (demandesWithCoords.length > 0) {
    map.fitBounds(bounds, { padding: [50, 50] })
  }
}

// Écouter les clics sur les popups
window.addEventListener('open-demande', ((e: CustomEvent) => {
  router.push(`/demandes/${e.detail}`)
}) as EventListener)

function toggleStatut(statut: StatutDemande) {
  const index = selectedStatuts.value.indexOf(statut)
  if (index > -1) {
    selectedStatuts.value.splice(index, 1)
  } else {
    selectedStatuts.value.push(statut)
  }
}
</script>

<template>
  <div class="carte-view">
    <!-- Sidebar filtres -->
    <aside class="filters-sidebar">
      <div class="sidebar-header">
        <h2>Filtres</h2>
        <HelpButton pageKey="carte" size="sm" />
      </div>

      <div class="filter-section">
        <h3>Statuts</h3>
        <div class="statut-filters">
          <label
            v-for="(label, statut) in statutLabels"
            :key="statut"
            class="statut-checkbox"
          >
            <input
              type="checkbox"
              :checked="selectedStatuts.includes(statut as StatutDemande)"
              @change="toggleStatut(statut as StatutDemande)"
            />
            <span
              class="statut-color"
              :style="{ background: statutColors[statut] }"
            ></span>
            {{ label }}
          </label>
        </div>
      </div>

      <div class="filter-section">
        <h3>Affichage</h3>
        <label class="heatmap-toggle">
          <input
            type="checkbox"
            v-model="heatmapMode"
          />
          <span class="toggle-label">Carte thermique</span>
        </label>
        <div v-if="heatmapMode" class="heatmap-legend">
          <div class="heat-gradient"></div>
          <div class="heat-labels">
            <span>Faible</span>
            <span>Fort</span>
          </div>
        </div>
      </div>

      <div class="filter-section">
        <h3>Zones</h3>
        <label class="zone-toggle">
          <input
            type="checkbox"
            v-model="showZones"
          />
          <span class="toggle-label">Afficher les zones</span>
        </label>
        <div v-if="zonesStore.zones.length > 0" class="zones-legend">
          <div class="legend-item" v-if="zonesStore.quartiers.length > 0">
            <span class="legend-color" style="background: #3b82f6;"></span>
            Quartiers ({{ zonesStore.quartiers.length }})
          </div>
          <div class="legend-item" v-if="zonesStore.secteurs.length > 0">
            <span class="legend-color" style="background: #8b5cf6;"></span>
            Secteurs ({{ zonesStore.secteurs.length }})
          </div>
          <div class="legend-item" v-if="zonesStore.communes.length > 0">
            <span class="legend-color" style="background: #22c55e;"></span>
            Communes ({{ zonesStore.communes.length }})
          </div>
        </div>
      </div>

      <div class="stats-mini">
        <p>
          <strong>{{ demandesStore.demandes.filter(d => d.latitude).length }}</strong>
          demandes affichées
        </p>
      </div>
    </aside>

    <!-- Carte -->
    <div class="map-container" ref="mapContainer"></div>
  </div>
</template>

<style scoped>
.carte-view {
  display: flex;
  height: calc(100vh - 0px);
}

.filters-sidebar {
  width: 280px;
  background: white;
  padding: 1.5rem;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.filters-sidebar h2 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.filter-section {
  margin-bottom: 1.5rem;
}

.filter-section h3 {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  margin: 0 0 0.75rem;
  text-transform: uppercase;
}

.statut-filters {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.statut-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background 0.2s;
}

.statut-checkbox:hover {
  background: #f9fafb;
}

.statut-checkbox input {
  margin: 0;
}

.statut-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.zone-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background 0.2s;
}

.zone-toggle:hover {
  background: #f9fafb;
}

.zone-toggle input {
  margin: 0;
}

.toggle-label {
  font-size: 0.9rem;
}

.zones-legend {
  margin-top: 0.75rem;
  padding-left: 1.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  opacity: 0.8;
}

.heatmap-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background 0.2s;
}

.heatmap-toggle:hover {
  background: #f9fafb;
}

.heatmap-toggle input {
  margin: 0;
}

.heatmap-legend {
  margin-top: 0.5rem;
  padding: 0.5rem;
}

.heat-gradient {
  height: 10px;
  border-radius: 5px;
  background: linear-gradient(to right, #3b82f6, #22c55e, #f59e0b, #f97316, #ef4444);
}

.heat-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 2px;
}

.stats-mini {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
  color: #6b7280;
  font-size: 0.9rem;
}

.map-container {
  flex: 1;
  height: 100%;
}

/* Custom marker styles */
:deep(.custom-marker) {
  background: transparent !important;
  border: none !important;
}

:deep(.leaflet-popup-content-wrapper) {
  border-radius: 12px;
}

:deep(.leaflet-popup-content) {
  margin: 12px 16px;
}

:deep(.zone-tooltip) {
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
</style>

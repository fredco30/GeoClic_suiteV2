<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import axios from 'axios'

const mapContainer = ref<HTMLDivElement | null>(null)
const map = ref<L.Map | null>(null)
const zonesLayer = ref<L.GeoJSON | null>(null)
const demandesLayer = ref<L.GeoJSON | null>(null)
const demandesCount = ref(0)
const loadingDemandes = ref(false)
const headerCollapsed = ref(false)
const showLegend = ref(false)

// Cleanup de la carte quand le composant est démonté
onBeforeUnmount(() => {
  if (map.value) {
    map.value.stop()
    if (demandesLayer.value) {
      map.value.removeLayer(demandesLayer.value)
      demandesLayer.value = null
    }
    if (zonesLayer.value) {
      map.value.removeLayer(zonesLayer.value)
      zonesLayer.value = null
    }
    map.value.remove()
    map.value = null
  }
})

// Couleurs des zones
const zoneColors: Record<string, { color: string; fillColor: string }> = {
  quartier: { color: '#2563eb', fillColor: '#3b82f6' },
  secteur: { color: '#7c3aed', fillColor: '#8b5cf6' },
  commune: { color: '#16a34a', fillColor: '#22c55e' }
}

// Labels des statuts
const statutLabels: Record<string, string> = {
  nouveau: 'Nouveau',
  en_moderation: 'En modération',
  envoye: 'Transmis au service',
  accepte: 'Accepté',
  en_cours: 'En cours',
  planifie: 'Planifié',
  traite: 'Traité',
  resolu: 'Résolu',
  rejete: 'Rejeté',
  cloture: 'Clôturé'
}

// Conversion des noms d'icônes Material vers emojis
const iconToEmoji: Record<string, string> = {
  park: '🌳',
  nature: '🌿',
  eco: '♻️',
  directions_car: '🚗',
  route: '🛣️',
  traffic: '🚦',
  construction: '🚧',
  warning: '⚠️',
  lightbulb: '💡',
  water_drop: '💧',
  delete: '🗑️',
  cleaning_services: '🧹',
  pets: '🐕',
  noise: '🔊',
  local_parking: '🅿️',
  dangerous: '☠️',
  report: '📋',
  help: '❓'
}

function getIconEmoji(iconName: string | null): string {
  if (!iconName) return '📍'
  return iconToEmoji[iconName] || '📍'
}

function toggleHeader() {
  headerCollapsed.value = !headerCollapsed.value
  // Redimensionner la carte après l'animation
  nextTick(() => {
    setTimeout(() => map.value?.invalidateSize(), 350)
  })
}

function toggleLegend() {
  showLegend.value = !showLegend.value
}

onMounted(async () => {
  if (!mapContainer.value) return

  const L = await import('leaflet')

  map.value = L.map(mapContainer.value, {
    zoomAnimation: true,
    fadeAnimation: true,
    markerZoomAnimation: true
  }).setView([46.603354, 1.888334], 6)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map.value)

  await Promise.all([loadZones(), loadDemandes()])
})

async function loadZones() {
  if (!map.value) return

  try {
    const L = await import('leaflet')
    const response = await axios.get('/api/zones/geojson')
    const geojson = response.data

    if (!geojson || !geojson.features?.length) return

    zonesLayer.value = L.geoJSON(geojson, {
      interactive: false,  // Permet aux clics de passer aux marqueurs
      style: (feature) => {
        const zoneType = feature?.properties?.zone_type || 'quartier'
        const colors = zoneColors[zoneType] || { color: '#6b7280', fillColor: '#9ca3af' }
        return {
          color: colors.color,
          weight: 3,
          opacity: 0.9,
          fillColor: colors.fillColor,
          fillOpacity: 0.2,
          dashArray: zoneType === 'commune' ? '10, 5' : undefined
        }
      }
    }).addTo(map.value)

    const bounds = zonesLayer.value.getBounds()
    if (bounds.isValid()) {
      map.value.fitBounds(bounds, { padding: [30, 30] })
    }
  } catch (error) {
    console.error('Erreur chargement zones:', error)
  }
}

async function loadDemandes() {
  if (!map.value) return
  loadingDemandes.value = true

  try {
    const L = await import('leaflet')
    const response = await axios.get('/api/demandes/public/carte/demandes')
    const geojson = response.data

    if (!geojson || !geojson.features?.length) {
      demandesCount.value = 0
      return
    }

    demandesCount.value = geojson.features.length

    demandesLayer.value = L.geoJSON(geojson, {
      pointToLayer: (feature, latlng) => {
        const props = feature.properties
        const color = props.statut_color || '#6b7280'
        return L.circleMarker(latlng, {
          radius: 10,
          fillColor: color,
          color: '#ffffff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.85
        })
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties
        const dateStr = props.created_at
          ? new Date(props.created_at).toLocaleDateString('fr-FR')
          : ''
        const statutLabel = statutLabels[props.statut] || props.statut

        // Photos HTML
        let photosHtml = ''
        if (props.photos && props.photos.length > 0) {
          const photosList = props.photos.slice(0, 3).map((photo: string) =>
            `<img src="${photo}" alt="Photo" style="width: 70px; height: 70px; object-fit: cover; border-radius: 6px; cursor: pointer;" onclick="window.open('${photo}', '_blank')" />`
          ).join('')
          photosHtml = `<div style="display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap;">${photosList}</div>`
        }

        const emoji = getIconEmoji(props.categorie_icone)

        layer.bindPopup(`
          <div style="min-width: 200px; max-width: 280px;">
            <div style="font-size: 1.5em; margin-bottom: 4px;">${emoji}</div>
            <strong>${props.categorie_nom}</strong><br>
            <span style="display: inline-block; padding: 2px 8px; border-radius: 12px; background: ${props.statut_color}; color: white; font-size: 0.85em; margin: 4px 0;">
              ${statutLabel}
            </span><br>
            <small style="color: #6b7280;">Signalé le ${dateStr}</small>
            ${photosHtml}
          </div>
        `, {
          closeButton: true,
          className: 'demande-popup',
          maxWidth: 300
        })

        layer.bindTooltip(`${emoji} ${props.categorie_nom}`, {
          permanent: false,
          direction: 'top',
          offset: [0, -10]
        })
      }
    }).addTo(map.value)

    if (!zonesLayer.value && demandesLayer.value) {
      const bounds = demandesLayer.value.getBounds()
      if (bounds.isValid()) {
        map.value.fitBounds(bounds, { padding: [50, 50] })
      }
    }
  } catch (error) {
    console.error('Erreur chargement demandes:', error)
  } finally {
    loadingDemandes.value = false
  }
}
</script>

<template>
  <div class="carte-page">
    <!-- Header collapsible -->
    <div :class="['carte-header', { collapsed: headerCollapsed }]" @click="toggleHeader">
      <div class="header-content">
        <h1>Carte des signalements</h1>
        <p v-if="!headerCollapsed">Visualisez les signalements en cours de traitement</p>
      </div>
      <span class="collapse-icon">{{ headerCollapsed ? '&#9660;' : '&#9650;' }}</span>
    </div>

    <!-- Carte -->
    <div class="carte-wrapper">
      <div ref="mapContainer" class="carte-container"></div>

      <!-- Badge compteur flottant -->
      <div class="floating-count" v-if="demandesCount > 0 || loadingDemandes">
        <span v-if="loadingDemandes">...</span>
        <span v-else>{{ demandesCount }}</span>
      </div>

      <!-- Bouton légende flottant -->
      <button class="legend-btn" @click.stop="toggleLegend" aria-label="Légende">
        i
      </button>

      <!-- Panneau légende -->
      <div v-if="showLegend" class="legend-panel" @click.stop>
        <div class="legend-panel-header">
          <span>Légende</span>
          <button @click="showLegend = false" class="close-btn">&times;</button>
        </div>

        <div class="legend-section">
          <h4>Statuts</h4>
          <div class="legend-grid">
            <div class="legend-item">
              <span class="legend-marker" style="background: #ef4444;"></span>
              <span>Nouveau</span>
            </div>
            <div class="legend-item">
              <span class="legend-marker" style="background: #f59e0b;"></span>
              <span>En cours</span>
            </div>
            <div class="legend-item">
              <span class="legend-marker" style="background: #3b82f6;"></span>
              <span>Planifié</span>
            </div>
            <div class="legend-item">
              <span class="legend-marker" style="background: #22c55e;"></span>
              <span>Résolu</span>
            </div>
          </div>
        </div>

        <div class="legend-section">
          <h4>Zones</h4>
          <div class="legend-grid">
            <div class="legend-item">
              <span class="legend-zone" style="border-color: #2563eb; background: rgba(59, 130, 246, 0.3)"></span>
              <span>Quartier</span>
            </div>
            <div class="legend-item">
              <span class="legend-zone" style="border-color: #7c3aed; background: rgba(139, 92, 246, 0.3)"></span>
              <span>Secteur</span>
            </div>
            <div class="legend-item">
              <span class="legend-zone dashed" style="border-color: #16a34a; background: rgba(34, 197, 94, 0.3)"></span>
              <span>Commune</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.carte-page {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

/* Header collapsible */
.carte-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.carte-header.collapsed {
  padding: 0.5rem 1rem;
}

.carte-header h1 {
  color: #1f2937;
  font-size: 1.1rem;
  margin: 0;
}

.carte-header.collapsed h1 {
  font-size: 0.95rem;
}

.carte-header p {
  color: #6b7280;
  font-size: 0.8rem;
  margin: 0.25rem 0 0 0;
}

.collapse-icon {
  color: #9ca3af;
  font-size: 0.8rem;
}

/* Wrapper carte */
.carte-wrapper {
  flex: 1;
  position: relative;
  min-height: 0;
}

.carte-container {
  width: 100%;
  height: 100%;
}

/* Badge compteur flottant */
.floating-count {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 1000;
  background: #2563eb;
  color: white;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* Bouton légende */
.legend-btn {
  position: absolute;
  bottom: 80px;
  left: 10px;
  z-index: 1000;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: white;
  border: 2px solid #e5e7eb;
  color: #2563eb;
  font-weight: 700;
  font-size: 1rem;
  font-style: italic;
  font-family: Georgia, serif;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.legend-btn:hover {
  background: #f3f4f6;
}

/* Panneau légende */
.legend-panel {
  position: absolute;
  bottom: 80px;
  left: 50px;
  z-index: 1001;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  min-width: 200px;
  max-width: 280px;
  overflow: hidden;
}

.legend-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.legend-section {
  padding: 0.75rem 1rem;
}

.legend-section:not(:last-child) {
  border-bottom: 1px solid #f3f4f6;
}

.legend-section h4 {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #374151;
}

.legend-marker {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

.legend-zone {
  width: 16px;
  height: 12px;
  border: 2px solid;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-zone.dashed {
  border-style: dashed;
}

/* Mobile */
@media (max-width: 640px) {
  .carte-page {
    height: calc(100vh - 56px);
  }

  .carte-header {
    padding: 0.5rem 0.75rem;
  }

  .carte-header h1 {
    font-size: 1rem;
  }

  .carte-header p {
    font-size: 0.75rem;
  }

  .legend-panel {
    left: 10px;
    right: 10px;
    bottom: 70px;
    max-width: none;
  }

  .legend-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

<style>
/* Style global pour les tooltips */
.zone-tooltip {
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
}
.zone-tooltip strong {
  color: #1f2937;
}
.zone-tooltip small {
  color: #6b7280;
}
</style>

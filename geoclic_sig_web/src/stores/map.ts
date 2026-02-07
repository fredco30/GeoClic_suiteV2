import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface Layer {
  id: string
  name: string
  type: 'points' | 'lines' | 'polygons'
  visible: boolean
  color: string
  data: GeoJSON.FeatureCollection | null
  projectId?: string
}

export interface Project {
  id: string
  name: string
  description?: string
  created_at: string
}

export interface ApiZone {
  id: string
  name: string
  code: string | null
  zone_type: string
  metadata: Record<string, any>
  visible: boolean
  color: string
  geojson?: GeoJSON.Geometry
  // Champs hiérarchiques
  level: number
  parent_id: string | null
  parent_name: string | null
  is_global: boolean
  project_id: string | null
  // Enfants (pour l'arbre)
  children?: ApiZone[]
  expanded?: boolean
}

// Couleurs par niveau hiérarchique
const LEVEL_COLORS: Record<number, string> = {
  1: '#22c55e',  // Commune - Vert
  2: '#3b82f6',  // Quartier - Bleu
  3: '#f97316',  // Secteur - Orange
}

// Couleurs de fallback pour les zones sans niveau
const ZONE_COLORS = [
  '#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f39c12',
  '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b'
]

// Labels pour les niveaux
export const LEVEL_LABELS: Record<number, string> = {
  1: 'Commune',
  2: 'Quartier',
  3: 'Secteur',
}

// Icônes pour les niveaux
export const LEVEL_ICONS: Record<number, string> = {
  1: '🏛️',
  2: '🏘️',
  3: '📍',
}

export const useMapStore = defineStore('map', () => {
  const layers = ref<Layer[]>([])
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const selectedFeature = ref<GeoJSON.Feature | null>(null)
  const loading = ref(false)
  const mapCenter = ref<[number, number]>([46.603354, 1.888334]) // France center
  const mapZoom = ref(6)

  // Zones API
  const apiZones = ref<ApiZone[]>([])
  const apiZonesTree = ref<ApiZone[]>([])  // Structure arborescente
  const apiZonesVisible = ref(true)
  const apiZonesLoading = ref(false)
  const apiZonesLevelFilter = ref<number | null>(null)  // Filtrer par niveau

  const visibleLayers = computed(() => layers.value.filter(l => l.visible))
  const visibleApiZones = computed(() => {
    let zones = apiZones.value.filter(z => z.visible)
    if (apiZonesLevelFilter.value !== null) {
      zones = zones.filter(z => z.level === apiZonesLevelFilter.value)
    }
    return zones
  })

  // Zones groupées par niveau
  const apiZonesByLevel = computed(() => {
    const grouped: Record<number, ApiZone[]> = { 1: [], 2: [], 3: [] }
    apiZones.value.forEach(zone => {
      const level = zone.level || 2
      if (!grouped[level]) grouped[level] = []
      grouped[level].push(zone)
    })
    return grouped
  })

  // Charger les projets
  async function loadProjects() {
    loading.value = true
    try {
      const response = await axios.get('/api/projects')
      projects.value = response.data
    } catch (error) {
      console.error('Erreur chargement projets:', error)
    } finally {
      loading.value = false
    }
  }

  // Charger les zones depuis l'API
  async function loadApiZones() {
    apiZonesLoading.value = true
    try {
      const response = await axios.get('/api/zones/geojson')
      const geojsonCollection = response.data

      // Parser les zones avec les champs hiérarchiques
      const zonesFlat: ApiZone[] = geojsonCollection.features.map((feature: any, index: number) => {
        const level = feature.properties.level || 2
        return {
          id: feature.id,
          name: feature.properties.name,
          code: feature.properties.code,
          zone_type: feature.properties.zone_type,
          metadata: feature.properties.metadata || {},
          visible: true,
          color: LEVEL_COLORS[level] || ZONE_COLORS[index % ZONE_COLORS.length],
          geojson: feature.geometry,
          // Champs hiérarchiques
          level: level,
          parent_id: feature.properties.parent_id || null,
          parent_name: feature.properties.parent_name || null,
          is_global: feature.properties.is_global || false,
          project_id: feature.properties.project_id || null,
          expanded: true,
        }
      })

      apiZones.value = zonesFlat

      // Construire l'arbre hiérarchique
      buildZonesTree(zonesFlat)
    } catch (error) {
      console.error('Erreur chargement zones API:', error)
      apiZones.value = []
      apiZonesTree.value = []
    } finally {
      apiZonesLoading.value = false
    }
  }

  // Construire l'arbre hiérarchique
  function buildZonesTree(zones: ApiZone[]) {
    const zonesById = new Map<string, ApiZone>()
    const rootZones: ApiZone[] = []

    // Indexer toutes les zones
    zones.forEach(zone => {
      zone.children = []
      zonesById.set(zone.id, zone)
    })

    // Construire l'arbre
    zones.forEach(zone => {
      if (zone.parent_id && zonesById.has(zone.parent_id)) {
        const parent = zonesById.get(zone.parent_id)!
        parent.children!.push(zone)
      } else {
        rootZones.push(zone)
      }
    })

    // Trier par nom à chaque niveau
    const sortByName = (a: ApiZone, b: ApiZone) => a.name.localeCompare(b.name)
    rootZones.sort(sortByName)
    rootZones.forEach(zone => {
      if (zone.children) zone.children.sort(sortByName)
      zone.children?.forEach(child => {
        if (child.children) child.children.sort(sortByName)
      })
    })

    apiZonesTree.value = rootZones
  }

  // Filtrer par niveau
  function setApiZonesLevelFilter(level: number | null) {
    apiZonesLevelFilter.value = level
  }

  // Toggle expansion d'une zone dans l'arbre
  function toggleZoneExpanded(zoneId: string) {
    const zone = apiZones.value.find(z => z.id === zoneId)
    if (zone) {
      zone.expanded = !zone.expanded
    }
  }

  // Rendre visible/invisible toutes les zones d'un niveau
  function toggleLevelVisibility(level: number) {
    const zonesOfLevel = apiZones.value.filter(z => z.level === level)
    const allVisible = zonesOfLevel.every(z => z.visible)
    zonesOfLevel.forEach(z => { z.visible = !allVisible })
  }

  // Toggle visibilité globale des zones API
  function toggleApiZonesVisible() {
    apiZonesVisible.value = !apiZonesVisible.value
  }

  // Toggle visibilité d'une zone spécifique
  function toggleApiZoneVisibility(zoneId: string) {
    const zone = apiZones.value.find(z => z.id === zoneId)
    if (zone) {
      zone.visible = !zone.visible
    }
  }

  // Obtenir le GeoJSON des zones visibles
  function getApiZonesGeoJSON(): GeoJSON.FeatureCollection {
    let zones = apiZones.value.filter(z => z.visible && z.geojson)

    // Appliquer le filtre de niveau si actif
    if (apiZonesLevelFilter.value !== null) {
      zones = zones.filter(z => z.level === apiZonesLevelFilter.value)
    }

    const features = zones.map(z => ({
      type: 'Feature' as const,
      id: z.id,
      properties: {
        name: z.name,
        code: z.code,
        zone_type: z.zone_type,
        color: z.color,
        level: z.level,
        parent_id: z.parent_id,
        parent_name: z.parent_name,
        is_global: z.is_global,
      },
      geometry: z.geojson!
    }))

    return {
      type: 'FeatureCollection',
      features
    }
  }

  // Calculer les bounds de toutes les zones API
  function getApiZonesBounds(): [[number, number], [number, number]] | null {
    if (apiZones.value.length === 0) return null

    let minLat = Infinity, maxLat = -Infinity
    let minLng = Infinity, maxLng = -Infinity

    apiZones.value.forEach(zone => {
      if (!zone.geojson) return

      const processCoords = (coords: any) => {
        if (typeof coords[0] === 'number') {
          // C'est une coordonnée [lng, lat]
          minLng = Math.min(minLng, coords[0])
          maxLng = Math.max(maxLng, coords[0])
          minLat = Math.min(minLat, coords[1])
          maxLat = Math.max(maxLat, coords[1])
        } else {
          // C'est un tableau de coordonnées
          coords.forEach(processCoords)
        }
      }

      if (zone.geojson.type === 'Polygon') {
        processCoords((zone.geojson as GeoJSON.Polygon).coordinates)
      } else if (zone.geojson.type === 'MultiPolygon') {
        processCoords((zone.geojson as GeoJSON.MultiPolygon).coordinates)
      }
    })

    if (minLat === Infinity) return null
    return [[minLat, minLng], [maxLat, maxLng]]
  }

  // Sélectionner un projet
  async function selectProject(project: Project) {
    currentProject.value = project
    await loadProjectData(project.id)
  }

  // Charger les données d'un projet
  async function loadProjectData(projectId: string) {
    loading.value = true
    try {
      const response = await axios.get(`/api/points?project_id=${projectId}&page_size=500`)

      // Grouper par type de géométrie
      const points: GeoJSON.Feature[] = []
      const lines: GeoJSON.Feature[] = []
      const polygons: GeoJSON.Feature[] = []

      // L'API retourne { total, page, page_size, items: [...] }
      const items = Array.isArray(response.data) ? response.data : (response.data.items || [])

      items.forEach((point: any) => {
        // Construire la géométrie GeoJSON depuis geom_type + coordinates
        let geometry: GeoJSON.Geometry | null = null
        if (point.coordinates && point.coordinates.length > 0) {
          const geomType = (point.geom_type || 'POINT').toUpperCase()
          if (geomType === 'POINT') {
            geometry = {
              type: 'Point',
              coordinates: [point.coordinates[0].longitude, point.coordinates[0].latitude]
            }
          } else if (geomType === 'LINESTRING') {
            geometry = {
              type: 'LineString',
              coordinates: point.coordinates.map((c: any) => [c.longitude, c.latitude])
            }
          } else if (geomType === 'POLYGON') {
            geometry = {
              type: 'Polygon',
              coordinates: [point.coordinates.map((c: any) => [c.longitude, c.latitude])]
            }
          }
        }

        if (!geometry) return

        const feature: GeoJSON.Feature = {
          type: 'Feature',
          geometry: geometry,
          properties: {
            id: point.id,
            name: point.name,
            type: point.type,
            subtype: point.subtype,
            lexique_code: point.lexique_code,
            condition_state: point.condition_state,
            point_status: point.point_status,
            sync_status: point.sync_status,
            comment: point.comment,
            color_value: point.color_value,
            icon_name: point.icon_name,
          }
        }

        if (geometry.type === 'Point') {
          points.push(feature)
        } else if (geometry.type === 'LineString' || geometry.type === 'MultiLineString') {
          lines.push(feature)
        } else if (geometry.type === 'Polygon' || geometry.type === 'MultiPolygon') {
          polygons.push(feature)
        }
      })

      // Créer les couches
      layers.value = [
        {
          id: 'points',
          name: 'Points',
          type: 'points',
          visible: true,
          color: '#3388ff',
          data: { type: 'FeatureCollection', features: points },
          projectId
        },
        {
          id: 'lines',
          name: 'Lignes',
          type: 'lines',
          visible: true,
          color: '#ff7800',
          data: { type: 'FeatureCollection', features: lines },
          projectId
        },
        {
          id: 'polygons',
          name: 'Polygones',
          type: 'polygons',
          visible: true,
          color: '#00ff00',
          data: { type: 'FeatureCollection', features: polygons },
          projectId
        }
      ]
    } catch (error) {
      console.error('Erreur chargement données:', error)
    } finally {
      loading.value = false
    }
  }

  // Ajouter une couche importée (méthode simple)
  function addImportedLayer(name: string, geojson: GeoJSON.FeatureCollection, type: 'points' | 'lines' | 'polygons') {
    const id = `import_${Date.now()}`
    layers.value.push({
      id,
      name,
      type,
      visible: true,
      color: '#' + Math.floor(Math.random() * 16777215).toString(16),
      data: geojson
    })
  }

  // Ajouter une couche (méthode générique)
  function addLayer(layer: Partial<Layer> & { id: string; name: string; data: GeoJSON.FeatureCollection }) {
    const newLayer: Layer = {
      id: layer.id,
      name: layer.name,
      type: layer.type || 'points',
      visible: layer.visible ?? true,
      color: layer.color || '#3388ff',
      data: layer.data,
      projectId: layer.projectId
    }
    layers.value.push(newLayer)
  }

  // Toggle visibilité couche
  function toggleLayerVisibility(layerId: string) {
    const layer = layers.value.find(l => l.id === layerId)
    if (layer) {
      layer.visible = !layer.visible
    }
  }

  // Supprimer une couche
  function removeLayer(layerId: string) {
    layers.value = layers.value.filter(l => l.id !== layerId)
  }

  // Sélectionner une feature
  function selectFeature(feature: GeoJSON.Feature | null) {
    selectedFeature.value = feature
  }

  // Centrer sur les données
  function fitToBounds(bounds: [[number, number], [number, number]]) {
    // Sera géré par le composant carte
  }

  return {
    layers,
    projects,
    currentProject,
    selectedFeature,
    loading,
    mapCenter,
    mapZoom,
    visibleLayers,
    // Zones API
    apiZones,
    apiZonesTree,
    apiZonesVisible,
    apiZonesLoading,
    apiZonesLevelFilter,
    visibleApiZones,
    apiZonesByLevel,
    loadProjects,
    selectProject,
    loadProjectData,
    addImportedLayer,
    addLayer,
    toggleLayerVisibility,
    removeLayer,
    selectFeature,
    fitToBounds,
    // Zones API functions
    loadApiZones,
    toggleApiZonesVisible,
    toggleApiZoneVisibility,
    getApiZonesGeoJSON,
    getApiZonesBounds,
    // Nouvelles fonctions hiérarchiques
    setApiZonesLevelFilter,
    toggleZoneExpanded,
    toggleLevelVisibility,
  }
})

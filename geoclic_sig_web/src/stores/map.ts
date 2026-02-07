import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface Layer {
  id: string
  name: string
  type: 'points' | 'lines' | 'polygons'
  visible: boolean
  color: string
  icon?: string  // MDI icon name (ex: "mdi-bench")
  data: GeoJSON.FeatureCollection | null
  projectId?: string
}

export interface Project {
  id: string
  name: string
  description?: string
  created_at: string
}

export interface LexiqueEntry {
  code: string
  label: string
  parent_code: string | null
  level: number
  icon_name: string | null
  color_value: number | null
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

// Couleurs de fallback pour les couches
const LAYER_COLORS = [
  '#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f39c12',
  '#1abc9c', '#e67e22', '#2980b9', '#c0392b', '#27ae60'
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

// Convertir ARGB int en couleur hex CSS
function argbToHex(argb: number): string {
  if (!argb || argb === 0) return ''
  const hex = (argb & 0x00FFFFFF).toString(16).padStart(6, '0')
  return `#${hex}`
}

export const useMapStore = defineStore('map', () => {
  const layers = ref<Layer[]>([])
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const selectedFeature = ref<GeoJSON.Feature | null>(null)
  const loading = ref(false)
  const mapCenter = ref<[number, number]>([46.603354, 1.888334]) // France center
  const mapZoom = ref(6)

  // Lexique (code → entrée)
  const lexiqueMap = ref<Map<string, LexiqueEntry>>(new Map())

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

  // Charger le lexique pour un projet et construire le mapping code → entrée
  async function loadLexique(projectId: string) {
    try {
      const response = await axios.get(`/api/lexique?project_id=${projectId}`)
      const entries: LexiqueEntry[] = response.data
      const map = new Map<string, LexiqueEntry>()
      entries.forEach((e: any) => {
        map.set(e.code, {
          code: e.code,
          label: e.label,
          parent_code: e.parent_code,
          level: e.level,
          icon_name: e.icon_name,
          color_value: e.color_value,
        })
      })
      lexiqueMap.value = map
    } catch (error) {
      console.error('Erreur chargement lexique:', error)
    }
  }

  // Remonter la hiérarchie du lexique pour trouver l'ancêtre à un niveau donné
  function getLexiqueAncestor(code: string, targetLevel: number): LexiqueEntry | null {
    let current = lexiqueMap.value.get(code)
    if (!current) return null

    // Si on est déjà au bon niveau ou en dessous
    while (current && current.level > targetLevel) {
      if (!current.parent_code) break
      const parent = lexiqueMap.value.get(current.parent_code)
      if (!parent) break
      current = parent
    }

    return current?.level === targetLevel ? current : null
  }

  // Obtenir l'icône et la couleur pour un code lexique
  // Cherche d'abord sur l'entrée elle-même, puis remonte vers les parents
  function getLexiqueDisplay(code: string): { label: string; icon: string; color: string } {
    const entry = lexiqueMap.value.get(code)
    if (!entry) return { label: code, icon: 'mdi-map-marker', color: '#3498db' }

    // Chercher l'icône : d'abord sur l'entrée, puis remonter
    let icon = entry.icon_name || ''
    let color = entry.color_value ? argbToHex(entry.color_value) : ''

    if (!icon || !color) {
      let current: LexiqueEntry | undefined = entry
      while (current?.parent_code) {
        current = lexiqueMap.value.get(current.parent_code)
        if (current) {
          if (!icon && current.icon_name) icon = current.icon_name
          if (!color && current.color_value) color = argbToHex(current.color_value)
        }
      }
    }

    return {
      label: entry.label,
      icon: icon || 'mdi-map-marker',
      color: color || '#3498db',
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
      // Charger le lexique et les points en parallèle
      const [pointsResponse] = await Promise.allSettled([
        axios.get(`/api/points?project_id=${projectId}&page_size=500`),
        loadLexique(projectId),
      ])

      if (pointsResponse.status !== 'fulfilled') {
        console.error('Erreur chargement points:', pointsResponse.reason)
        layers.value = []
        return
      }

      const response = pointsResponse.value

      // L'API retourne { total, page, page_size, items: [...] }
      const items = Array.isArray(response.data) ? response.data : (response.data.items || [])

      // Grouper les features par catégorie (level 2 du lexique)
      const categoryGroups = new Map<string, {
        features: GeoJSON.Feature[]
        label: string
        icon: string
        color: string
      }>()

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

        // Déterminer la catégorie (level 2) pour le groupement
        const lexiqueCode = point.lexique_code || ''
        let categoryCode = 'other'
        let categoryDisplay = { label: 'Autres', icon: 'mdi-map-marker', color: '#95a5a6' }

        if (lexiqueCode && lexiqueMap.value.size > 0) {
          // Chercher l'ancêtre level 2 (catégorie) pour le groupement
          let cat = getLexiqueAncestor(lexiqueCode, 2)

          // Si pas trouvé, essayer level 1 (peut-être seulement 2 niveaux)
          if (!cat) cat = getLexiqueAncestor(lexiqueCode, 1)

          // Fallback : essayer point.type comme code lexique direct
          if (!cat && point.type) {
            const typeEntry = lexiqueMap.value.get(point.type)
            if (typeEntry) cat = typeEntry
          }

          if (cat) {
            categoryCode = cat.code
            categoryDisplay = getLexiqueDisplay(cat.code)
          } else {
            // Peut-être que le point est directement au level 1 ou 2
            const direct = lexiqueMap.value.get(lexiqueCode)
            if (direct) {
              categoryCode = direct.code
              categoryDisplay = getLexiqueDisplay(direct.code)
            }
          }
        } else if (point.type) {
          // Fallback sans lexique : grouper par type brut
          categoryCode = point.type
          categoryDisplay = { label: point.type, icon: 'mdi-map-marker', color: '#3498db' }
        }

        // Résoudre les labels depuis le lexique pour l'affichage dans le détail
        const pointEntry = lexiqueCode && lexiqueMap.value.size > 0
          ? lexiqueMap.value.get(lexiqueCode)
          : null
        const pointDisplay = pointEntry
          ? getLexiqueDisplay(lexiqueCode)
          : { label: '', icon: '', color: '' }

        // Résoudre la catégorie (level 2) pour le label "Catégorie" dans le détail
        const catEntry = lexiqueCode && lexiqueMap.value.size > 0
          ? (getLexiqueAncestor(lexiqueCode, 2) || getLexiqueAncestor(lexiqueCode, 1))
          : null

        const feature: GeoJSON.Feature = {
          type: 'Feature',
          geometry: geometry,
          properties: {
            id: point.id,
            name: point.name,
            categorie: catEntry?.label || point.type || '',
            type: pointDisplay.label || point.subtype || '',
            lexique_code: point.lexique_code,
            condition_state: point.condition_state,
            point_status: point.point_status,
            sync_status: point.sync_status,
            comment: point.comment,
            color_value: point.color_value,
            icon_name: pointDisplay.icon || point.icon_name,
            photos: point.photos || [],
            // Info catégorie pour le rendu carte
            _category_icon: categoryDisplay.icon,
            _category_color: categoryDisplay.color,
          }
        }

        if (!categoryGroups.has(categoryCode)) {
          categoryGroups.set(categoryCode, {
            features: [],
            ...categoryDisplay,
          })
        }
        categoryGroups.get(categoryCode)!.features.push(feature)
      })

      // Créer une couche par catégorie
      const newLayers: Layer[] = []
      let colorIdx = 0
      categoryGroups.forEach((group, code) => {
        const geomType = group.features[0]?.geometry?.type || 'Point'
        let layerType: 'points' | 'lines' | 'polygons' = 'points'
        if (geomType === 'LineString' || geomType === 'MultiLineString') layerType = 'lines'
        if (geomType === 'Polygon' || geomType === 'MultiPolygon') layerType = 'polygons'

        newLayers.push({
          id: code,
          name: group.label,
          type: layerType,
          visible: true,
          color: group.color || LAYER_COLORS[colorIdx % LAYER_COLORS.length],
          icon: group.icon,
          data: { type: 'FeatureCollection', features: group.features },
          projectId,
        })
        colorIdx++
      })

      // Trier par nom
      newLayers.sort((a, b) => a.name.localeCompare(b.name))
      layers.value = newLayers

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
      icon: layer.icon,
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
    lexiqueMap,
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
    loadLexique,
    getLexiqueDisplay,
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

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface Zone {
  id: string
  name: string
  zone_type: string
  level: number
  parent_id: string | null
  parent_name: string | null
  is_global: boolean
  project_id: string | null
  code: string | null
  code_insee?: string
  code_iris?: string
  population?: number
  point_count: number
  properties?: Record<string, unknown>
  geometry?: GeoJSON.Geometry
  created_at: string
  updated_at?: string
}

// Labels et couleurs par niveau
export const LEVEL_LABELS: Record<number, string> = {
  1: 'Commune',
  2: 'Quartier',
  3: 'Secteur',
}

export const LEVEL_COLORS: Record<number, string> = {
  1: 'success',
  2: 'info',
  3: 'warning',
}

export const useZonesStore = defineStore('zones', () => {
  const zones = ref<Zone[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Zones par niveau
  const communes = computed(() =>
    (zones.value || []).filter(z => z.level === 1)
  )

  const quartiers = computed(() =>
    (zones.value || []).filter(z => z.level === 2)
  )

  const secteurs = computed(() =>
    (zones.value || []).filter(z => z.level === 3)
  )

  // Zones filtrées par type (compatibilité)
  const zonesByType = computed(() => {
    const grouped: Record<string, Zone[]> = {}
    for (const zone of zones.value || []) {
      const type = zone.zone_type || 'autre'
      if (!grouped[type]) grouped[type] = []
      grouped[type].push(zone)
    }
    return grouped
  })

  // Toutes les zones comme options de filtre (avec hiérarchie)
  const zonesOptions = computed(() =>
    (zones.value || []).map(z => ({
      value: z.id,
      label: z.name,
      type: z.zone_type,
      level: z.level,
      parentId: z.parent_id,
      parentName: z.parent_name
    }))
  )

  // Options de communes pour le filtre en cascade
  const communeOptions = computed(() =>
    communes.value.map(z => ({
      value: z.id,
      label: z.name
    }))
  )

  // Options de quartiers pour une commune donnée (ou tous si null)
  function getQuartierOptions(communeId: string | null) {
    let filtered = quartiers.value
    if (communeId) {
      filtered = filtered.filter(z => z.parent_id === communeId)
    }
    return filtered.map(z => ({
      value: z.id,
      label: z.name,
      parentId: z.parent_id,
      parentName: z.parent_name
    }))
  }

  // Options de secteurs pour un quartier donné (ou tous si null)
  function getSecteurOptions(quartierId: string | null) {
    let filtered = secteurs.value
    if (quartierId) {
      filtered = filtered.filter(z => z.parent_id === quartierId)
    }
    return filtered.map(z => ({
      value: z.id,
      label: z.name,
      parentId: z.parent_id,
      parentName: z.parent_name
    }))
  }

  // Obtenir les enfants directs d'une zone
  function getChildren(parentId: string): Zone[] {
    return (zones.value || []).filter(z => z.parent_id === parentId)
  }

  // Obtenir toute la hiérarchie descendante
  function getDescendants(parentId: string): Zone[] {
    const children = getChildren(parentId)
    let descendants = [...children]
    for (const child of children) {
      descendants = descendants.concat(getDescendants(child.id))
    }
    return descendants
  }

  async function fetchZones(projectId?: string) {
    loading.value = true
    error.value = null
    try {
      const params = projectId ? `?project_id=${projectId}&include_global=true` : '?include_global=true'
      const response = await axios.get(`/api/zones${params}`)
      zones.value = response.data || []
    } catch (e: any) {
      error.value = e.message || 'Erreur lors du chargement des zones'
      zones.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchZonesGeoJSON(projectId?: string) {
    loading.value = true
    error.value = null
    try {
      const params = projectId ? `?project_id=${projectId}&include_global=true` : '?include_global=true'
      const response = await axios.get(`/api/zones/geojson${params}`)
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Erreur lors du chargement du GeoJSON'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchHierarchy() {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/zones/hierarchy')
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Erreur lors du chargement de la hiérarchie'
      return null
    } finally {
      loading.value = false
    }
  }

  function getZoneById(id: string): Zone | undefined {
    return (zones.value || []).find(z => z.id === id)
  }

  function getZoneByName(name: string): Zone | undefined {
    return (zones.value || []).find(z => z.name === name)
  }

  function getLevelLabel(level: number): string {
    return LEVEL_LABELS[level] || `Niveau ${level}`
  }

  function getLevelColor(level: number): string {
    return LEVEL_COLORS[level] || 'grey'
  }

  return {
    zones,
    loading,
    error,
    communes,
    quartiers,
    secteurs,
    zonesByType,
    zonesOptions,
    communeOptions,
    getQuartierOptions,
    getSecteurOptions,
    getChildren,
    getDescendants,
    fetchZones,
    fetchZonesGeoJSON,
    fetchHierarchy,
    getZoneById,
    getZoneByName,
    getLevelLabel,
    getLevelColor
  }
})

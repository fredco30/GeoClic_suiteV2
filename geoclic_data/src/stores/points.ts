/**
 * stores/points.ts
 *
 * Store Pinia pour la gestion des points avec détection anti-doublon
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { pointsAPI } from '@/services/api'

export interface Point {
  id: string
  // Champs principaux (API format)
  name: string
  type: string
  subtype?: string | null
  lexique_code?: string | null
  project_id?: string | null
  comment?: string | null
  // Coordonnees (extraites depuis coordinates)
  latitude: number
  longitude: number
  // Etat et workflow
  condition_state?: string | null
  point_status?: string | null
  sync_status?: string
  // Donnees techniques
  custom_properties?: Record<string, any>
  photos?: any[]
  // Metadata
  created_by?: string | null
  created_at: string
  updated_at?: string | null
  // Affichage (venant du lexique)
  color_value?: number | null
  icon_name?: string | null
  // Aliases pour retrocompatibilite
  nom?: string  // alias pour name
  description?: string | null  // alias pour comment
  lexique_id?: string  // alias pour lexique_code
  projet_id?: string  // alias pour project_id
  couleur?: string | null
  icone?: string | null
  donnees_techniques?: Record<string, any>
  synced?: boolean  // pour la compatibilite
}

export interface PointCreatePayload {
  name: string
  type: string
  lexique_code?: string
  project_id?: string
  comment?: string
  coordinates: { latitude: number; longitude: number }[]
  geom_type?: string
  custom_properties?: Record<string, any>
}

export interface DuplicateCheck {
  hasDuplicate: boolean
  nearbyPoints: Point[]
  distance: number
}

export const usePointsStore = defineStore('points', () => {
  // State
  const points = ref<Point[]>([])
  const selectedPoint = ref<Point | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)

  // Filtres
  const filters = ref({
    projet_id: null as string | null,
    lexique_id: null as string | null,
    search: '',
  })

  // Pagination
  const pagination = ref({
    page: 1,
    page_size: 50,
  })

  // Rayon de détection doublon (en mètres)
  const duplicateRadius = ref(5)

  // Getters
  const filteredPoints = computed(() => {
    let result = [...points.value]

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      result = result.filter(p => {
        const name = p.name || p.nom || ''
        const comment = p.comment || p.description || ''
        return name.toLowerCase().includes(search) ||
               comment.toLowerCase().includes(search)
      })
    }

    return result
  })

  const getById = computed(() => (id: string) =>
    points.value.find(p => p.id === id)
  )

  // Actions
  async function fetchPoints(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      // Mapper les noms de paramètres frontend vers backend
      const params = {
        project_id: filters.value.projet_id || undefined,
        lexique_code: filters.value.lexique_id || undefined,
        search: filters.value.search || undefined,
        page: pagination.value.page,
        page_size: pagination.value.page_size,
      }

      const response = await pointsAPI.getAll(params)
      points.value = response.items || response
      total.value = response.total || points.value.length
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du chargement des points'
    } finally {
      loading.value = false
    }
  }

  async function fetchById(id: string): Promise<Point | null> {
    loading.value = true
    error.value = null

    try {
      const point = await pointsAPI.getById(id)
      selectedPoint.value = point
      return point
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du chargement du point'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Vérifie s'il existe un doublon à proximité
   * Retourne les points trouvés dans le rayon défini
   */
  async function checkDuplicate(lat: number, lng: number): Promise<DuplicateCheck> {
    try {
      const response = await pointsAPI.checkDuplicate(lat, lng, duplicateRadius.value)
      return {
        hasDuplicate: response.nearby_points?.length > 0,
        nearbyPoints: response.nearby_points || [],
        distance: response.min_distance || 0,
      }
    } catch (err: any) {
      console.error('Erreur vérification doublon:', err)
      return {
        hasDuplicate: false,
        nearbyPoints: [],
        distance: 0,
      }
    }
  }

  async function createPoint(data: PointCreatePayload | Partial<Point>): Promise<Point | null> {
    loading.value = true
    error.value = null

    try {
      // Extraire les coordonnées pour la vérification anti-doublon
      let lat: number | undefined
      let lng: number | undefined

      if ('coordinates' in data && data.coordinates && data.coordinates.length > 0) {
        const firstCoord = data.coordinates[0]
        if (firstCoord) {
          lat = firstCoord.latitude
          lng = firstCoord.longitude
        }
      } else if ('latitude' in data && 'longitude' in data) {
        lat = data.latitude as number
        lng = data.longitude as number
      }

      // Vérification anti-doublon avant création
      if (lat !== undefined && lng !== undefined) {
        const duplicateCheck = await checkDuplicate(lat, lng)
        if (duplicateCheck.hasDuplicate) {
          error.value = `Un point existe déjà à ${duplicateCheck.distance.toFixed(1)}m de cette position`
          return null
        }
      }

      const newPoint = await pointsAPI.create(data)
      // Transformer la réponse pour avoir latitude/longitude
      if (newPoint.coordinates?.length) {
        newPoint.latitude = newPoint.coordinates[0].latitude
        newPoint.longitude = newPoint.coordinates[0].longitude
      }
      points.value.unshift(newPoint)
      total.value++
      return newPoint
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la création'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updatePoint(id: string, data: PointCreatePayload | Partial<Point>): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      // Extraire les coordonnées pour la vérification anti-doublon
      let lat: number | undefined
      let lng: number | undefined

      if ('coordinates' in data && data.coordinates && data.coordinates.length > 0) {
        const firstCoord = data.coordinates[0]
        if (firstCoord) {
          lat = firstCoord.latitude
          lng = firstCoord.longitude
        }
      } else if ('latitude' in data && 'longitude' in data) {
        lat = data.latitude as number
        lng = data.longitude as number
      }

      // Si les coordonnées changent, vérifier les doublons
      if (lat !== undefined && lng !== undefined) {
        const existingPoint = getById.value(id)
        if (existingPoint &&
          (existingPoint.latitude !== lat || existingPoint.longitude !== lng)) {
          const duplicateCheck = await checkDuplicate(lat, lng)
          // Exclure le point lui-même de la vérification
          const realDuplicates = duplicateCheck.nearbyPoints.filter(p => p.id !== id)
          if (realDuplicates.length > 0) {
            error.value = `Un autre point existe déjà à proximité de cette position`
            return false
          }
        }
      }

      const updated = await pointsAPI.update(id, data)
      const index = points.value.findIndex(p => p.id === id)
      if (index !== -1) {
        points.value[index] = updated
      }
      if (selectedPoint.value?.id === id) {
        selectedPoint.value = updated
      }
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la mise à jour'
      return false
    } finally {
      loading.value = false
    }
  }

  async function deletePoint(id: string, force: boolean = true): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      await pointsAPI.delete(id, force)
      points.value = points.value.filter(p => p.id !== id)
      total.value--
      if (selectedPoint.value?.id === id) {
        selectedPoint.value = null
      }
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la suppression'
      return false
    } finally {
      loading.value = false
    }
  }

  async function getGeoJSON(): Promise<any> {
    try {
      return await pointsAPI.getGeoJSON({
        project_id: filters.value.projet_id || undefined,
        lexique_code: filters.value.lexique_id || undefined,
      })
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de l\'export GeoJSON'
      return null
    }
  }

  async function exportCSV(): Promise<Blob | null> {
    try {
      return await pointsAPI.exportCSV({
        project_id: filters.value.projet_id || undefined,
        lexique_code: filters.value.lexique_id || undefined,
      })
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de l\'export CSV'
      return null
    }
  }

  function setFilters(newFilters: Partial<typeof filters.value>): void {
    Object.assign(filters.value, newFilters)
    pagination.value.page = 1
  }

  function setDuplicateRadius(radius: number): void {
    duplicateRadius.value = radius
  }

  function selectPoint(point: Point | null): void {
    selectedPoint.value = point
  }

  function clearError(): void {
    error.value = null
  }

  return {
    // State
    points,
    selectedPoint,
    loading,
    error,
    total,
    filters,
    pagination,
    duplicateRadius,
    // Getters
    filteredPoints,
    getById,
    // Actions
    fetchPoints,
    fetchById,
    checkDuplicate,
    createPoint,
    updatePoint,
    deletePoint,
    getGeoJSON,
    exportCSV,
    setFilters,
    setDuplicateRadius,
    selectPoint,
    clearError,
  }
})

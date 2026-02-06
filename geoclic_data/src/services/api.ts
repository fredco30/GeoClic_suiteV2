/**
 * services/api.ts
 *
 * Service API pour communiquer avec le backend FastAPI
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios'
import router from '@/router'

// Configuration de base - détection automatique de l'URL API
// Retourne la BASE (sans /api) car axios ajoute /api au baseURL
function getApiBaseUrl(): string {
  // Si une URL est explicitement configurée, l'utiliser
  const configuredUrl = import.meta.env.VITE_API_URL
  if (configuredUrl) return configuredUrl

  // Détection automatique basée sur l'hôte actuel
  const currentHost = window.location.hostname

  // Si on accède via localhost ou 127.0.0.1 (développement local)
  if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
    return 'http://localhost:8000'
  }

  // Si on accède via un nom de domaine (production avec nginx proxy)
  // Ex: geoclic.fr, admin.geoclic.fr, etc.
  // Retourner chaîne vide car le proxy nginx redirige /api/* vers l'API
  if (currentHost.includes('.') && !currentHost.match(/^\d+\.\d+\.\d+\.\d+$/)) {
    return ''
  }

  // Si on accède via une IP (locale ou publique), utiliser la même IP pour l'API
  // Cela suppose que le port 8000 est aussi redirigé sur la box
  return `http://${currentHost}:8000`
}

const API_BASE_URL = getApiBaseUrl()

// ============================================
// FONCTIONS DE MAPPING BACKEND <-> FRONTEND
// ============================================

// Projets: backend (name, is_active, point_count) -> frontend (nom, actif, points_count)
function mapProjectFromBackend(p: any) {
  return {
    ...p,
    nom: p.name,
    actif: p.is_active,
    points_count: p.point_count,
  }
}

function mapProjectToBackend(p: any) {
  const mapped: any = { ...p }
  if (p.nom !== undefined) { mapped.name = p.nom; delete mapped.nom }
  if (p.actif !== undefined) { mapped.is_active = p.actif; delete mapped.actif }
  return mapped
}

// Lexique: backend (label, is_active, icon_name, color_value, level, parent_code, display_order)
//       -> frontend (libelle, actif, icone, couleur, niveau, parent_id, ordre)
function mapLexiqueFromBackend(l: any) {
  return {
    ...l,
    libelle: l.label,
    actif: l.is_active,
    icone: l.icon_name,
    couleur: l.color_value,
    niveau: l.level,
    parent_id: l.parent_code,
    ordre: l.display_order,
  }
}

function mapLexiqueToBackend(l: any) {
  const mapped: any = { ...l }
  if (l.libelle !== undefined) { mapped.label = l.libelle; delete mapped.libelle }
  if (l.actif !== undefined) { mapped.is_active = l.actif; delete mapped.actif }
  if (l.icone !== undefined) { mapped.icon_name = l.icone; delete mapped.icone }
  if (l.couleur !== undefined) {
    // Convert hex color string to integer for backend
    let colorValue: number | null = null
    if (typeof l.couleur === 'string' && l.couleur.startsWith('#')) {
      colorValue = parseInt(l.couleur.substring(1), 16)
    } else if (typeof l.couleur === 'number') {
      colorValue = l.couleur
    }
    mapped.color_value = colorValue
    delete mapped.couleur
  }
  if (l.niveau !== undefined) { mapped.level = l.niveau; delete mapped.niveau }
  if (l.parent_id !== undefined) { mapped.parent_code = l.parent_id; delete mapped.parent_id }
  if (l.ordre !== undefined) { mapped.display_order = l.ordre; delete mapped.ordre }
  return mapped
}

// Points: backend (name, coordinates) -> frontend (nom, latitude, longitude)
function mapPointFromBackend(p: any) {
  // Extraire latitude/longitude depuis coordinates
  const firstCoord = p.coordinates?.[0]
  return {
    ...p,
    nom: p.name,
    projet_id: p.project_id,
    lexique_id: p.lexique_code,
    description: p.comment,
    latitude: firstCoord?.latitude ?? p.latitude,
    longitude: firstCoord?.longitude ?? p.longitude,
  }
}

function mapPointToBackend(p: any) {
  const mapped: any = { ...p }
  // Renommer les champs
  if (p.nom !== undefined) { mapped.name = p.nom; delete mapped.nom }
  if (p.projet_id !== undefined) { mapped.project_id = p.projet_id; delete mapped.projet_id }
  if (p.lexique_id !== undefined) { mapped.lexique_code = p.lexique_id; delete mapped.lexique_id }
  if (p.description !== undefined) { mapped.comment = p.description; delete mapped.description }
  if (p.donnees_techniques !== undefined) { mapped.custom_properties = p.donnees_techniques; delete mapped.donnees_techniques }

  // Convertir latitude/longitude en format coordinates pour le backend
  if (p.latitude !== undefined && p.longitude !== undefined && !p.coordinates) {
    mapped.coordinates = [{ latitude: p.latitude, longitude: p.longitude }]
    delete mapped.latitude
    delete mapped.longitude
  }

  return mapped
}

// Création de l'instance Axios avec préfixe /api
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Intercepteur pour ajouter le token JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('data_auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Intercepteur pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expiré ou invalide
      localStorage.removeItem('data_auth_token')
      localStorage.removeItem('data_user')
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

// ============================================
// AUTH
// ============================================

// Mapper les données utilisateur du backend vers le frontend
function mapUserFromBackend(u: any) {
  return {
    id: u.id,
    email: u.email,
    nom: u.name || '',
    prenom: '',  // Le backend n'a pas de champ prénom séparé
    role: u.role,
    actif: u.is_active,
    created_at: u.created_at,
    last_login: u.last_login,
    permissions: u.permissions || { projets: [], categories: [] },
  }
}

export const authAPI = {
  async login(email: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    // Retourner le token + user mappé avec permissions
    return {
      access_token: response.data.access_token,
      expires_in: response.data.expires_in,
      user: mapUserFromBackend(response.data.user),
    }
  },

  async getMe() {
    const response = await api.get('/auth/me')
    return mapUserFromBackend(response.data)
  },

  async refreshToken() {
    const response = await api.post('/auth/refresh')
    return response.data
  },
}

// ============================================
// LEXIQUE (Catégories)
// ============================================

export const lexiqueAPI = {
  async getAll(projectId?: string) {
    const params = projectId ? { project_id: projectId } : {}
    const response = await api.get('/lexique', { params })
    return response.data.map(mapLexiqueFromBackend)
  },

  async getTree(projectId?: string) {
    const params = projectId ? { project_id: projectId } : {}
    const response = await api.get('/lexique/tree', { params })
    // Map recursively for tree structure
    const mapTree = (items: any[]): any[] => items.map(item => ({
      ...mapLexiqueFromBackend(item),
      children: item.children ? mapTree(item.children) : []
    }))
    return {
      ...response.data,
      roots: mapTree(response.data.roots || [])
    }
  },

  async getById(id: string, projectId?: string) {
    const params = projectId ? { project_id: projectId } : {}
    const response = await api.get(`/lexique/${id}`, { params })
    return mapLexiqueFromBackend(response.data)
  },

  async getChildren(code: string, projectId?: string) {
    const params = projectId ? { project_id: projectId } : {}
    const response = await api.get(`/lexique/${code}/children`, { params })
    return response.data.map(mapLexiqueFromBackend)
  },

  async create(data: any) {
    // project_id is required in data
    const response = await api.post('/lexique', mapLexiqueToBackend(data))
    return mapLexiqueFromBackend(response.data)
  },

  async update(id: string, data: any, projectId?: string) {
    const params = projectId ? { project_id: projectId } : {}
    const response = await api.patch(`/lexique/${id}`, mapLexiqueToBackend(data), { params })
    return mapLexiqueFromBackend(response.data)
  },

  async delete(code: string, projectId: string) {
    // project_id is required for deletion
    const response = await api.delete(`/lexique/${code}`, { params: { project_id: projectId } })
    return response.data
  },

  async canDelete(code: string, projectId: string) {
    const response = await api.get(`/lexique/${code}/can-delete`, { params: { project_id: projectId } })
    return response.data
  },

  async reorder(items: { id: string; ordre: number }[], projectId?: string) {
    // Map ordre -> display_order for backend
    const backendItems = items.map(i => ({ id: i.id, display_order: i.ordre }))
    const params = projectId ? { project_id: projectId } : {}
    const response = await api.post('/lexique/reorder', backendItems, { params })
    return response.data
  },
}

// ============================================
// CHAMPS DYNAMIQUES
// ============================================

export const champsAPI = {
  async getByLexique(lexiqueId: string) {
    const response = await api.get(`/champs/lexique/${lexiqueId}`)
    return response.data
  },

  async create(data: any) {
    const response = await api.post('/champs', data)
    return response.data
  },

  async update(id: string, data: any) {
    const response = await api.patch(`/champs/${id}`, data)
    return response.data
  },

  async delete(id: string) {
    const response = await api.delete(`/champs/${id}`)
    return response.data
  },

  async reorder(items: { id: string; ordre: number }[]) {
    const response = await api.post('/champs/reorder', items)
    return response.data
  },
}

// ============================================
// PROJETS
// ============================================

export const projetsAPI = {
  async getAll() {
    const response = await api.get('/projects')
    return response.data.map(mapProjectFromBackend)
  },

  async getById(id: string) {
    const response = await api.get(`/projects/${id}`)
    return mapProjectFromBackend(response.data)
  },

  async create(data: any) {
    const response = await api.post('/projects', mapProjectToBackend(data))
    return mapProjectFromBackend(response.data)
  },

  async update(id: string, data: any) {
    const response = await api.patch(`/projects/${id}`, mapProjectToBackend(data))
    return mapProjectFromBackend(response.data)
  },

  async delete(id: string) {
    const response = await api.delete(`/projects/${id}`)
    return response.data
  },

  async getStats(id: string) {
    const response = await api.get(`/projects/${id}/stats`)
    return response.data
  },
}

// ============================================
// UTILISATEURS
// ============================================

export const usersAPI = {
  async getAll() {
    const response = await api.get('/users')
    return response.data
  },

  async getById(id: string) {
    const response = await api.get(`/users/${id}`)
    return response.data
  },

  async create(data: any) {
    const response = await api.post('/users', data)
    return response.data
  },

  async update(id: string, data: any) {
    const response = await api.patch(`/users/${id}`, data)
    return response.data
  },

  async delete(id: string) {
    const response = await api.delete(`/users/${id}`)
    return response.data
  },

  async updatePermissions(id: string, permissions: any) {
    const response = await api.put(`/users/${id}/permissions`, permissions)
    return response.data
  },
}

// ============================================
// POINTS
// ============================================

export const pointsAPI = {
  async getAll(params?: {
    project_id?: string
    lexique_code?: string
    search?: string
    page?: number
    page_size?: number
  }) {
    const response = await api.get('/points', { params })
    return {
      ...response.data,
      items: response.data.items?.map(mapPointFromBackend) || []
    }
  },

  async getById(id: string) {
    const response = await api.get(`/points/${id}`)
    return mapPointFromBackend(response.data)
  },

  async create(data: any) {
    const response = await api.post('/points', mapPointToBackend(data))
    return mapPointFromBackend(response.data)
  },

  async update(id: string, data: any) {
    const response = await api.patch(`/points/${id}`, mapPointToBackend(data))
    return mapPointFromBackend(response.data)
  },

  async delete(id: string, force: boolean = true) {
    const response = await api.delete(`/points/${id}`, {
      params: { force },
    })
    return response.data
  },

  async checkDuplicate(lat: number, lng: number, radius: number = 5) {
    const response = await api.get('/points/check-duplicate', {
      params: { lat, lng, radius },
    })
    return response.data
  },

  async getGeoJSON(params?: {
    project_id?: string
    lexique_code?: string
    date_start?: string
    date_end?: string
  }) {
    const response = await api.get('/points/export/geojson', { params })
    return response.data
  },

  async exportCSV(params?: {
    project_id?: string
    lexique_code?: string
    date_start?: string
    date_end?: string
  }) {
    const response = await api.get('/points/export/csv', {
      params,
      responseType: 'blob',
    })
    return response.data
  },
}

// ============================================
// STATISTIQUES
// ============================================

export const statsAPI = {
  async getDashboard() {
    const response = await api.get('/stats/dashboard')
    return response.data
  },

  async getPointsByCategory() {
    const response = await api.get('/stats/points-by-category')
    return response.data
  },

  async getPointsByDate(days: number = 30) {
    const response = await api.get('/stats/points-by-date', { params: { days } })
    return response.data
  },

  async getActivityByUser() {
    const response = await api.get('/stats/activity-by-user')
    return response.data
  },
}

// ============================================
// QR CODES
// ============================================

export const qrcodesAPI = {
  async generateForPoint(pointId: string) {
    const response = await api.get(`/qrcodes/point/${pointId}`, {
      responseType: 'blob',
    })
    return response.data
  },

  async generateBatch(pointIds: string[], format: 'pdf' | 'png' = 'pdf') {
    const response = await api.post(
      '/qrcodes/batch',
      { point_ids: pointIds, format },
      { responseType: 'blob' }
    )
    return response.data
  },
}

// ============================================
// ONEGEO SUITE (OGS)
// ============================================

export const ogsAPI = {
  async getStatus() {
    const response = await api.get('/ogs/status')
    return response.data
  },

  async publish(lexiqueCode: string, includeChildren: boolean = true) {
    const response = await api.post('/ogs/publish', {
      lexique_code: lexiqueCode,
      include_children: includeChildren,
    })
    return response.data
  },

  async getTables() {
    const response = await api.get('/ogs/tables')
    return response.data
  },

  async deleteTable(tableName: string) {
    const response = await api.delete(`/ogs/tables/${tableName}`)
    return response.data
  },
}

// ============================================
// IMPORTS
// ============================================

export const importsAPI = {
  async preview(file: File) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/imports/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  async execute(
    file: File,
    projectId: string,
    lexiqueCode: string,
    mapping: Record<string, string>,
    options: {
      skipDuplicates?: boolean
      updateExisting?: boolean
      duplicateRadius?: number
    } = {}
  ) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', projectId)
    formData.append('lexique_code', lexiqueCode)
    formData.append('mapping', JSON.stringify(mapping))
    formData.append('skip_duplicates', String(options.skipDuplicates ?? true))
    formData.append('update_existing', String(options.updateExisting ?? false))
    formData.append('duplicate_radius', String(options.duplicateRadius ?? 5))

    const response = await api.post('/imports/execute', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  async downloadTemplate(format: 'csv' | 'geojson') {
    const response = await api.get(`/imports/templates/${format}`, {
      responseType: 'blob',
    })
    return response.data
  },
}

// ============================================
// POSTGIS EXTERNE
// ============================================

export const postgisAPI = {
  async getStatus() {
    const response = await api.get('/postgis/config/status')
    return response.data
  },

  async configure(config: {
    host: string
    port: number
    database: string
    username: string
    password: string
    schema_name?: string
  }) {
    const response = await api.post('/postgis/config', config)
    return response.data
  },

  async testConnection() {
    const response = await api.post('/postgis/config/test')
    return response.data
  },

  async deleteConfig() {
    const response = await api.delete('/postgis/config')
    return response.data
  },

  async getTables() {
    const response = await api.get('/postgis/tables')
    return response.data
  },

  async getTableColumns(tableName: string, schemaName: string = 'public') {
    const response = await api.get(`/postgis/tables/${tableName}/columns`, {
      params: { schema_name: schemaName },
    })
    return response.data
  },

  async previewTable(tableName: string, schemaName: string = 'public', limit: number = 10) {
    const response = await api.get(`/postgis/tables/${tableName}/preview`, {
      params: { schema_name: schemaName, limit },
    })
    return response.data
  },

  async suggestMapping(tableName: string, schemaName: string = 'public') {
    const response = await api.get(`/postgis/tables/${tableName}/suggest-mapping`, {
      params: { schema_name: schemaName },
    })
    return response.data
  },

  async importData(data: {
    table_name: string
    schema_name?: string
    project_id: string
    lexique_code: string
    mapping: Record<string, string>
    filters?: Array<{ column: string; operator: string; value?: string }>
    limit?: number
  }) {
    const response = await api.post('/postgis/import', data)
    return response.data
  },
}

export default api

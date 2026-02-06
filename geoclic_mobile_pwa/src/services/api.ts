import axios, { AxiosInstance, AxiosError } from 'axios'

// Configuration par défaut
// URL vide = utilise le proxy Vite (même origine)
const DEFAULT_SERVER_URL = ''
const STORAGE_KEY_SERVER_URL = 'geoclic_server_url'
const STORAGE_KEY_TOKEN = 'geoclic_token'
const STORAGE_KEY_USER = 'geoclic_user'

// Types
export interface User {
  id: string
  email: string
  name: string
  role: string
  permissions?: {
    projets?: string[]
    categories?: string[]
  }
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Coordinate {
  latitude: number
  longitude: number
}

export type GeometryType = 'POINT' | 'LINESTRING' | 'POLYGON'

export interface PhotoMetadata {
  id?: string
  url?: string
  filename?: string
  gps_lat?: number
  gps_lng?: number
  gps_accuracy?: number
  taken_at?: string
  localPath?: string  // Pour les photos en attente d'upload
}

export interface Point {
  id?: string
  name: string
  comment?: string
  lexique_code?: string
  project_id?: string
  type?: string
  subtype?: string
  geom_type?: GeometryType
  coordinates: Coordinate[]
  gps_precision?: number
  gps_source?: string
  altitude?: number
  sync_status?: string
  custom_properties?: Record<string, unknown>
  photos?: PhotoMetadata[]
  created_at?: string
  updated_at?: string
  // Champs locaux pour la sync
  _localId?: string
  _pendingSync?: boolean
  _pendingPhotos?: string[]
}

export interface LexiqueItem {
  code: string
  label: string
  parent_code?: string
  level: number
  icon_name?: string
  color_value?: string | number  // int ARGB depuis GET /api/lexique, string hex depuis sync
  full_path?: string
}

/**
 * Convertit color_value (int ARGB ou string hex) en string CSS hex.
 */
export function normalizeColor(color: string | number | undefined | null): string | undefined {
  if (color == null) return undefined
  if (typeof color === 'string') {
    // Déjà une string hex
    return color.startsWith('#') ? color : `#${color}`
  }
  if (typeof color === 'number') {
    // Int ARGB → hex RGB
    const r = (color >> 16) & 0xFF
    const g = (color >> 8) & 0xFF
    const b = color & 0xFF
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
  }
  return undefined
}

export interface Project {
  id: string
  name: string
  collectivite_name?: string
  status?: string
}

export interface ChampDynamique {
  id: string
  lexique_code: string  // Utilisé par le frontend
  lexique_id?: string   // Retourné par l'API (mapping vers lexique_code)
  nom: string
  type: 'text' | 'number' | 'date' | 'select' | 'multiselect' | 'photo' | 'file' | 'geometry' | 'slider' | 'color' | 'signature' | 'qrcode' | 'calculated' | 'checkbox' | string
  obligatoire: boolean
  ordre: number
  options?: string[]
  min?: number
  max?: number
  default_value?: string
  project_id?: string
  // Champs conditionnels
  condition_field?: string      // Nom du champ déclencheur
  condition_operator?: string   // Opérateur: '=', '!=', 'contains', 'not_empty'
  condition_value?: string      // Valeur attendue
}

export interface SyncRequest {
  device_id: string
  last_sync_at?: string
  points_to_upload: Point[]
}

export interface SyncResponse {
  success: boolean
  sync_id: number
  server_time: string
  points_uploaded: number
  points_to_download: Point[]
  errors: string[]
}

// Singleton API Service
class ApiService {
  private api: AxiosInstance
  private serverUrl: string

  constructor() {
    this.serverUrl = this.getStoredServerUrl()
    this.api = this.createAxiosInstance()
  }

  private getStoredServerUrl(): string {
    // 1. Vérifier si l'utilisateur a défini manuellement une URL
    const stored = localStorage.getItem(STORAGE_KEY_SERVER_URL)
    if (stored) return stored

    // 2. En production (hébergé sur geoclic.fr/mobile/), utiliser une URL vide
    //    car Nginx redirige /api vers le backend automatiquement
    //    En dev (localhost), pareil : Vite proxy gère /api
    return DEFAULT_SERVER_URL
  }

  getAutoDetectedUrl(): string {
    // Retourne l'URL effective utilisée pour les requêtes API
    if (this.serverUrl) return this.serverUrl
    return window.location.origin
  }

  private createAxiosInstance(): AxiosInstance {
    // Si serverUrl est vide, utiliser /api (proxy Vite)
    const baseURL = this.serverUrl ? `${this.serverUrl}/api` : '/api'

    const instance = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Intercepteur pour ajouter le token
    instance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem(STORAGE_KEY_TOKEN)
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Intercepteur pour gérer les erreurs
    instance.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expiré ou invalide
          this.clearAuth()
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )

    return instance
  }

  // Configuration serveur
  getServerUrl(): string {
    return this.serverUrl
  }

  setServerUrl(url: string): void {
    // Nettoyer l'URL
    let cleanUrl = url.trim()

    // Si vide, utiliser le proxy local
    if (!cleanUrl) {
      this.serverUrl = ''
      localStorage.removeItem(STORAGE_KEY_SERVER_URL)
      this.api = this.createAxiosInstance()
      return
    }

    if (cleanUrl.endsWith('/')) {
      cleanUrl = cleanUrl.slice(0, -1)
    }
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = 'https://' + cleanUrl
    }

    this.serverUrl = cleanUrl
    localStorage.setItem(STORAGE_KEY_SERVER_URL, cleanUrl)
    this.api = this.createAxiosInstance()
  }

  // Test de connexion au serveur
  async testConnection(): Promise<{ success: boolean; message: string }> {
    try {
      await this.api.get('/auth/me', { timeout: 5000 })
      return { success: true, message: 'Connexion réussie' }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED') {
          return { success: false, message: 'Timeout - serveur inaccessible' }
        }
        if (error.response?.status === 401) {
          return { success: true, message: 'Serveur accessible (non authentifié)' }
        }
        if (error.code === 'ERR_NETWORK') {
          return { success: false, message: 'Erreur réseau - vérifiez l\'URL' }
        }
      }
      return { success: false, message: 'Erreur de connexion' }
    }
  }

  // Authentification
  async login(email: string, password: string): Promise<LoginResponse> {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await this.api.post<LoginResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    // Stocker le token et l'utilisateur
    localStorage.setItem(STORAGE_KEY_TOKEN, response.data.access_token)
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(response.data.user))

    return response.data
  }

  getStoredUser(): User | null {
    const userStr = localStorage.getItem(STORAGE_KEY_USER)
    if (userStr) {
      try {
        return JSON.parse(userStr)
      } catch {
        return null
      }
    }
    return null
  }

  getStoredToken(): string | null {
    return localStorage.getItem(STORAGE_KEY_TOKEN)
  }

  clearAuth(): void {
    localStorage.removeItem(STORAGE_KEY_TOKEN)
    localStorage.removeItem(STORAGE_KEY_USER)
  }

  logout(): void {
    this.clearAuth()
  }

  // Points
  async getPoints(params?: {
    page?: number
    limit?: number
    project_id?: string
    lexique_code?: string
    search?: string
  }): Promise<{ items: Point[]; total: number; page: number; pages: number }> {
    const response = await this.api.get('/points', { params })
    return response.data
  }

  async getPoint(id: string): Promise<Point> {
    const response = await this.api.get(`/points/${id}`)
    return response.data
  }

  async createPoint(point: Partial<Point>): Promise<Point> {
    const response = await this.api.post('/points', point)
    return response.data
  }

  async updatePoint(id: string, point: Partial<Point>): Promise<Point> {
    const response = await this.api.patch(`/points/${id}`, point)
    return response.data
  }

  async deletePoint(id: string): Promise<void> {
    await this.api.delete(`/points/${id}`)
  }

  // Photos
  async uploadPhoto(
    pointId: string,
    file: Blob | File,
    metadata?: { gps_lat?: number; gps_lng?: number; gps_accuracy?: number }
  ): Promise<{ success: boolean; photo: PhotoMetadata }> {
    const formData = new FormData()
    formData.append('file', file, file instanceof File ? file.name : 'photo.jpg')
    formData.append('point_id', pointId)
    if (metadata?.gps_lat) formData.append('latitude', String(metadata.gps_lat))
    if (metadata?.gps_lng) formData.append('longitude', String(metadata.gps_lng))
    if (metadata?.gps_accuracy) formData.append('accuracy', String(metadata.gps_accuracy))

    const response = await this.api.post('/photos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  getPhotoUrl(filename: string): string {
    // Si serverUrl est vide, utiliser le chemin relatif (proxy)
    if (this.serverUrl) {
      return `${this.serverUrl}/api/photos/file/${filename}`
    }
    return `/api/photos/file/${filename}`
  }

  // Lexique
  async getLexique(): Promise<LexiqueItem[]> {
    const response = await this.api.get('/lexique')
    return Array.isArray(response.data) ? response.data : []
  }

  // Projets
  async getProjects(): Promise<Project[]> {
    const response = await this.api.get('/projects')
    return Array.isArray(response.data) ? response.data : []
  }

  // Synchronisation
  async sync(request: SyncRequest): Promise<SyncResponse> {
    const response = await this.api.post('/sync', request)
    return response.data
  }

  async getOfflinePackage(): Promise<{
    lexique_entries: LexiqueItem[]
    projects: Project[]
    champs_dynamiques: ChampDynamique[]
  }> {
    const response = await this.api.get('/sync/offline-package')
    return response.data
  }

  // Champs dynamiques par lexique code
  async getChampsByLexique(lexiqueCode: string, projectId?: string): Promise<ChampDynamique[]> {
    const params: Record<string, string> = {}
    if (projectId) {
      params.project_id = projectId
    }
    const response = await this.api.get(`/champs/lexique/${lexiqueCode}`, { params })
    return response.data
  }

}

// Export singleton
export const api = new ApiService()
export default api

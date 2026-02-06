import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface DemandeCreate {
  categorie_id: string
  description: string
  declarant_email: string
  declarant_telephone?: string
  declarant_nom?: string
  declarant_langue?: string
  coordonnees?: {
    latitude: number
    longitude: number
  }
  adresse_approximative?: string
  equipement_id?: string
  photos?: string[]
  champs_supplementaires?: Record<string, unknown>
  source?: 'web' | 'mobile' | 'qr_code'
}

export interface DemandeResponse {
  numero_suivi: string
  statut: string
  categorie_nom: string
  description: string
  created_at: string
  message: string
}

export interface DemandeDetail {
  numero_suivi: string
  statut: string
  categorie_nom: string
  description: string
  adresse_approximative?: string
  created_at: string
  updated_at: string
  date_prise_en_charge?: string
  date_planification?: string
  date_resolution?: string
  historique?: HistoriqueEntry[]
}

export interface HistoriqueEntry {
  id: string
  action: string
  ancien_statut?: string
  nouveau_statut?: string
  commentaire?: string
  created_at: string
}

export interface Category {
  id: string
  nom: string
  description?: string
  icone?: string
  couleur?: string
  parent_id?: string
  photo_obligatoire?: boolean
  photo_max_count?: number
  champs_config?: ChampConfig[]
}

export interface ChampConfig {
  nom: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'checkbox' | 'number' | 'date'
  obligatoire: boolean
  options?: string[]
}

export interface Equipement {
  id: string
  nom: string
  type_nom: string
  adresse?: string
  coordonnees?: {
    latitude: number
    longitude: number
  }
}

export interface Project {
  id: string
  name: string
  description?: string
  collectivite_name?: string
}

export interface DoublonPotentiel {
  id: string
  numero_suivi: string
  description: string
  statut: string
  distance_metres: number
  created_at: string
  declarant_email: string
  photos: string[]
  score_similarite: number
}

export interface DoublonCheckResponse {
  doublons_trouves: number
  doublons: DoublonPotentiel[]
  message: string
}

export const api = {
  // Projets SIG (non-système)
  async getProjects(): Promise<Project[]> {
    const response = await apiClient.get('/sig/projects')
    // L'API retourne { projects: [...], total: N }
    return response.data.projects || []
  },

  // Récupérer le projet système "Signalements Citoyens"
  async getSystemProject(): Promise<Project | null> {
    try {
      const response = await apiClient.get('/sig/projects', {
        params: { include_system: true }
      })
      const projects = response.data.projects || []
      return projects.find((p: any) => p.is_system) || null
    } catch {
      return null
    }
  },

  // Catégories
  async getCategories(projectId: string): Promise<Category[]> {
    const response = await apiClient.get(`/demandes/categories`, {
      params: { project_id: projectId },
    })
    return response.data
  },

  // Catégories sans filtre project_id (fallback)
  async getCategoriesAll(): Promise<Category[]> {
    const response = await apiClient.get(`/demandes/categories`)
    return response.data
  },

  // Créer une demande
  async createDemande(projectId: string, demande: DemandeCreate): Promise<DemandeResponse> {
    const response = await apiClient.post(`/demandes/public/demandes`, demande, {
      params: { project_id: projectId },
    })
    return response.data
  },

  // Suivre une demande
  async getDemande(numeroSuivi: string, email: string): Promise<DemandeDetail> {
    const response = await apiClient.get(`/demandes/public/demandes/${numeroSuivi}`, {
      params: { email },
    })
    return response.data
  },

  // Récupérer un équipement par ID (scan QR)
  async getEquipement(projectId: string, equipementId: string): Promise<Equipement> {
    const response = await apiClient.get(`/public/equipements/${equipementId}`, {
      params: { project_id: projectId },
    })
    return response.data
  },

  // Upload photo (public endpoint, resize to 720x576 max)
  async uploadPhoto(file: File): Promise<string> {
    const formData = new FormData()
    formData.append('file', file)
    // Supprimer le Content-Type par défaut pour que axios détecte automatiquement multipart/form-data
    const response = await apiClient.post('/demandes/public/photos/upload', formData, {
      headers: {
        'Content-Type': undefined,
      },
    })
    return response.data.url
  },

  // Géocoding inverse (coordonnées -> adresse)
  // Note: User-Agent ne peut pas être défini dans le navigateur (CORS security)
  async reverseGeocode(lat: number, lng: number): Promise<string> {
    try {
      const response = await axios.get(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
      )
      return response.data.display_name || ''
    } catch {
      return ''
    }
  },

  // Vérification des doublons avant soumission
  async checkDoublons(
    projectId: string,
    categorieId: string,
    latitude: number,
    longitude: number,
    rayonMetres: number = 50,
    jours: number = 30
  ): Promise<DoublonCheckResponse> {
    const response = await apiClient.post(`/demandes/public/doublons/check`, {
      categorie_id: categorieId,
      latitude,
      longitude,
      rayon_metres: rayonMetres,
      jours,
    }, {
      params: { project_id: projectId },
    })
    return response.data
  },
}

export default api

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface Demande {
  id: string
  project_id?: string
  numero_suivi: string
  categorie_id: string
  categorie_nom: string
  categorie_icone?: string
  categorie_parent_nom?: string
  description: string
  statut: StatutDemande
  priorite: 'basse' | 'normale' | 'haute' | 'urgente'
  declarant_email: string
  declarant_nom?: string
  declarant_telephone?: string
  latitude?: number
  longitude?: number
  adresse?: string
  quartier_id?: string
  quartier_nom?: string
  equipement_id?: string
  equipement_nom?: string
  service_assigne_id?: string
  service_assigne_nom?: string
  service_assigne_couleur?: string
  agent_assigne_id?: string
  agent_assigne_nom?: string
  agent_service_id?: string
  agent_service_nom?: string
  date_planification?: string
  date_resolution?: string
  created_at: string
  updated_at: string
  photos: Photo[]
  documents?: string[]
  commentaires_count: number
  messages_non_lus?: number
}

// Photo peut être une string (URL) ou un objet complet
export type Photo = string | {
  id?: string
  url: string
  thumbnail_url?: string
  uploaded_at?: string
}

export type StatutDemande =
  | 'nouveau'
  | 'en_moderation'
  | 'envoye'
  | 'accepte'
  | 'rejete'
  | 'en_cours'
  | 'planifie'
  | 'traite'
  | 'cloture'

export interface DemandeFilters {
  statut?: StatutDemande | StatutDemande[]
  categorie_id?: string
  quartier_id?: string
  agent_id?: string
  priorite?: string
  date_debut?: string
  date_fin?: string
  search?: string
}

export interface HistoriqueEntry {
  id: string
  action: string
  ancien_statut?: string
  nouveau_statut?: string
  commentaire?: string
  agent_nom?: string
  created_at: string
}

export const useDemandesStore = defineStore('demandes', () => {
  const demandes = ref<Demande[]>([])
  const currentDemande = ref<Demande | null>(null)
  const historique = ref<HistoriqueEntry[]>([])
  const loading = ref(false)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const filters = ref<DemandeFilters>({})

  // Compteurs par statut
  const countNouvelles = computed(() =>
    (demandes.value || []).filter(d => d.statut === 'nouveau').length
  )

  const countEnModeration = computed(() =>
    (demandes.value || []).filter(d => d.statut === 'en_moderation').length
  )

  const countEnvoye = computed(() =>
    (demandes.value || []).filter(d => d.statut === 'envoye').length
  )

  const countEnCours = computed(() =>
    (demandes.value || []).filter(d => ['accepte', 'envoye', 'en_cours', 'planifie'].includes(d.statut)).length
  )

  async function fetchDemandes(newFilters?: DemandeFilters) {
    loading.value = true
    if (newFilters) {
      filters.value = newFilters
      page.value = 1
    }

    try {
      const params = new URLSearchParams()
      params.append('page', page.value.toString())
      params.append('page_size', pageSize.value.toString())

      Object.entries(filters.value).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v))
          } else {
            params.append(key, value.toString())
          }
        }
      })

      const response = await axios.get(`/api/demandes?${params}`)
      // L'API retourne { demandes: [...], total: N }
      demandes.value = response.data?.demandes || response.data?.items || []
      total.value = response.data?.total || 0
    } finally {
      loading.value = false
    }
  }

  async function fetchDemande(id: string) {
    loading.value = true
    try {
      const [demandeRes, historiqueRes] = await Promise.allSettled([
        axios.get(`/api/demandes/${id}`),
        axios.get(`/api/demandes/${id}/historique`)
      ])
      if (demandeRes.status === 'fulfilled') {
        currentDemande.value = demandeRes.value.data
      }
      if (historiqueRes.status === 'fulfilled') {
        historique.value = historiqueRes.value.data
      } else {
        historique.value = []
        console.warn('Erreur chargement historique:', historiqueRes.reason)
      }
    } finally {
      loading.value = false
    }
  }

  async function updateStatut(
    id: string,
    statut: StatutDemande,
    commentaire?: string
  ) {
    const response = await axios.patch(`/api/demandes/${id}/statut`, {
      statut,
      commentaire
    })

    // Mettre à jour la demande dans la liste
    const index = demandes.value.findIndex(d => d.id === id)
    if (index !== -1) {
      demandes.value[index] = response.data
    }
    if (currentDemande.value?.id === id) {
      currentDemande.value = response.data
    }

    return response.data
  }

  async function assignerAgent(id: string, agentId: string) {
    const response = await axios.patch(`/api/demandes/${id}/assigner`, {
      agent_id: agentId
    })

    if (currentDemande.value?.id === id) {
      currentDemande.value = response.data
    }

    return response.data
  }

  async function planifier(id: string, date: string, commentaire?: string) {
    const response = await axios.patch(`/api/demandes/${id}/planifier`, {
      date_planification: date,
      commentaire
    })

    if (currentDemande.value?.id === id) {
      currentDemande.value = response.data
    }

    return response.data
  }

  async function updatePriorite(id: string, priorite: 'basse' | 'normale' | 'haute' | 'urgente') {
    const response = await axios.patch(`/api/demandes/${id}/priorite`, {
      priorite
    })

    // Mettre à jour la demande dans la liste
    const index = demandes.value.findIndex(d => d.id === id)
    if (index !== -1) {
      demandes.value[index] = response.data
    }
    if (currentDemande.value?.id === id) {
      currentDemande.value = response.data
    }

    return response.data
  }

  async function addCommentaire(id: string, contenu: string, interne: boolean = false) {
    const response = await axios.post(`/api/demandes/${id}/commentaires`, {
      contenu,
      interne
    })

    // Recharger l'historique
    const historiqueRes = await axios.get(`/api/demandes/${id}/historique`)
    historique.value = historiqueRes.data

    return response.data
  }

  async function getStatistiques(periode?: string) {
    const params = periode ? `?periode=${periode}` : ''
    const response = await axios.get(`/api/demandes/statistiques${params}`)
    return response.data
  }

  function setPage(newPage: number) {
    page.value = newPage
    fetchDemandes()
  }

  return {
    demandes,
    currentDemande,
    historique,
    loading,
    total,
    page,
    pageSize,
    filters,
    countNouvelles,
    countEnModeration,
    countEnvoye,
    countEnCours,
    fetchDemandes,
    fetchDemande,
    updateStatut,
    assignerAgent,
    planifier,
    updatePriorite,
    addCommentaire,
    getStatistiques,
    setPage
  }
})

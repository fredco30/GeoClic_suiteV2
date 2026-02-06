import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export interface DemandeListItem {
  id: string
  numero: string | null
  description: string
  statut: string
  priorite: string
  created_at: string
  updated_at: string | null
  categorie_id: string | null
  categorie_nom: string | null
  categorie_icone: string | null
  categorie_couleur: string | null
  adresse: string | null
  quartier_nom: string | null
  latitude: number | null
  longitude: number | null
  agent_service_id: string | null
  agent_service_nom: string | null
  has_photos: boolean
  photo_count: number
  unread_messages: number
}

export interface DemandeDetail extends DemandeListItem {
  declarant_prenom: string | null
  declarant_initial_nom: string | null
  declarant_email_masque: string | null
  date_prise_en_charge: string | null
  date_resolution: string | null
  commentaire_interne: string | null
  photos: string[]
  photos_intervention: string[]
}

export interface Message {
  id: string
  demande_id: string
  sender_type: 'service' | 'demandes'
  sender_id: string | null
  sender_nom: string | null
  message: string
  lu_par_service: boolean
  lu_par_demandes: boolean
  created_at: string
}

const API_BASE = '/api/services'

export const useDemandesStore = defineStore('demandes', () => {
  const demandes = ref<DemandeListItem[]>([])
  const currentDemande = ref<DemandeDetail | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Charger la liste des demandes (uniquement celles assignées à l'agent connecté)
  async function loadDemandes(filters: {
    statut?: string
    priorite?: string
    search?: string
  } = {}) {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      // Toujours filtrer par mes demandes pour la PWA Terrain
      params.append('my_demandes', 'true')
      if (filters.statut) params.append('statut', filters.statut)
      if (filters.priorite) params.append('priorite', filters.priorite)
      if (filters.search) params.append('search', filters.search)

      const response = await axios.get(`${API_BASE}/demandes?${params}`)
      demandes.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du chargement'
    } finally {
      loading.value = false
    }
  }

  // Charger une demande
  async function loadDemande(id: string) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${API_BASE}/demandes/${id}`)
      currentDemande.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du chargement'
    } finally {
      loading.value = false
    }
  }

  // Changer le statut
  async function updateStatut(id: string, statut: string) {
    loading.value = true
    error.value = null

    try {
      await axios.put(`${API_BASE}/demandes/${id}/statut`, { statut })

      // Recharger la demande
      if (currentDemande.value?.id === id) {
        await loadDemande(id)
      }

      // Mettre à jour dans la liste
      const index = demandes.value.findIndex(d => d.id === id)
      if (index !== -1) {
        demandes.value[index].statut = statut
      }

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la mise à jour'
      return false
    } finally {
      loading.value = false
    }
  }

  // Assigner un agent
  async function assignAgent(demandeId: string, agentId: string | null) {
    loading.value = true
    error.value = null

    try {
      await axios.put(`${API_BASE}/demandes/${demandeId}/agent`, {
        agent_service_id: agentId
      })

      // Recharger
      if (currentDemande.value?.id === demandeId) {
        await loadDemande(demandeId)
      }

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de l\'assignation'
      return false
    } finally {
      loading.value = false
    }
  }

  // Charger les messages (canal terrain pour la PWA)
  async function loadMessages(demandeId: string) {
    try {
      const response = await axios.get(`${API_BASE}/demandes/${demandeId}/messages`, {
        params: { canal: 'terrain' }
      })
      messages.value = response.data
    } catch (err: any) {
      console.error('Erreur chargement messages:', err)
    }
  }

  // Envoyer un message (source=terrain pour identifier que ça vient de la PWA)
  async function sendMessage(demandeId: string, message: string) {
    try {
      const response = await axios.post(
        `${API_BASE}/demandes/${demandeId}/messages`,
        { message },
        { params: { canal: 'terrain', source: 'terrain' } }
      )
      messages.value.push(response.data)
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de l\'envoi'
      return false
    }
  }

  // Marquer les messages comme lus (canal terrain)
  async function markMessagesRead(demandeId: string) {
    try {
      await axios.put(`${API_BASE}/demandes/${demandeId}/messages/read`, null, {
        params: { canal: 'terrain' }
      })
      // Mettre à jour localement
      messages.value.forEach(m => {
        if (m.sender_type === 'service') {
          m.lu_par_service = true
        }
      })
    } catch {
      // Ignorer
    }
  }

  // Upload une photo d'intervention
  async function uploadPhoto(demandeId: string, file: File): Promise<string | null> {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(
        `${API_BASE}/demandes/${demandeId}/photos`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )

      // Mettre à jour localement
      if (currentDemande.value?.id === demandeId) {
        if (!currentDemande.value.photos_intervention) {
          currentDemande.value.photos_intervention = []
        }
        currentDemande.value.photos_intervention.push(response.data.url)
      }

      return response.data.url
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de l\'upload'
      return null
    }
  }

  return {
    demandes,
    currentDemande,
    messages,
    loading,
    error,
    loadDemandes,
    loadDemande,
    updateStatut,
    assignAgent,
    loadMessages,
    sendMessage,
    markMessagesRead,
    uploadPhoto
  }
})

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
  date_planification: string | null
  date_resolution: string | null
  commentaire_interne: string | null
  photos: string[]
  photos_intervention: string[]
}

export interface Message {
  id: string
  demande_id: string
  sender_type: 'service' | 'demandes' | 'terrain'
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
  const messagesTerrain = ref<Message[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Charger la liste des demandes
  async function loadDemandes(filters: {
    statut?: string
    priorite?: string
    agent_service_id?: string
    search?: string
  } = {}) {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (filters.statut) params.append('statut', filters.statut)
      if (filters.priorite) params.append('priorite', filters.priorite)
      if (filters.agent_service_id) params.append('agent_service_id', filters.agent_service_id)
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
  async function updateStatut(
    id: string,
    statut: string,
    commentaire?: string,
    date_planification?: string
  ) {
    loading.value = true
    error.value = null

    try {
      const data: { statut: string; commentaire?: string; date_planification?: string } = { statut }
      if (commentaire) data.commentaire = commentaire
      if (date_planification) data.date_planification = date_planification

      await axios.put(`${API_BASE}/demandes/${id}/statut`, data)

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

  // Charger les messages (backoffice par défaut)
  async function loadMessages(demandeId: string, canal: string = 'backoffice') {
    try {
      const response = await axios.get(`${API_BASE}/demandes/${demandeId}/messages`, {
        params: { canal }
      })
      if (canal === 'terrain') {
        messagesTerrain.value = response.data
      } else {
        messages.value = response.data
      }
    } catch (err: any) {
      console.error('Erreur chargement messages:', err)
    }
  }

  // Envoyer un message
  async function sendMessage(demandeId: string, message: string, canal: string = 'backoffice') {
    try {
      const response = await axios.post(
        `${API_BASE}/demandes/${demandeId}/messages`,
        { message },
        { params: { canal, source: 'service' } }
      )
      if (canal === 'terrain') {
        messagesTerrain.value.push(response.data)
      } else {
        messages.value.push(response.data)
      }
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de l\'envoi'
      return false
    }
  }

  // Marquer les messages comme lus
  async function markMessagesRead(demandeId: string, canal: string = 'backoffice') {
    try {
      await axios.put(`${API_BASE}/demandes/${demandeId}/messages/read`, null, {
        params: { canal }
      })
      // Mettre à jour localement
      const msgArray = canal === 'terrain' ? messagesTerrain.value : messages.value
      const senderFilter = canal === 'terrain' ? 'terrain' : 'demandes'
      msgArray.forEach(m => {
        if (m.sender_type === senderFilter) {
          m.lu_par_service = true
        }
      })
    } catch {
      // Ignorer
    }
  }

  return {
    demandes,
    currentDemande,
    messages,
    messagesTerrain,
    loading,
    error,
    loadDemandes,
    loadDemande,
    updateStatut,
    assignAgent,
    loadMessages,
    sendMessage,
    markMessagesRead
  }
})

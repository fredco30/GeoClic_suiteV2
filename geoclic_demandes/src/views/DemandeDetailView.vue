<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDemandesStore, type StatutDemande } from '../stores/demandes'
import { useAuthStore } from '../stores/auth'
import HelpButton from '@/components/help/HelpButton.vue'
import MiniMap from '@/components/MiniMap.vue'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const demandesStore = useDemandesStore()
const authStore = useAuthStore()

// Conversion noms Material Icons → emojis
const iconToEmoji: Record<string, string> = {
  park: '🌳', nature: '🌿', eco: '♻️',
  directions_car: '🚗', route: '🛣️', traffic: '🚦',
  construction: '🚧', warning: '⚠️', lightbulb: '💡',
  water_drop: '💧', delete: '🗑️', cleaning_services: '🧹',
  pets: '🐕', noise: '🔊', local_parking: '🅿️',
  dangerous: '☠️', report: '📋', help: '❓',
  home: '🏠', business: '🏢', school: '🏫',
  sports: '⚽', pool: '🏊', fitness_center: '💪',
  child_care: '👶', elderly: '👴', accessibility: '♿',
  security: '🔒', camera: '📷', speed: '🏎️',
}
function getIconEmoji(iconName: string | null | undefined): string {
  if (!iconName) return '📌'
  return iconToEmoji[iconName] || '📌'
}

const showStatusModal = ref(false)
const showAssignModal = ref(false)
const showPlanModal = ref(false)
const showDoublonModal = ref(false)
const showServiceModal = ref(false)
const showPrioriteModal = ref(false)

const newStatut = ref<StatutDemande>('accepte')
const commentaire = ref('')
const datePlanification = ref('')

// Doublons
const doublonsPotentiels = ref<any[]>([])
const doublonsLies = ref<any[]>([])
const doublonsLoading = ref(false)
const selectedDoublonId = ref('')
const doublonSuccess = ref(false)

// Services
interface Service {
  id: string
  nom: string
  code: string
  couleur: string
  icone: string
}
const services = ref<Service[]>([])
const selectedServiceId = ref('')
const serviceLoading = ref(false)

// Priorité
type Priorite = 'basse' | 'normale' | 'haute' | 'urgente'
const selectedPriorite = ref<Priorite>('normale')
const prioriteLoading = ref(false)

// Envoi email photos
const sendingPhotosEmail = ref(false)
const photosEmailSent = ref(false)
const priorites = [
  { value: 'urgente' as Priorite, label: 'Urgente', class: 'priority-urgente' },
  { value: 'haute' as Priorite, label: 'Haute', class: 'priority-haute' },
  { value: 'normale' as Priorite, label: 'Normale', class: 'priority-normale' },
  { value: 'basse' as Priorite, label: 'Basse', class: 'priority-basse' }
]

// Tchat
interface Message {
  id: string
  demande_id: string
  sender_type: 'service' | 'demandes'
  sender_id: string | null
  sender_nom: string
  message: string
  lu_par_service: boolean
  lu_par_demandes: boolean
  created_at: string
}
const messages = ref<Message[]>([])
const newMessage = ref('')
const messagesLoading = ref(false)
const sendingMessage = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
let pollingInterval: ReturnType<typeof setInterval> | null = null

// Palette de couleurs pour les intervenants
const senderColors = [
  { bg: '#dbeafe', text: '#1e40af', name: '#1e3a8a' },  // Bleu
  { bg: '#dcfce7', text: '#166534', name: '#14532d' },  // Vert
  { bg: '#fef3c7', text: '#92400e', name: '#78350f' },  // Ambre
  { bg: '#fce7f3', text: '#9d174d', name: '#831843' },  // Rose
  { bg: '#e0e7ff', text: '#4338ca', name: '#3730a3' },  // Indigo
  { bg: '#ccfbf1', text: '#0f766e', name: '#134e4a' },  // Teal
  { bg: '#fee2e2', text: '#b91c1c', name: '#991b1b' },  // Rouge
  { bg: '#f3e8ff', text: '#7c3aed', name: '#6b21a8' },  // Violet
]

const senderColorMap = new Map<string, typeof senderColors[0]>()

function getSenderColor(senderId: string | null, senderNom: string) {
  const key = senderId || senderNom || 'unknown'
  if (!senderColorMap.has(key)) {
    let hash = 0
    for (let i = 0; i < key.length; i++) {
      hash = ((hash << 5) - hash) + key.charCodeAt(i)
      hash = hash & hash
    }
    const index = Math.abs(hash) % senderColors.length
    senderColorMap.set(key, senderColors[index])
  }
  return senderColorMap.get(key)!
}

const demande = computed(() => demandesStore.currentDemande)
const historique = computed(() => demandesStore.historique)

// Normaliser les photos (API peut retourner string[] ou Photo[])
const normalizedPhotos = computed(() => {
  if (!demande.value?.photos) return []
  return demande.value.photos.map((photo: string | { id?: string; url?: string; thumbnail_url?: string }, index: number) => {
    if (typeof photo === 'string') {
      // C'est une URL directe
      return { id: `photo-${index}`, url: photo, thumbnail_url: photo }
    }
    // C'est déjà un objet Photo
    return photo
  })
})

const agents = ref<any[]>([])
const selectedAgentId = ref('')

const statutsDisponibles = computed(() => {
  if (!demande.value) return []

  const current = demande.value.statut
  const transitions: Record<string, StatutDemande[]> = {
    nouveau: ['en_moderation', 'accepte', 'rejete'],
    en_moderation: ['accepte', 'rejete'],
    accepte: ['en_cours', 'planifie', 'cloture'],
    en_cours: ['planifie', 'traite', 'cloture'],
    planifie: ['en_cours', 'traite', 'cloture'],
    traite: ['cloture'],
    rejete: ['nouveau'],
    cloture: []
  }

  return transitions[current] || []
})

onMounted(async () => {
  const id = route.params.id as string
  await demandesStore.fetchDemande(id)
  // Charger les doublons, services et messages (après que la demande soit chargée)
  await loadDoublons()
  await loadServices()
  await loadMessages()
  startPolling()
})

async function loadServices() {
  // Récupérer le project_id depuis la demande chargée
  if (!demande.value?.project_id) return

  try {
    const response = await axios.get('/api/demandes/services', {
      params: { project_id: demande.value.project_id, actif_only: true }
    })
    services.value = response.data
  } catch (error) {
    console.error('Erreur chargement services:', error)
  }
}

function openServiceModal() {
  selectedServiceId.value = demande.value?.service_assigne_id || ''
  showServiceModal.value = true
}

async function changeService() {
  if (!demande.value || !selectedServiceId.value) return

  serviceLoading.value = true
  try {
    await axios.post(
      `/api/demandes/services/${selectedServiceId.value}/assign-demande/${demande.value.id}`
    )
    showServiceModal.value = false
    // Recharger la demande pour avoir le service à jour
    await demandesStore.fetchDemande(demande.value.id)
  } catch (error) {
    console.error('Erreur changement service:', error)
  } finally {
    serviceLoading.value = false
  }
}

function openPrioriteModal() {
  selectedPriorite.value = (demande.value?.priorite as Priorite) || 'normale'
  showPrioriteModal.value = true
}

async function changePriorite() {
  if (!demande.value) return

  prioriteLoading.value = true
  try {
    await demandesStore.updatePriorite(demande.value.id, selectedPriorite.value)
    showPrioriteModal.value = false
  } catch (error) {
    console.error('Erreur changement priorité:', error)
  } finally {
    prioriteLoading.value = false
  }
}

async function envoyerPhotosEmail() {
  if (!demande.value) return

  sendingPhotosEmail.value = true
  photosEmailSent.value = false

  try {
    const response = await axios.post(`/api/demandes/${demande.value.id}/envoyer-email-photos`)
    if (response.data.success) {
      photosEmailSent.value = true
      // Masquer le message après 5 secondes
      setTimeout(() => {
        photosEmailSent.value = false
      }, 5000)
    }
  } catch (error: any) {
    console.error('Erreur envoi email:', error)
    alert(error.response?.data?.detail || 'Erreur lors de l\'envoi de l\'email')
  } finally {
    sendingPhotosEmail.value = false
  }
}

async function loadDoublons() {
  const id = route.params.id as string
  doublonsLoading.value = true

  try {
    // Charger les doublons potentiels
    const potentielsResponse = await fetch(`/api/demandes/${id}/doublons`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('demandes_auth_token')}`
      }
    })
    if (potentielsResponse.ok) {
      doublonsPotentiels.value = await potentielsResponse.json()
    }

    // Charger les doublons liés (demandes qui sont des doublons de celle-ci)
    const liesResponse = await fetch(`/api/demandes/${id}/doublons-lies`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('demandes_auth_token')}`
      }
    })
    if (liesResponse.ok) {
      doublonsLies.value = await liesResponse.json()
    }
  } catch (error) {
    console.error('Erreur chargement doublons:', error)
  } finally {
    doublonsLoading.value = false
  }
}

async function marquerDoublon() {
  if (!demande.value || !selectedDoublonId.value) return

  try {
    const response = await fetch(`/api/demandes/${demande.value.id}/marquer-doublon`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('demandes_auth_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        doublon_de_id: selectedDoublonId.value,
        commentaire: commentaire.value || 'Marqué comme doublon'
      })
    })

    if (response.ok) {
      showDoublonModal.value = false
      selectedDoublonId.value = ''
      commentaire.value = ''
      doublonSuccess.value = true

      // Rediriger vers la liste après 2 secondes
      setTimeout(() => {
        router.push('/demandes')
      }, 2000)
    }
  } catch (error) {
    console.error('Erreur marquage doublon:', error)
  }
}

async function dissocierDoublon() {
  if (!demande.value) return

  if (!confirm('Êtes-vous sûr de vouloir dissocier ce doublon ? La demande sera réouverte.')) {
    return
  }

  try {
    const response = await fetch(`/api/demandes/${demande.value.id}/dissocier-doublon`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('demandes_auth_token')}`
      }
    })

    if (response.ok) {
      await demandesStore.fetchDemande(demande.value.id)
    }
  } catch (error) {
    console.error('Erreur dissociation doublon:', error)
  }
}

async function changeStatut() {
  if (!demande.value) return

  try {
    await demandesStore.updateStatut(
      demande.value.id,
      newStatut.value,
      commentaire.value || undefined
    )
    showStatusModal.value = false
    commentaire.value = ''

    // Recharger pour avoir l'historique à jour
    await demandesStore.fetchDemande(demande.value.id)
  } catch (error) {
    console.error('Erreur changement statut:', error)
  }
}

async function assignerAgent() {
  if (!demande.value || !selectedAgentId.value) return

  try {
    await demandesStore.assignerAgent(demande.value.id, selectedAgentId.value)
    showAssignModal.value = false
  } catch (error) {
    console.error('Erreur assignation:', error)
  }
}

async function planifier() {
  if (!demande.value || !datePlanification.value) return

  try {
    await demandesStore.planifier(
      demande.value.id,
      datePlanification.value,
      commentaire.value || undefined
    )
    showPlanModal.value = false
    commentaire.value = ''
    datePlanification.value = ''
  } catch (error) {
    console.error('Erreur planification:', error)
  }
}

function getStatutClass(statut: string): string {
  const classes: Record<string, string> = {
    nouveau: 'status-nouveau',
    en_moderation: 'status-moderation',
    envoye: 'status-envoye',
    accepte: 'status-accepte',
    en_cours: 'status-encours',
    planifie: 'status-planifie',
    traite: 'status-traite',
    rejete: 'status-rejete',
    cloture: 'status-cloture'
  }
  return classes[statut] || ''
}

function getStatutLabel(statut: string): string {
  const labels: Record<string, string> = {
    nouveau: 'Nouveau',
    en_moderation: 'En modération',
    envoye: 'Envoyé au service',
    accepte: 'Accepté',
    en_cours: 'En cours',
    planifie: 'Planifié',
    traite: 'Traité',
    rejete: 'Non retenu',
    cloture: 'Clôturé'
  }
  return labels[statut] || statut
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatShortDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ========== TCHAT ==========
async function loadMessages() {
  if (!demande.value) return

  try {
    const response = await axios.get(`/api/demandes/${demande.value.id}/messages`)
    messages.value = response.data

    // Marquer comme lus les messages du service (si non lus)
    const unreadFromService = messages.value.filter(m => m.sender_type === 'service' && !m.lu_par_demandes)
    if (unreadFromService.length > 0) {
      await markMessagesAsRead()
    }

    // Scroll to bottom
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Erreur chargement messages:', error)
  }
}

async function sendMessage() {
  if (!demande.value || !newMessage.value.trim()) return

  sendingMessage.value = true
  try {
    await axios.post(`/api/demandes/${demande.value.id}/messages`, {
      message: newMessage.value.trim()
    })
    newMessage.value = ''
    await loadMessages()
  } catch (error) {
    console.error('Erreur envoi message:', error)
  } finally {
    sendingMessage.value = false
  }
}

async function markMessagesAsRead() {
  if (!demande.value) return

  try {
    await axios.put(`/api/demandes/${demande.value.id}/messages/marquer-lu`)
  } catch (error) {
    console.error('Erreur marquage lu:', error)
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function formatMessageTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  if (isToday) {
    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function startPolling() {
  // Polling toutes les 30 secondes
  pollingInterval = setInterval(() => {
    loadMessages()
  }, 30000)
}

function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

// Computed pour messages non lus du service
const unreadServiceMessages = computed(() => {
  return messages.value.filter(m => m.sender_type === 'service' && !m.lu_par_demandes).length
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="demande-detail" v-if="demande">
    <!-- Message de succès doublon -->
    <div v-if="doublonSuccess" class="success-banner">
      <span class="success-icon">&#10003;</span>
      Demande marquée comme doublon avec succès. Redirection en cours...
    </div>

    <!-- Header -->
    <header class="detail-header">
      <button class="back-btn" @click="router.back()">
        &#8592; Retour
      </button>

      <div class="header-content">
        <div class="header-main">
          <h1>{{ demande.numero_suivi }} <HelpButton page-key="demandeDetail" size="sm" /></h1>
          <span :class="['statut-badge', getStatutClass(demande.statut)]">
            {{ getStatutLabel(demande.statut) }}
          </span>
        </div>
        <p class="header-meta">
          Créée le {{ formatDate(demande.created_at) }}
        </p>
      </div>

      <div class="header-actions">
        <HelpButton pageKey="demandeDetail" size="sm" />
        <router-link
          :to="`/demandes/${demande.id}/modifier`"
          class="btn btn-edit"
        >
          &#9998; Modifier
        </router-link>
        <button
          v-if="statutsDisponibles.length > 0"
          class="btn btn-primary"
          @click="showStatusModal = true"
        >
          Changer statut
        </button>
        <button
          v-if="authStore.canAssign"
          class="btn btn-secondary"
          @click="openServiceModal"
        >
          Assigner au service
        </button>
        <button
          v-if="['accepte', 'en_cours'].includes(demande.statut)"
          class="btn btn-secondary"
          @click="showPlanModal = true"
        >
          Planifier
        </button>
      </div>
    </header>

    <div class="detail-content">
      <!-- Colonne principale -->
      <div class="main-column">
        <!-- Description -->
        <section class="card">
          <h2>
            <span class="section-icon">{{ getIconEmoji(demande.categorie_icone) }}</span>
            {{ demande.categorie_nom }}
          </h2>
          <p class="description">{{ demande.description }}</p>

          <!-- Photos -->
          <div v-if="normalizedPhotos.length > 0" class="photos-grid">
            <a
              v-for="photo in normalizedPhotos"
              :key="photo.id"
              :href="photo.url"
              target="_blank"
              class="photo-link"
            >
              <img
                :src="photo.thumbnail_url || photo.url"
                :alt="'Photo'"
                class="photo-thumbnail"
              />
            </a>
          </div>

          <!-- Documents joints -->
          <div v-if="demande.documents && demande.documents.length > 0" class="documents-section">
            <h3 class="documents-title">Documents joints</h3>
            <div class="documents-list">
              <a
                v-for="(doc, index) in demande.documents"
                :key="'doc-' + index"
                :href="doc"
                target="_blank"
                class="document-link"
              >
                <span class="document-icon">&#128196;</span>
                <span class="document-name">{{ doc.split('/').pop() }}</span>
              </a>
            </div>
          </div>
        </section>

        <!-- Photos d'intervention -->
        <section v-if="demande.photos_intervention && demande.photos_intervention.length > 0" class="card card-intervention">
          <div class="intervention-header">
            <h2>
              <span class="intervention-icon">&#10003;</span>
              Photos d'intervention
            </h2>
            <button
              class="btn btn-email-photos"
              @click="envoyerPhotosEmail"
              :disabled="sendingPhotosEmail"
            >
              <span v-if="sendingPhotosEmail">Envoi...</span>
              <span v-else>&#9993; Envoyer au citoyen</span>
            </button>
          </div>
          <p class="intervention-hint">Photos prises par l'agent terrain après intervention</p>
          <div class="photos-grid">
            <a
              v-for="(photo, index) in demande.photos_intervention"
              :key="'intervention-' + index"
              :href="photo"
              target="_blank"
              class="photo-link intervention-photo"
            >
              <img
                :src="photo"
                :alt="`Photo intervention ${index + 1}`"
                class="photo-thumbnail"
              />
            </a>
          </div>
          <p v-if="photosEmailSent" class="email-success">&#10003; Email envoyé avec succès !</p>
        </section>

        <!-- Localisation -->
        <section class="card">
          <h2>&#128205; Localisation</h2>
          <div class="location-info">
            <p v-if="demande.adresse">{{ demande.adresse }}</p>
            <p v-if="demande.quartier_nom" class="quartier">
              Quartier: {{ demande.quartier_nom }}
            </p>
            <p v-if="demande.equipement_nom" class="equipement">
              Équipement: {{ demande.equipement_nom }}
            </p>
            <div v-if="demande.latitude && demande.longitude" class="coords">
              <small>{{ demande.latitude.toFixed(6) }}, {{ demande.longitude.toFixed(6) }}</small>
            </div>
          </div>
          <!-- Carte -->
          <MiniMap
            v-if="demande.latitude && demande.longitude"
            :latitude="demande.latitude"
            :longitude="demande.longitude"
          />
        </section>

        <!-- Historique -->
        <section class="card">
          <h2>&#128197; Historique</h2>
          <div class="timeline">
            <div
              v-for="entry in historique"
              :key="entry.id"
              class="timeline-item"
            >
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-header">
                  <span class="timeline-action">
                    {{ entry.action === 'creation' ? 'Création' :
                       entry.action === 'changement_statut' ? `Statut → ${getStatutLabel(entry.nouveau_statut || '')}` :
                       entry.action }}
                  </span>
                  <span class="timeline-date">{{ formatShortDate(entry.created_at) }}</span>
                </div>
                <p v-if="entry.commentaire" class="timeline-comment">
                  {{ entry.commentaire }}
                </p>
                <span v-if="entry.agent_nom" class="timeline-agent">
                  par {{ entry.agent_nom }}
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Colonne latérale -->
      <aside class="side-column">
        <!-- Déclarant -->
        <section class="card">
          <h3>&#128100; Déclarant</h3>
          <div class="info-row">
            <span class="label">Email</span>
            <a :href="`mailto:${demande.declarant_email}`">{{ demande.declarant_email }}</a>
          </div>
          <div v-if="demande.declarant_nom" class="info-row">
            <span class="label">Nom</span>
            <span>{{ demande.declarant_nom }}</span>
          </div>
          <div v-if="demande.declarant_telephone" class="info-row">
            <span class="label">Téléphone</span>
            <a :href="`tel:${demande.declarant_telephone}`">{{ demande.declarant_telephone }}</a>
          </div>
        </section>

        <!-- Traitement -->
        <section class="card">
          <h3>&#9881; Traitement</h3>
          <div class="info-row priorite-row">
            <span class="label">Priorité</span>
            <div class="priorite-value">
              <span class="priorite-badge" :class="`priority-${demande.priorite}`">
                {{ demande.priorite }}
              </span>
              <button
                class="btn-change-priorite"
                @click="openPrioriteModal"
                title="Modifier la priorité"
              >
                Modifier
              </button>
            </div>
          </div>
          <div class="info-row service-row">
            <span class="label">Service</span>
            <div class="service-value">
              <span
                v-if="demande.service_assigne_nom"
                class="service-badge"
                :style="{ backgroundColor: demande.service_assigne_couleur || '#3b82f6' }"
              >
                {{ demande.service_assigne_nom }}
              </span>
              <span v-else class="not-assigned">Non assigné</span>
              <button
                class="btn-change-service"
                @click="openServiceModal"
                title="Modifier le service"
              >
                Modifier
              </button>
            </div>
          </div>
          <div class="info-row">
            <span class="label">Agent terrain</span>
            <span>{{ demande.agent_service_nom || 'Non assigné' }}</span>
          </div>
          <div v-if="demande.date_planification" class="info-row">
            <span class="label">Intervention</span>
            <span>{{ formatShortDate(demande.date_planification) }}</span>
          </div>
          <div v-if="demande.date_resolution" class="info-row">
            <span class="label">Résolu le</span>
            <span>{{ formatShortDate(demande.date_resolution) }}</span>
          </div>
        </section>

        <!-- Doublons potentiels -->
        <section v-if="doublonsPotentiels.length > 0" class="card doublons-section">
          <h3>&#9888; Doublons potentiels</h3>
          <p class="doublons-info">{{ doublonsPotentiels.length }} demande(s) similaire(s) à proximité</p>
          <div class="doublons-list">
            <div
              v-for="doublon in doublonsPotentiels"
              :key="doublon.id"
              class="doublon-item"
              @click="router.push(`/demandes/${doublon.id}`)"
            >
              <div class="doublon-header">
                <span class="doublon-numero">{{ doublon.numero_suivi }}</span>
                <span class="doublon-distance">{{ Math.round(doublon.distance_metres) }}m</span>
              </div>
              <p class="doublon-desc">{{ doublon.description }}</p>
              <div class="doublon-footer">
                <span :class="['doublon-statut', doublon.statut]">{{ doublon.statut }}</span>
                <span class="doublon-score">{{ doublon.score_similarite }}%</span>
              </div>
            </div>
          </div>
          <button
            class="btn btn-warning btn-block"
            @click="showDoublonModal = true"
          >
            Marquer comme doublon
          </button>
        </section>

        <!-- Doublons liés (cette demande est l'originale) -->
        <section v-if="doublonsLies.length > 0" class="card doublons-section">
          <h3>&#128279; Doublons liés</h3>
          <p class="doublons-info">{{ doublonsLies.length }} demande(s) marquée(s) comme doublon de celle-ci</p>
          <div class="doublons-list">
            <div
              v-for="doublon in doublonsLies"
              :key="doublon.id"
              class="doublon-item"
              @click="router.push(`/demandes/${doublon.id}`)"
            >
              <div class="doublon-header">
                <span class="doublon-numero">{{ doublon.numero_suivi }}</span>
              </div>
              <p class="doublon-desc">{{ doublon.description }}</p>
            </div>
          </div>
        </section>

        <!-- Indicateur si cette demande est un doublon -->
        <section v-if="demande.est_doublon" class="card doublon-alert">
          <h3>&#128274; Doublon</h3>
          <p>Cette demande a été marquée comme doublon.</p>
          <button class="btn btn-secondary btn-block" @click="dissocierDoublon">
            Dissocier ce doublon
          </button>
        </section>
      </aside>

      <!-- Colonne Tchat -->
      <aside class="chat-column">
        <div class="chat-container">
          <div class="chat-header">
            <h3>&#128172; Service terrain</h3>
            <span v-if="demande.service_assigne_nom" class="chat-service-badge" :style="{ backgroundColor: demande.service_assigne_couleur || '#3b82f6' }">
              {{ demande.service_assigne_nom }}
            </span>
            <span v-else class="chat-no-service">Aucun service</span>
          </div>

          <div ref="messagesContainer" class="messages-container">
            <div v-if="messages.length === 0" class="no-messages">
              <span class="no-messages-icon">&#128172;</span>
              <p>Aucun message</p>
              <small>Les messages avec le service terrain apparaîtront ici</small>
            </div>

            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="['message', msg.sender_type === 'demandes' ? 'message-sent' : 'message-received']"
              :style="msg.sender_type !== 'demandes' ? {
                backgroundColor: getSenderColor(msg.sender_id, msg.sender_nom).bg,
                color: getSenderColor(msg.sender_id, msg.sender_nom).text
              } : {}"
            >
              <div class="message-header">
                <span
                  class="message-sender"
                  :style="msg.sender_type !== 'demandes' ? {
                    color: getSenderColor(msg.sender_id, msg.sender_nom).name
                  } : {}"
                >{{ msg.sender_nom }}</span>
                <span class="message-time">{{ formatMessageTime(msg.created_at) }}</span>
              </div>
              <div class="message-content">{{ msg.message }}</div>
            </div>
          </div>

          <div class="chat-input-container">
            <textarea
              v-model="newMessage"
              placeholder="Écrire un message..."
              rows="2"
              @keydown.enter.exact.prevent="sendMessage"
              :disabled="sendingMessage"
            ></textarea>
            <button
              class="btn-send"
              @click="sendMessage"
              :disabled="!newMessage.trim() || sendingMessage"
            >
              <span v-if="sendingMessage" class="sending-spinner"></span>
              <span v-else>&#10148;</span>
            </button>
          </div>

          <div class="chat-footer">
            <small>Entrée pour envoyer</small>
          </div>
        </div>
      </aside>
    </div>

    <!-- Modal Changement Statut -->
    <div v-if="showStatusModal" class="modal-overlay" @click.self="showStatusModal = false">
      <div class="modal">
        <h3>Changer le statut</h3>
        <div class="form-group">
          <label>Nouveau statut</label>
          <select v-model="newStatut">
            <option v-for="s in statutsDisponibles" :key="s" :value="s">
              {{ getStatutLabel(s) }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>Commentaire (optionnel)</label>
          <textarea v-model="commentaire" rows="3" placeholder="Motif du changement..."></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showStatusModal = false">Annuler</button>
          <button class="btn btn-primary" @click="changeStatut">Confirmer</button>
        </div>
      </div>
    </div>

    <!-- Modal Planification -->
    <div v-if="showPlanModal" class="modal-overlay" @click.self="showPlanModal = false">
      <div class="modal">
        <h3>Planifier l'intervention</h3>
        <div class="form-group">
          <label>Date d'intervention</label>
          <input type="datetime-local" v-model="datePlanification" />
        </div>
        <div class="form-group">
          <label>Commentaire (optionnel)</label>
          <textarea v-model="commentaire" rows="3" placeholder="Détails de l'intervention..."></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showPlanModal = false">Annuler</button>
          <button class="btn btn-primary" @click="planifier">Planifier</button>
        </div>
      </div>
    </div>

    <!-- Modal Marquer comme doublon -->
    <div v-if="showDoublonModal" class="modal-overlay" @click.self="showDoublonModal = false">
      <div class="modal">
        <h3>Marquer comme doublon</h3>
        <p class="modal-info">Cette demande sera clôturée et liée à la demande originale.</p>
        <div class="form-group">
          <label>Demande originale</label>
          <select v-model="selectedDoublonId">
            <option value="">-- Sélectionner --</option>
            <option v-for="d in doublonsPotentiels" :key="d.id" :value="d.id">
              {{ d.numero_suivi }} - {{ d.description.substring(0, 50) }}...
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>Commentaire (optionnel)</label>
          <textarea v-model="commentaire" rows="2" placeholder="Raison du marquage..."></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showDoublonModal = false">Annuler</button>
          <button
            class="btn btn-warning"
            :disabled="!selectedDoublonId"
            @click="marquerDoublon"
          >
            Marquer comme doublon
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Changer Service -->
    <div v-if="showServiceModal" class="modal-overlay" @click.self="showServiceModal = false">
      <div class="modal">
        <h3>&#127970; Assigner à un service</h3>
        <div class="form-group">
          <label>Service</label>
          <select v-model="selectedServiceId">
            <option value="">-- Aucun service --</option>
            <option v-for="s in services" :key="s.id" :value="s.id">
              {{ s.nom }} ({{ s.code }})
            </option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showServiceModal = false">Annuler</button>
          <button
            class="btn btn-primary"
            :disabled="serviceLoading"
            @click="changeService"
          >
            {{ serviceLoading ? 'En cours...' : 'Assigner' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Changer Priorité -->
    <div v-if="showPrioriteModal" class="modal-overlay" @click.self="showPrioriteModal = false">
      <div class="modal">
        <h3>&#9888; Changer la priorité</h3>
        <div class="form-group">
          <label>Priorité</label>
          <div class="priorite-options">
            <label
              v-for="p in priorites"
              :key="p.value"
              class="priorite-option"
              :class="{ selected: selectedPriorite === p.value }"
            >
              <input
                type="radio"
                :value="p.value"
                v-model="selectedPriorite"
                name="priorite"
              />
              <span class="priorite-badge" :class="p.class">{{ p.label }}</span>
            </label>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showPrioriteModal = false">Annuler</button>
          <button
            class="btn btn-primary"
            :disabled="prioriteLoading"
            @click="changePriorite"
          >
            {{ prioriteLoading ? 'En cours...' : 'Confirmer' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Loading -->
  <div v-else-if="demandesStore.loading" class="loading">
    <div class="spinner"></div>
  </div>
</template>

<style scoped>
.demande-detail {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.back-btn {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  font-size: 0.95rem;
  padding: 0.5rem 0;
}

.back-btn:hover {
  color: #3b82f6;
}

.header-content {
  flex: 1;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-main h1 {
  font-size: 1.5rem;
  font-family: monospace;
  margin: 0;
}

.header-meta {
  color: #6b7280;
  margin: 0.5rem 0 0;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-edit {
  background: #f59e0b;
  color: white;
  text-decoration: none;
}

.btn-edit:hover {
  background: #d97706;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: white;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

/* Content Layout */
.detail-content {
  display: grid;
  grid-template-columns: 1fr 320px 340px;
  gap: 1.5rem;
}

@media (max-width: 1200px) {
  .detail-content {
    grid-template-columns: 1fr 320px;
  }
  .chat-column {
    grid-column: 1 / -1;
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .detail-content {
    grid-template-columns: 1fr;
  }
}

.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.card h2, .card h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-icon {
  font-size: 1.25rem;
}

.description {
  color: #374151;
  line-height: 1.6;
  margin: 0;
}

/* Photos */
.photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.documents-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.documents-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.5rem 0;
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.document-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #3b82f6;
  text-decoration: none;
  font-size: 0.85rem;
  transition: background 0.2s;
}

.document-link:hover {
  background: #eff6ff;
}

.document-icon {
  font-size: 1.25rem;
}

.document-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.photo-thumbnail {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
}

/* Location */
.location-info p {
  margin: 0.5rem 0;
}

.quartier, .equipement {
  color: #6b7280;
  font-size: 0.9rem;
}

.coords {
  color: #9ca3af;
}

.map-placeholder {
  height: 200px;
  background: #f3f4f6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  margin-top: 1rem;
}

/* Timeline */
.timeline {
  position: relative;
  padding-left: 1.5rem;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e5e7eb;
}

.timeline-item {
  position: relative;
  padding-bottom: 1.5rem;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-dot {
  position: absolute;
  left: -1.5rem;
  top: 4px;
  width: 12px;
  height: 12px;
  background: #3b82f6;
  border-radius: 50%;
  border: 2px solid white;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.timeline-action {
  font-weight: 500;
}

.timeline-date {
  color: #9ca3af;
  font-size: 0.8rem;
}

.timeline-comment {
  color: #6b7280;
  font-size: 0.9rem;
  margin: 0.25rem 0;
}

.timeline-agent {
  color: #9ca3af;
  font-size: 0.8rem;
}

/* Side column */
.info-row {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  color: #6b7280;
}

.info-row a {
  color: #3b82f6;
  text-decoration: none;
}

/* Status & Priority badges */
.statut-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-nouveau { background: #dbeafe; color: #1d4ed8; }
.status-moderation { background: #fef3c7; color: #b45309; }
.status-envoye { background: #e0f2fe; color: #0369a1; }
.status-accepte { background: #dcfce7; color: #15803d; }
.status-encours { background: #ede9fe; color: #7c3aed; }
.status-planifie { background: #e0e7ff; color: #4338ca; }
.status-traite { background: #d1fae5; color: #047857; }
.status-rejete { background: #fee2e2; color: #dc2626; }
.status-cloture { background: #f3f4f6; color: #6b7280; }

.priorite-badge {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.priority-urgente { background: #fee2e2; color: #dc2626; }
.priority-haute { background: #ffedd5; color: #c2410c; }
.priority-normale { background: #f3f4f6; color: #6b7280; }
.priority-basse { background: #f0fdf4; color: #166534; }

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  width: 100%;
  max-width: 400px;
  margin: 1rem;
}

.modal h3 {
  margin: 0 0 1.5rem;
  font-size: 1.125rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
}

.form-group select,
.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.95rem;
}

.form-group select:focus,
.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

/* Loading */
.loading {
  display: flex;
  justify-content: center;
  padding: 4rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Doublons */
.doublons-section {
  border-left: 4px solid #f59e0b;
}

.doublons-info {
  color: #92400e;
  font-size: 0.85rem;
  margin: 0 0 1rem 0;
}

.doublons-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.doublon-item {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.doublon-item:hover {
  background: #fef3c7;
  border-color: #f59e0b;
}

.doublon-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.doublon-numero {
  font-weight: 600;
  font-family: monospace;
  color: #1f2937;
}

.doublon-distance {
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.doublon-desc {
  font-size: 0.85rem;
  color: #4b5563;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.doublon-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
}

.doublon-statut {
  font-size: 0.7rem;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  text-transform: capitalize;
}

.doublon-statut.nouveau { background: #dbeafe; color: #1d4ed8; }
.doublon-statut.en_cours { background: #ede9fe; color: #7c3aed; }
.doublon-statut.traite { background: #d1fae5; color: #047857; }

.doublon-score {
  background: #dc2626;
  color: white;
  font-weight: 600;
  font-size: 0.7rem;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.doublon-alert {
  background: #fef2f2;
  border-left: 4px solid #dc2626;
}

.doublon-alert h3 {
  color: #dc2626;
}

.doublon-alert p {
  color: #991b1b;
  font-size: 0.9rem;
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-warning:hover {
  background: #d97706;
}

.btn-warning:disabled {
  background: #fcd34d;
  cursor: not-allowed;
}

.btn-block {
  width: 100%;
  text-align: center;
}

.modal-info {
  color: #6b7280;
  font-size: 0.9rem;
  margin: 0 0 1rem 0;
}

.success-banner {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
  animation: slideIn 0.3s ease-out;
}

.success-icon {
  font-size: 1.5rem;
  font-weight: bold;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Service styles */
.service-row {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}

.service-value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}

.service-badge {
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
}

.not-assigned {
  color: #9ca3af;
  font-style: italic;
}

.btn-change-service {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0.25rem 0.75rem;
  cursor: pointer;
  font-size: 0.8rem;
  color: #374151;
  transition: all 0.2s;
  margin-left: auto;
}

.btn-change-service:hover {
  background: #e5e7eb;
  border-color: #3b82f6;
  color: #3b82f6;
}

/* Priorité row */
.priorite-row {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}

.priorite-value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}

.btn-change-priorite {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0.25rem 0.75rem;
  cursor: pointer;
  font-size: 0.8rem;
  color: #4b5563;
  transition: all 0.2s;
  margin-left: auto;
}

.btn-change-priorite:hover {
  background: #e5e7eb;
  border-color: #3b82f6;
  color: #3b82f6;
}

/* Modal priorité */
.priorite-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.priorite-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.priorite-option:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.priorite-option.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.priorite-option input[type="radio"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

/* ========== TCHAT STYLES ========== */
.chat-column {
  position: sticky;
  top: 1.5rem;
  height: fit-content;
  max-height: calc(100vh - 180px);
}

.chat-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 500px;
  max-height: calc(100vh - 200px);
}

.chat-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.chat-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chat-service-badge {
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.chat-no-service {
  color: #9ca3af;
  font-size: 0.8rem;
  font-style: italic;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-height: 300px;
}

.no-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  text-align: center;
  padding: 2rem;
}

.no-messages-icon {
  font-size: 3rem;
  opacity: 0.3;
  margin-bottom: 0.5rem;
}

.no-messages p {
  margin: 0;
  font-weight: 500;
}

.no-messages small {
  margin-top: 0.25rem;
  font-size: 0.8rem;
}

.message {
  max-width: 85%;
  padding: 0.625rem 0.875rem;
  border-radius: 12px;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-sent {
  background: #3b82f6;
  color: white;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
}

.message-received {
  background: #f3f4f6;
  color: #1f2937;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
  font-size: 0.7rem;
}

.message-sent .message-header {
  color: rgba(255, 255, 255, 0.8);
}

.message-received .message-header {
  color: #6b7280;
}

.message-sender {
  font-weight: 600;
}

.message-time {
  opacity: 0.8;
}

.message-content {
  font-size: 0.9rem;
  line-height: 1.4;
  word-break: break-word;
  white-space: pre-wrap;
}

.chat-input-container {
  padding: 0.75rem 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
  background: #fafafa;
}

.chat-input-container textarea {
  flex: 1;
  padding: 0.625rem 0.875rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  resize: none;
  font-size: 0.9rem;
  font-family: inherit;
  line-height: 1.4;
}

.chat-input-container textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.chat-input-container textarea:disabled {
  background: #f3f4f6;
}

.btn-send {
  width: 44px;
  height: 44px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  transition: all 0.2s;
  flex-shrink: 0;
}

.btn-send:hover:not(:disabled) {
  background: #2563eb;
  transform: scale(1.05);
}

.btn-send:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.sending-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.chat-footer {
  padding: 0.5rem 1rem;
  text-align: center;
  color: #9ca3af;
  font-size: 0.75rem;
  border-top: 1px solid #f3f4f6;
}

/* Photos d'intervention */
.card-intervention {
  border-left: 4px solid #10b981;
  background: linear-gradient(to right, #f0fdf4, white);
}

.card-intervention h2 {
  color: #059669;
}

.intervention-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #10b981;
  color: white;
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: bold;
}

.intervention-hint {
  color: #6b7280;
  font-size: 0.85rem;
  margin: 0 0 1rem 0;
}

.intervention-photo {
  border: 2px solid #10b981;
  border-radius: 10px;
  overflow: hidden;
}

.intervention-photo:hover {
  border-color: #059669;
  transform: scale(1.02);
  transition: all 0.2s;
}

.intervention-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.intervention-header h2 {
  margin: 0;
}

.btn-email-photos {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.btn-email-photos:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669, #047857);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.btn-email-photos:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.email-success {
  color: #059669;
  font-size: 0.85rem;
  font-weight: 500;
  margin-top: 0.75rem;
  padding: 0.5rem;
  background: #d1fae5;
  border-radius: 6px;
  text-align: center;
  animation: fadeIn 0.3s ease-out;
}
</style>

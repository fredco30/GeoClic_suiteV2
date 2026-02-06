<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import HelpButton from '@/components/help/HelpButton.vue'

// Types
interface Service {
  id: string
  project_id: string
  nom: string
  code: string | null
  description: string | null
  email: string | null
  telephone: string | null
  responsable_nom: string | null
  actif: boolean
  ordre_affichage: number
  couleur: string
  icone: string
  notifier_nouvelle_demande: boolean
  notifier_changement_statut: boolean
  emails_notification: string[]
  created_at: string
  updated_at: string
  total_demandes?: number
  demandes_en_cours?: number
}

interface Agent {
  id: string
  service_id: string
  email: string | null
  nom: string | null
  prenom: string | null
  nom_complet: string
  telephone: string | null
  role: 'responsable' | 'agent'
  peut_assigner: boolean
  recoit_notifications: boolean
  actif: boolean
  last_login: string | null
  created_at: string
}

interface Project {
  id: string
  name: string
}

// State
const services = ref<Service[]>([])
const projects = ref<Project[]>([])
const loading = ref(true)
const showModal = ref(false)
const editingService = ref<Service | null>(null)
const currentProjectId = ref<string | null>(null)

// Agents State
const showAgentsModal = ref(false)
const selectedServiceForAgents = ref<Service | null>(null)
const agents = ref<Agent[]>([])
const loadingAgents = ref(false)
const showAgentForm = ref(false)
const editingAgent = ref<Agent | null>(null)
const agentForm = ref({
  email: '',
  password: '',
  nom: '',
  prenom: '',
  telephone: '',
  role: 'agent' as 'responsable' | 'agent',
  peut_assigner: false,
  recoit_notifications: true
})

// Form
const form = ref({
  nom: '',
  code: '',
  description: '',
  email: '',
  telephone: '',
  responsable_nom: '',
  actif: true,
  ordre_affichage: 0,
  couleur: '#3b82f6',
  icone: 'business',
  notifier_nouvelle_demande: true,
  notifier_changement_statut: false,
  emails_notification: [] as string[],
  newEmail: ''
})

// Icones disponibles
const icones = [
  // Services généraux
  { name: 'business', emoji: '🏢', label: 'Service' },
  { name: 'engineering', emoji: '👷', label: 'Technique' },
  { name: 'groups', emoji: '👥', label: 'Social' },
  { name: 'support_agent', emoji: '🎧', label: 'Support' },

  // Espaces verts et environnement
  { name: 'park', emoji: '🌳', label: 'Espaces verts' },
  { name: 'eco', emoji: '🌿', label: 'Environnement' },
  { name: 'grass', emoji: '🌱', label: 'Jardins' },
  { name: 'pets', emoji: '🐕', label: 'Animaux' },

  // Propreté et déchets
  { name: 'delete', emoji: '🗑️', label: 'Propreté' },
  { name: 'recycling', emoji: '♻️', label: 'Recyclage' },
  { name: 'cleaning', emoji: '🧹', label: 'Nettoyage' },

  // Voirie et mobilité
  { name: 'directions_car', emoji: '🚗', label: 'Voirie' },
  { name: 'construction', emoji: '🚧', label: 'Travaux' },
  { name: 'traffic', emoji: '🚦', label: 'Circulation' },
  { name: 'directions_bike', emoji: '🚲', label: 'Vélos' },
  { name: 'directions_bus', emoji: '🚌', label: 'Transport' },
  { name: 'local_parking', emoji: '🅿️', label: 'Parking' },

  // Réseaux et énergie
  { name: 'lightbulb', emoji: '💡', label: 'Eclairage' },
  { name: 'water_drop', emoji: '🚰', label: 'Eau' },
  { name: 'bolt', emoji: '⚡', label: 'Electricité' },
  { name: 'local_fire_department', emoji: '🔥', label: 'Chauffage' },

  // Urbanisme et bâtiments
  { name: 'home', emoji: '🏠', label: 'Urbanisme' },
  { name: 'apartment', emoji: '🏗️', label: 'Bâtiments' },
  { name: 'foundation', emoji: '🏛️', label: 'Patrimoine' },

  // Sécurité et prévention
  { name: 'security', emoji: '🛡️', label: 'Sécurité' },
  { name: 'local_police', emoji: '👮', label: 'Police' },
  { name: 'emergency', emoji: '🚨', label: 'Urgences' },

  // Education et culture
  { name: 'school', emoji: '🏫', label: 'Education' },
  { name: 'menu_book', emoji: '📚', label: 'Bibliothèque' },
  { name: 'theater_comedy', emoji: '🎭', label: 'Culture' },

  // Sports et loisirs
  { name: 'sports_soccer', emoji: '⚽', label: 'Sports' },
  { name: 'pool', emoji: '🏊', label: 'Piscine' },
  { name: 'fitness_center', emoji: '🏋️', label: 'Fitness' },

  // Autres
  { name: 'restaurant', emoji: '🍽️', label: 'Restauration' },
  { name: 'medical_services', emoji: '🏥', label: 'Santé' },
  { name: 'elderly', emoji: '👴', label: 'Seniors' },
  { name: 'child_care', emoji: '👶', label: 'Petite enfance' },
  { name: 'handyman', emoji: '🔧', label: 'Maintenance' },
  { name: 'settings', emoji: '⚙️', label: 'Administration' },
]

// Couleurs prédéfinies
const couleurs = [
  '#3b82f6', // Bleu
  '#10b981', // Vert
  '#f59e0b', // Orange
  '#ef4444', // Rouge
  '#8b5cf6', // Violet
  '#ec4899', // Rose
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#f97316', // Orange foncé
  '#6366f1', // Indigo
]

// Computed
const statsTotal = computed(() => services.value.length)
const statsActifs = computed(() => services.value.filter(s => s.actif).length)
const statsDemandes = computed(() => services.value.reduce((sum, s) => sum + (s.total_demandes || 0), 0))

const currentProject = computed(() => {
  return projects.value.find(p => p.id === currentProjectId.value)
})

// Helpers
function getIconEmoji(iconName: string): string {
  const icon = icones.find(i => i.name === iconName)
  return icon?.emoji || '🏢'
}

// API calls
async function loadProjects() {
  try {
    // Charger les projets incluant le projet système pour Demandes
    const response = await axios.get('/api/sig/projects', {
      params: { include_system: true }
    })
    projects.value = response.data?.projects || []

    // Auto-sélectionner le projet système
    const systemProject = projects.value.find((p: any) => p.is_system)
    if (systemProject) {
      currentProjectId.value = systemProject.id
      await loadServices()
    } else if (projects.value.length > 0 && !currentProjectId.value) {
      // Fallback: sélectionner le premier projet
      currentProjectId.value = projects.value[0].id
      await loadServices()
    }
  } catch (error) {
    console.error('Erreur chargement projets:', error)
    projects.value = []
  }
}

async function loadServices() {
  if (!currentProjectId.value) return

  loading.value = true
  try {
    const response = await axios.get('/api/demandes/services', {
      params: {
        project_id: currentProjectId.value,
        actif_only: false,
        include_stats: true
      }
    })
    services.value = response.data
  } catch (error) {
    console.error('Erreur chargement services:', error)
  } finally {
    loading.value = false
  }
}

async function saveService() {
  if (!currentProjectId.value) return

  try {
    const data = {
      nom: form.value.nom,
      code: form.value.code || null,
      description: form.value.description || null,
      email: form.value.email || null,
      telephone: form.value.telephone || null,
      responsable_nom: form.value.responsable_nom || null,
      actif: form.value.actif,
      ordre_affichage: form.value.ordre_affichage,
      couleur: form.value.couleur,
      icone: form.value.icone,
      notifier_nouvelle_demande: form.value.notifier_nouvelle_demande,
      notifier_changement_statut: form.value.notifier_changement_statut,
      emails_notification: form.value.emails_notification,
    }

    if (editingService.value) {
      await axios.put(`/api/demandes/services/${editingService.value.id}`, data)
    } else {
      await axios.post('/api/demandes/services', data, {
        params: { project_id: currentProjectId.value }
      })
    }

    showModal.value = false
    resetForm()
    await loadServices()
  } catch (error: any) {
    console.error('Erreur sauvegarde service:', error)
    alert(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
  }
}

async function deleteService(service: Service) {
  if (!confirm(`Supprimer le service "${service.nom}" ?`)) return

  try {
    await axios.delete(`/api/demandes/services/${service.id}`)
    await loadServices()
  } catch (error: any) {
    if (error.response?.status === 400) {
      alert(error.response.data.detail)
    } else {
      console.error('Erreur suppression:', error)
    }
  }
}

function editService(service: Service) {
  editingService.value = service
  form.value = {
    nom: service.nom,
    code: service.code || '',
    description: service.description || '',
    email: service.email || '',
    telephone: service.telephone || '',
    responsable_nom: service.responsable_nom || '',
    actif: service.actif,
    ordre_affichage: service.ordre_affichage,
    couleur: service.couleur,
    icone: service.icone,
    notifier_nouvelle_demande: service.notifier_nouvelle_demande,
    notifier_changement_statut: service.notifier_changement_statut,
    emails_notification: [...(service.emails_notification || [])],
    newEmail: ''
  }
  showModal.value = true
}

function openNewServiceModal() {
  editingService.value = null
  resetForm()
  showModal.value = true
}

function resetForm() {
  form.value = {
    nom: '',
    code: '',
    description: '',
    email: '',
    telephone: '',
    responsable_nom: '',
    actif: true,
    ordre_affichage: services.value.length,
    couleur: '#3b82f6',
    icone: 'business',
    notifier_nouvelle_demande: true,
    notifier_changement_statut: false,
    emails_notification: [],
    newEmail: ''
  }
}

function addNotificationEmail() {
  const email = form.value.newEmail.trim()
  if (email && !form.value.emails_notification.includes(email)) {
    form.value.emails_notification.push(email)
    form.value.newEmail = ''
  }
}

function removeNotificationEmail(index: number) {
  form.value.emails_notification.splice(index, 1)
}

// ========== Gestion des agents ==========
async function openAgentsModal(service: Service) {
  selectedServiceForAgents.value = service
  showAgentsModal.value = true
  await loadAgents(service.id)
}

async function loadAgents(serviceId: string) {
  loadingAgents.value = true
  try {
    const response = await axios.get(`/api/demandes/services/${serviceId}/agents`, {
      params: { include_inactive: true }
    })
    agents.value = response.data
  } catch (error) {
    console.error('Erreur chargement agents:', error)
    agents.value = []
  } finally {
    loadingAgents.value = false
  }
}

function openNewAgentForm() {
  editingAgent.value = null
  agentForm.value = {
    email: '',
    password: '',
    nom: '',
    prenom: '',
    telephone: '',
    role: 'agent',
    peut_assigner: false,
    recoit_notifications: true
  }
  showAgentForm.value = true
}

function openEditAgentForm(agent: Agent) {
  editingAgent.value = agent
  agentForm.value = {
    email: agent.email || '',
    password: '',
    nom: agent.nom || '',
    prenom: agent.prenom || '',
    telephone: agent.telephone || '',
    role: agent.role,
    peut_assigner: agent.peut_assigner,
    recoit_notifications: agent.recoit_notifications
  }
  showAgentForm.value = true
}

async function saveAgent() {
  if (!selectedServiceForAgents.value) return

  try {
    if (editingAgent.value) {
      // Modification
      await axios.put(`/api/demandes/services/${selectedServiceForAgents.value.id}/agents/${editingAgent.value.id}`, {
        nom: agentForm.value.nom,
        prenom: agentForm.value.prenom,
        telephone: agentForm.value.telephone || null,
        role: agentForm.value.role,
        peut_assigner: agentForm.value.peut_assigner,
        recoit_notifications: agentForm.value.recoit_notifications
      })
    } else {
      // Création
      await axios.post(`/api/demandes/services/${selectedServiceForAgents.value.id}/agents`, {
        email: agentForm.value.email,
        password: agentForm.value.password,
        nom: agentForm.value.nom,
        prenom: agentForm.value.prenom,
        telephone: agentForm.value.telephone || null,
        role: agentForm.value.role,
        peut_assigner: agentForm.value.peut_assigner,
        recoit_notifications: agentForm.value.recoit_notifications
      })
    }

    showAgentForm.value = false
    await loadAgents(selectedServiceForAgents.value.id)
  } catch (error: any) {
    console.error('Erreur sauvegarde agent:', error)
    alert(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
  }
}

async function resetAgentPassword(agent: Agent) {
  const newPassword = prompt('Nouveau mot de passe pour ' + agent.nom_complet + ' (min 6 caractères):')
  if (!newPassword || newPassword.length < 6) {
    if (newPassword) alert('Le mot de passe doit faire au moins 6 caractères')
    return
  }

  if (!selectedServiceForAgents.value) return

  try {
    await axios.post(`/api/demandes/services/${selectedServiceForAgents.value.id}/agents/${agent.id}/reset-password`, {
      new_password: newPassword
    })
    alert('Mot de passe réinitialisé avec succès')
  } catch (error: any) {
    console.error('Erreur reset password:', error)
    alert(error.response?.data?.detail || 'Erreur lors de la réinitialisation')
  }
}

async function toggleAgentStatus(agent: Agent) {
  if (!selectedServiceForAgents.value) return

  const action = agent.actif ? 'désactiver' : 'réactiver'
  if (!confirm(`Voulez-vous ${action} l'agent "${agent.nom_complet}" ?`)) return

  try {
    if (agent.actif) {
      await axios.delete(`/api/demandes/services/${selectedServiceForAgents.value.id}/agents/${agent.id}`)
    } else {
      await axios.put(`/api/demandes/services/${selectedServiceForAgents.value.id}/agents/${agent.id}`, {
        actif: true
      })
    }
    await loadAgents(selectedServiceForAgents.value.id)
  } catch (error: any) {
    console.error('Erreur toggle agent:', error)
    alert(error.response?.data?.detail || 'Erreur')
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Jamais'
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  await loadProjects()
})
</script>

<template>
  <div class="services-page">
    <!-- Header -->
    <header class="page-header">
      <div class="header-content">
        <h1>Services municipaux <HelpButton page-key="services" size="sm" /></h1>
        <p>Gérez les services de votre collectivité pour l'affectation des demandes</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" @click="openNewServiceModal" :disabled="!currentProjectId">
          + Nouveau service
        </button>
      </div>
    </header>

    <!-- Stats -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-value">{{ statsTotal }}</div>
        <div class="stat-label">Services</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ statsActifs }}</div>
        <div class="stat-label">Actifs</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ statsDemandes }}</div>
        <div class="stat-label">Demandes totales</div>
      </div>
    </div>

    <!-- Liste des services -->
    <div class="services-list" v-if="!loading">
      <div v-if="services.length === 0" class="empty-state">
        <div class="empty-icon">🏢</div>
        <h3>Aucun service</h3>
        <p>Créez votre premier service municipal pour commencer à affecter les demandes.</p>
        <button class="btn btn-primary" @click="openNewServiceModal">
          + Créer un service
        </button>
      </div>

      <div v-else class="services-grid">
        <div
          v-for="service in services"
          :key="service.id"
          class="service-card"
          :class="{ inactive: !service.actif }"
        >
          <div class="service-header" :style="{ borderColor: service.couleur }">
            <div class="service-icon" :style="{ backgroundColor: service.couleur }">
              {{ getIconEmoji(service.icone) }}
            </div>
            <div class="service-info">
              <h3>{{ service.nom }}</h3>
              <span v-if="service.code" class="service-code">{{ service.code }}</span>
            </div>
            <span v-if="!service.actif" class="badge inactive-badge">Inactif</span>
          </div>

          <div class="service-body">
            <p v-if="service.description" class="service-description">{{ service.description }}</p>

            <div class="service-details">
              <div v-if="service.responsable_nom" class="detail-row">
                <span class="detail-label">Responsable</span>
                <span class="detail-value">{{ service.responsable_nom }}</span>
              </div>
              <div v-if="service.email" class="detail-row">
                <span class="detail-label">Email</span>
                <span class="detail-value">{{ service.email }}</span>
              </div>
              <div v-if="service.telephone" class="detail-row">
                <span class="detail-label">Téléphone</span>
                <span class="detail-value">{{ service.telephone }}</span>
              </div>
            </div>

            <div class="service-stats">
              <div class="stat">
                <span class="stat-number">{{ service.total_demandes || 0 }}</span>
                <span class="stat-text">demandes</span>
              </div>
              <div class="stat">
                <span class="stat-number">{{ service.demandes_en_cours || 0 }}</span>
                <span class="stat-text">en cours</span>
              </div>
            </div>
          </div>

          <div class="service-actions">
            <button class="btn btn-sm btn-outline" @click="openAgentsModal(service)" title="Gérer les identifiants de connexion">
              🔑 Identifiants
            </button>
            <button class="btn btn-sm btn-secondary" @click="editService(service)">
              Modifier
            </button>
            <button class="btn btn-sm btn-danger" @click="deleteService(service)">
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="loading">
      <div class="spinner"></div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h2>{{ editingService ? 'Modifier le service' : 'Nouveau service' }}</h2>

        <form @submit.prevent="saveService">
          <div class="form-row">
            <div class="form-group flex-2">
              <label>Nom du service *</label>
              <input v-model="form.nom" type="text" required placeholder="Ex: Service Voirie" />
            </div>
            <div class="form-group flex-1">
              <label>Code</label>
              <input v-model="form.code" type="text" placeholder="Ex: VOI" maxlength="20" />
            </div>
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea v-model="form.description" rows="2" placeholder="Description du service..."></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Responsable</label>
              <input v-model="form.responsable_nom" type="text" placeholder="Nom du responsable" />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input v-model="form.email" type="email" placeholder="service@mairie.fr" />
            </div>
            <div class="form-group">
              <label>Téléphone</label>
              <input v-model="form.telephone" type="tel" placeholder="01 23 45 67 89" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Icône</label>
              <div class="icon-grid">
                <button
                  v-for="icon in icones"
                  :key="icon.name"
                  type="button"
                  class="icon-btn"
                  :class="{ active: form.icone === icon.name }"
                  @click="form.icone = icon.name"
                  :title="icon.label"
                >
                  {{ icon.emoji }}
                </button>
              </div>
            </div>
            <div class="form-group">
              <label>Couleur</label>
              <div class="color-grid">
                <button
                  v-for="color in couleurs"
                  :key="color"
                  type="button"
                  class="color-btn"
                  :class="{ active: form.couleur === color }"
                  :style="{ backgroundColor: color }"
                  @click="form.couleur = color"
                ></button>
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="form.actif" />
                Service actif
              </label>
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="form.notifier_nouvelle_demande" />
                Notifier nouvelles demandes
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>Emails de notification supplémentaires</label>
            <div class="email-input-row">
              <input
                v-model="form.newEmail"
                type="email"
                placeholder="email@exemple.fr"
                @keyup.enter.prevent="addNotificationEmail"
              />
              <button type="button" class="btn btn-secondary btn-sm" @click="addNotificationEmail">
                Ajouter
              </button>
            </div>
            <div v-if="form.emails_notification.length > 0" class="email-tags">
              <span v-for="(email, idx) in form.emails_notification" :key="idx" class="email-tag">
                {{ email }}
                <button type="button" @click="removeNotificationEmail(idx)">&times;</button>
              </span>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="showModal = false">
              Annuler
            </button>
            <button type="submit" class="btn btn-primary">
              {{ editingService ? 'Enregistrer' : 'Créer' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Agents -->
    <div v-if="showAgentsModal" class="modal-overlay" @click.self="showAgentsModal = false">
      <div class="modal modal-lg">
        <div class="modal-header-bar">
          <h2>🔑 Identifiants - {{ selectedServiceForAgents?.nom }}</h2>
          <button class="btn-close" @click="showAgentsModal = false">&times;</button>
        </div>

        <p class="modal-subtitle">
          Ces identifiants permettent aux agents de se connecter à GeoClic Services pour gérer les demandes.
        </p>

        <div v-if="!showAgentForm">
          <!-- Liste des agents -->
          <div class="agents-header">
            <button class="btn btn-primary btn-sm" @click="openNewAgentForm">
              + Nouvel identifiant
            </button>
          </div>

          <div v-if="loadingAgents" class="loading-small">
            <div class="spinner-small"></div>
          </div>

          <div v-else-if="agents.length === 0" class="empty-state-small">
            <p>Aucun identifiant créé pour ce service.</p>
            <p class="text-muted">Créez un identifiant pour permettre aux agents de se connecter.</p>
          </div>

          <div v-else class="agents-list">
            <div v-for="agent in agents" :key="agent.id" class="agent-card" :class="{ inactive: !agent.actif }">
              <div class="agent-info">
                <div class="agent-avatar" :class="{ responsable: agent.role === 'responsable' }">
                  {{ agent.prenom?.[0] || agent.nom?.[0] || '?' }}{{ agent.nom?.[1] || '' }}
                </div>
                <div class="agent-details">
                  <div class="agent-name">
                    {{ agent.nom_complet }}
                    <span v-if="agent.role === 'responsable'" class="role-badge responsable">Responsable</span>
                    <span v-else class="role-badge agent">Agent</span>
                    <span v-if="!agent.actif" class="status-badge inactive">Désactivé</span>
                  </div>
                  <div class="agent-email">{{ agent.email }}</div>
                  <div class="agent-meta">
                    <span v-if="agent.peut_assigner" class="meta-badge">Peut assigner</span>
                    <span v-if="agent.recoit_notifications" class="meta-badge">Notifications</span>
                    <span class="meta-date">Dernière connexion: {{ formatDate(agent.last_login) }}</span>
                  </div>
                </div>
              </div>
              <div class="agent-actions">
                <button class="btn btn-xs btn-secondary" @click="openEditAgentForm(agent)" title="Modifier">
                  ✏️
                </button>
                <button class="btn btn-xs btn-secondary" @click="resetAgentPassword(agent)" title="Réinitialiser mot de passe">
                  🔄
                </button>
                <button
                  class="btn btn-xs"
                  :class="agent.actif ? 'btn-danger' : 'btn-success'"
                  @click="toggleAgentStatus(agent)"
                  :title="agent.actif ? 'Désactiver' : 'Réactiver'"
                >
                  {{ agent.actif ? '🚫' : '✅' }}
                </button>
              </div>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="showAgentsModal = false">
              Fermer
            </button>
          </div>
        </div>

        <!-- Formulaire agent -->
        <div v-else class="agent-form-container">
          <h3>{{ editingAgent ? 'Modifier l\'identifiant' : 'Nouvel identifiant' }}</h3>

          <form @submit.prevent="saveAgent">
            <div class="form-row">
              <div class="form-group">
                <label>Prénom *</label>
                <input v-model="agentForm.prenom" type="text" required placeholder="Jean" />
              </div>
              <div class="form-group">
                <label>Nom *</label>
                <input v-model="agentForm.nom" type="text" required placeholder="Dupont" />
              </div>
            </div>

            <div class="form-group" v-if="!editingAgent">
              <label>Email de connexion *</label>
              <input v-model="agentForm.email" type="text" required placeholder="jean.dupont@mairie.local" />
              <small class="form-hint">Cet email servira d'identifiant de connexion</small>
            </div>
            <div class="form-group" v-else>
              <label>Email de connexion</label>
              <input :value="editingAgent.email" type="text" disabled class="input-disabled" />
              <small class="form-hint">L'email ne peut pas être modifié</small>
            </div>

            <div class="form-group" v-if="!editingAgent">
              <label>Mot de passe *</label>
              <input v-model="agentForm.password" type="password" required minlength="6" placeholder="Minimum 6 caractères" />
            </div>

            <div class="form-group">
              <label>Téléphone</label>
              <input v-model="agentForm.telephone" type="tel" placeholder="06 12 34 56 78" />
            </div>

            <div class="form-group">
              <label>Rôle</label>
              <select v-model="agentForm.role">
                <option value="agent">Agent</option>
                <option value="responsable">Responsable</option>
              </select>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="agentForm.peut_assigner" />
                  Peut assigner des demandes
                </label>
              </div>
              <div class="form-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="agentForm.recoit_notifications" />
                  Reçoit les notifications
                </label>
              </div>
            </div>

            <div class="modal-actions">
              <button type="button" class="btn btn-secondary" @click="showAgentForm = false">
                Annuler
              </button>
              <button type="submit" class="btn btn-primary">
                {{ editingAgent ? 'Enregistrer' : 'Créer' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.services-page {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-content h1 {
  font-size: 1.75rem;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.header-content p {
  color: #6b7280;
  font-size: 0.95rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.project-select {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  font-size: 0.95rem;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #3b82f6;
}

.stat-label {
  color: #6b7280;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.service-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.service-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.service-card.inactive {
  opacity: 0.7;
}

.service-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-left: 4px solid;
  background: #f9fafb;
}

.service-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.service-info h3 {
  font-size: 1.1rem;
  color: #1f2937;
  margin: 0;
}

.service-code {
  font-size: 0.8rem;
  color: #6b7280;
  font-family: monospace;
  background: #e5e7eb;
  padding: 2px 6px;
  border-radius: 4px;
}

.inactive-badge {
  background: #fee2e2;
  color: #dc2626;
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: auto;
}

.service-body {
  padding: 1rem 1.25rem;
}

.service-description {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.service-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
}

.detail-label {
  color: #6b7280;
}

.detail-value {
  color: #374151;
}

.service-stats {
  display: flex;
  gap: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.service-stats .stat {
  text-align: center;
}

.stat-number {
  font-size: 1.25rem;
  font-weight: 600;
  color: #3b82f6;
}

.stat-text {
  font-size: 0.75rem;
  color: #6b7280;
  display: block;
}

.service-actions {
  padding: 0.75rem 1.25rem;
  background: #f9fafb;
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #6b7280;
  margin-bottom: 1.5rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h2 {
  font-size: 1.5rem;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.form-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-group {
  flex: 1;
  margin-bottom: 1rem;
}

.form-group.flex-2 {
  flex: 2;
}

.form-group.flex-1 {
  flex: 1;
}

.form-group label {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.95rem;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-label input {
  width: auto !important;
}

.icon-grid,
.color-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.icon-btn {
  width: 40px;
  height: 40px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  font-size: 1.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  border-color: #3b82f6;
}

.icon-btn.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.color-btn {
  width: 32px;
  height: 32px;
  border: 3px solid transparent;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.color-btn:hover {
  transform: scale(1.1);
}

.color-btn.active {
  border-color: #1f2937;
}

.email-input-row {
  display: flex;
  gap: 0.5rem;
}

.email-input-row input {
  flex: 1;
}

.email-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.email-tag {
  background: #e5e7eb;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.email-tag button {
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
  font-size: 1.1rem;
  line-height: 1;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

/* Buttons */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-danger {
  background: #fee2e2;
  color: #dc2626;
}

.btn-danger:hover {
  background: #fecaca;
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
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Btn outline */
.btn-outline {
  background: white;
  border: 1px solid #d1d5db;
  color: #374151;
}

.btn-outline:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

/* Btn success */
.btn-success {
  background: #dcfce7;
  color: #16a34a;
}

.btn-success:hover {
  background: #bbf7d0;
}

/* Btn extra small */
.btn-xs {
  padding: 0.35rem 0.6rem;
  font-size: 0.8rem;
}

/* Modal large */
.modal-lg {
  max-width: 700px;
}

.modal-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.modal-header-bar h2 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.btn-close:hover {
  color: #374151;
}

.modal-subtitle {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

/* Agents section */
.agents-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.loading-small {
  display: flex;
  justify-content: center;
  padding: 2rem;
}

.spinner-small {
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.empty-state-small {
  text-align: center;
  padding: 2rem;
  background: #f9fafb;
  border-radius: 8px;
}

.empty-state-small p {
  margin: 0.25rem 0;
}

.text-muted {
  color: #9ca3af;
  font-size: 0.85rem;
}

/* Agents list */
.agents-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.agent-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
}

.agent-card.inactive {
  opacity: 0.6;
  background: #fef2f2;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.agent-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.agent-avatar.responsable {
  background: #8b5cf6;
}

.agent-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-name {
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.role-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.role-badge.responsable {
  background: #ede9fe;
  color: #7c3aed;
}

.role-badge.agent {
  background: #dbeafe;
  color: #2563eb;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #dc2626;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
}

.agent-email {
  color: #6b7280;
  font-size: 0.85rem;
}

.agent-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
  margin-top: 4px;
}

.meta-badge {
  font-size: 0.7rem;
  padding: 2px 6px;
  background: #e5e7eb;
  border-radius: 4px;
  color: #4b5563;
}

.meta-date {
  font-size: 0.75rem;
  color: #9ca3af;
}

.agent-actions {
  display: flex;
  gap: 0.5rem;
}

/* Agent form */
.agent-form-container {
  padding-top: 0.5rem;
}

.agent-form-container h3 {
  font-size: 1.1rem;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.form-hint {
  display: block;
  font-size: 0.8rem;
  color: #9ca3af;
  margin-top: 4px;
}

.input-disabled {
  background: #f3f4f6 !important;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .form-row {
    flex-direction: column;
    gap: 0;
  }

  .services-grid {
    grid-template-columns: 1fr;
  }

  .agent-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .agent-actions {
    align-self: flex-end;
  }
}
</style>

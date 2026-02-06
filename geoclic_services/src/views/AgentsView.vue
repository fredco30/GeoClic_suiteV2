<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

interface Agent {
  id: string
  email: string
  nom: string | null
  prenom: string | null
  nom_complet: string
  telephone: string | null
  role: 'responsable' | 'agent'
  peut_assigner: boolean
  actif: boolean
  last_login: string | null
  created_at: string
  demandes_assignees: number
  demandes_traitees: number
}

const agents = ref<Agent[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const showModal = ref(false)
const modalMode = ref<'create' | 'edit'>('create')
const editingAgent = ref<Agent | null>(null)

const formData = ref({
  email: '',
  password: '',
  nom: '',
  prenom: '',
  telephone: '',
  role: 'agent' as 'responsable' | 'agent',
  peut_assigner: false,
})

const showResetPasswordModal = ref(false)
const resetPasswordAgent = ref<Agent | null>(null)
const newPassword = ref('')

async function loadAgents() {
  loading.value = true
  try {
    const response = await axios.get('/api/services/agents?include_inactive=true')
    agents.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Erreur lors du chargement'
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  modalMode.value = 'create'
  editingAgent.value = null
  formData.value = {
    email: '',
    password: '',
    nom: '',
    prenom: '',
    telephone: '',
    role: 'agent',
    peut_assigner: false,
  }
  showModal.value = true
}

function openEditModal(agent: Agent) {
  modalMode.value = 'edit'
  editingAgent.value = agent
  formData.value = {
    email: agent.email,
    password: '',
    nom: agent.nom || '',
    prenom: agent.prenom || '',
    telephone: agent.telephone || '',
    role: agent.role,
    peut_assigner: agent.peut_assigner,
  }
  showModal.value = true
}

async function handleSubmit() {
  try {
    if (modalMode.value === 'create') {
      await axios.post('/api/services/agents', {
        email: formData.value.email,
        password: formData.value.password,
        nom: formData.value.nom,
        prenom: formData.value.prenom,
        telephone: formData.value.telephone || null,
        role: formData.value.role,
        peut_assigner: formData.value.peut_assigner,
      })
    } else if (editingAgent.value) {
      await axios.put(`/api/services/agents/${editingAgent.value.id}`, {
        nom: formData.value.nom,
        prenom: formData.value.prenom,
        telephone: formData.value.telephone || null,
        role: formData.value.role,
        peut_assigner: formData.value.peut_assigner,
      })
    }

    showModal.value = false
    await loadAgents()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Erreur lors de l\'enregistrement'
  }
}

function openResetPasswordModal(agent: Agent) {
  resetPasswordAgent.value = agent
  newPassword.value = ''
  showResetPasswordModal.value = true
}

async function handleResetPassword() {
  if (!resetPasswordAgent.value || !newPassword.value) return

  try {
    await axios.post(`/api/services/agents/${resetPasswordAgent.value.id}/reset-password`, {
      new_password: newPassword.value
    })
    showResetPasswordModal.value = false
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Erreur lors de la réinitialisation'
  }
}

async function toggleAgentStatus(agent: Agent) {
  try {
    if (agent.actif) {
      await axios.delete(`/api/services/agents/${agent.id}`)
    } else {
      await axios.put(`/api/services/agents/${agent.id}`, { actif: true })
    }
    await loadAgents()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Erreur lors de la modification'
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

onMounted(() => {
  loadAgents()
})
</script>

<template>
  <div class="agents-page">
    <div class="page-header">
      <div>
        <h1>Agents du service</h1>
        <p class="text-gray">Gérez les membres de votre équipe</p>
      </div>
      <button class="btn btn-primary" @click="openCreateModal">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        Nouvel agent
      </button>
    </div>

    <div v-if="error" class="alert alert-error">
      {{ error }}
      <button class="alert-close" @click="error = null">&times;</button>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <div v-else class="agents-grid">
      <div
        v-for="agent in agents"
        :key="agent.id"
        :class="['agent-card', { inactive: !agent.actif }]"
      >
        <div class="agent-header">
          <div class="agent-avatar">
            {{ (agent.prenom?.charAt(0) || agent.email.charAt(0)).toUpperCase() }}
          </div>
          <div class="agent-info">
            <h3>{{ agent.nom_complet }}</h3>
            <span class="agent-email">{{ agent.email }}</span>
          </div>
          <span :class="['badge', agent.role === 'responsable' ? 'badge-info' : 'badge-gray']">
            {{ agent.role === 'responsable' ? 'Responsable' : 'Agent' }}
          </span>
        </div>

        <div class="agent-stats">
          <div class="stat">
            <span class="stat-value">{{ agent.demandes_assignees }}</span>
            <span class="stat-label">Assignées</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ agent.demandes_traitees }}</span>
            <span class="stat-label">Traitées</span>
          </div>
        </div>

        <div class="agent-meta">
          <span v-if="agent.telephone" class="meta-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/>
            </svg>
            {{ agent.telephone }}
          </span>
          <span class="meta-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12,6 12,12 16,14"/>
            </svg>
            Dernière connexion : {{ formatDate(agent.last_login) }}
          </span>
        </div>

        <div v-if="!agent.actif" class="inactive-badge">
          Désactivé
        </div>

        <div class="agent-actions">
          <button class="btn btn-sm btn-secondary" @click="openEditModal(agent)">
            Modifier
          </button>
          <button class="btn btn-sm btn-secondary" @click="openResetPasswordModal(agent)">
            Reset MDP
          </button>
          <button
            v-if="agent.id !== authStore.agent?.id"
            :class="['btn', 'btn-sm', agent.actif ? 'btn-danger' : 'btn-success']"
            @click="toggleAgentStatus(agent)"
          >
            {{ agent.actif ? 'Désactiver' : 'Réactiver' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal création/édition -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ modalMode === 'create' ? 'Nouvel agent' : 'Modifier l\'agent' }}</h3>

        <form @submit.prevent="handleSubmit">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Prénom *</label>
              <input v-model="formData.prenom" type="text" class="form-input" required />
            </div>
            <div class="form-group">
              <label class="form-label">Nom *</label>
              <input v-model="formData.nom" type="text" class="form-input" required />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Email *</label>
            <input
              v-model="formData.email"
              type="email"
              class="form-input"
              required
              :disabled="modalMode === 'edit'"
            />
          </div>

          <div v-if="modalMode === 'create'" class="form-group">
            <label class="form-label">Mot de passe *</label>
            <input v-model="formData.password" type="password" class="form-input" required minlength="6" />
          </div>

          <div class="form-group">
            <label class="form-label">Téléphone</label>
            <input v-model="formData.telephone" type="tel" class="form-input" />
          </div>

          <div class="form-group">
            <label class="form-label">Rôle</label>
            <select v-model="formData.role" class="form-input">
              <option value="agent">Agent terrain</option>
              <option value="responsable">Responsable</option>
            </select>
          </div>

          <div class="form-group checkbox-group">
            <label>
              <input type="checkbox" v-model="formData.peut_assigner" />
              Peut assigner des demandes à d'autres agents
            </label>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="showModal = false">Annuler</button>
            <button type="submit" class="btn btn-primary">
              {{ modalMode === 'create' ? 'Créer' : 'Enregistrer' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal reset password -->
    <div v-if="showResetPasswordModal" class="modal-overlay" @click.self="showResetPasswordModal = false">
      <div class="modal">
        <h3>Réinitialiser le mot de passe</h3>
        <p>Agent : <strong>{{ resetPasswordAgent?.nom_complet }}</strong></p>

        <form @submit.prevent="handleResetPassword">
          <div class="form-group">
            <label class="form-label">Nouveau mot de passe *</label>
            <input v-model="newPassword" type="password" class="form-input" required minlength="6" />
          </div>

          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="showResetPasswordModal = false">Annuler</button>
            <button type="submit" class="btn btn-primary">Réinitialiser</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agents-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: 0.25rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

.alert-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  float: right;
}

/* Agents grid */
.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1rem;
}

.agent-card {
  background: white;
  border-radius: var(--radius);
  padding: 1.25rem;
  box-shadow: var(--shadow);
  position: relative;
}

.agent-card.inactive {
  opacity: 0.7;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.agent-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.25rem;
}

.agent-info {
  flex: 1;
}

.agent-info h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--gray-800);
}

.agent-email {
  font-size: 0.8rem;
  color: var(--gray-500);
}

.agent-stats {
  display: flex;
  gap: 2rem;
  padding: 0.75rem 0;
  border-top: 1px solid var(--gray-100);
  border-bottom: 1px solid var(--gray-100);
  margin-bottom: 0.75rem;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--gray-800);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.agent-meta {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--gray-500);
  margin-bottom: 1rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.inactive-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: var(--gray-200);
  color: var(--gray-600);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.agent-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
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
}

.modal {
  background: white;
  border-radius: var(--radius);
  padding: 1.5rem;
  width: 100%;
  max-width: 450px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}

.modal h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.modal p {
  color: var(--gray-600);
  margin-bottom: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--gray-700);
  cursor: pointer;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}
</style>

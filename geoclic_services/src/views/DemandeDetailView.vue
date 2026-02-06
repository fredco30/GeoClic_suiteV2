<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDemandesStore } from '../stores/demandes'
import { useAuthStore } from '../stores/auth'
import ChatSection from '../components/ChatSection.vue'
import MiniMap from '../components/MiniMap.vue'

const route = useRoute()
const router = useRouter()
const demandesStore = useDemandesStore()
const authStore = useAuthStore()

const demandeId = computed(() => route.params.id as string)
const demande = computed(() => demandesStore.currentDemande)
const loading = computed(() => demandesStore.loading)

const showStatutModal = ref(false)
const newStatut = ref('')

// Planification
const showPlanificationModal = ref(false)
const datePlanification = ref('')
const heurePlanification = ref('09:00')

// Agents
const showAgentModal = ref(false)
const agents = ref<any[]>([])
const selectedAgentId = ref('')
const agentsLoading = ref(false)

onMounted(async () => {
  await demandesStore.loadDemande(demandeId.value)
  // Charger les messages des deux canaux
  await Promise.all([
    demandesStore.loadMessages(demandeId.value, 'backoffice'),
    demandesStore.loadMessages(demandeId.value, 'terrain')
  ])
  // Marquer comme lus dans les deux canaux
  await Promise.all([
    demandesStore.markMessagesRead(demandeId.value, 'backoffice'),
    demandesStore.markMessagesRead(demandeId.value, 'terrain')
  ])
  await loadAgents()
})

async function loadAgents() {
  agentsLoading.value = true
  try {
    const response = await fetch('/api/services/agents', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('services_token')}`
      }
    })
    if (response.ok) {
      agents.value = await response.json()
    }
  } catch (error) {
    console.error('Erreur chargement agents:', error)
  } finally {
    agentsLoading.value = false
  }
}

function openAgentModal() {
  selectedAgentId.value = demande.value?.agent_service_id || ''
  showAgentModal.value = true
}

async function assignAgent() {
  if (!selectedAgentId.value) return

  try {
    const response = await fetch(`/api/services/demandes/${demandeId.value}/agent`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('services_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ agent_service_id: selectedAgentId.value })
    })

    if (response.ok) {
      showAgentModal.value = false
      await demandesStore.loadDemande(demandeId.value)
    } else {
      const error = await response.json()
      console.error('Erreur assignation:', error.detail)
      alert(error.detail || 'Erreur lors de l\'assignation')
    }
  } catch (error) {
    console.error('Erreur assignation agent:', error)
  }
}

function takeCharge() {
  // Ouvrir directement le modal pour changer le statut à "en_cours"
  openStatutModal('en_cours')
}

function goBack() {
  router.push({ name: 'demandes' })
}

function openStatutModal(statut: string) {
  newStatut.value = statut
  showStatutModal.value = true
}

async function confirmStatutChange() {
  const success = await demandesStore.updateStatut(demandeId.value, newStatut.value)
  if (success) {
    showStatutModal.value = false
  }
}

function openPlanificationModal() {
  // Pré-remplir avec demain par défaut
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  datePlanification.value = tomorrow.toISOString().split('T')[0]
  heurePlanification.value = '09:00'
  showPlanificationModal.value = true
}

async function confirmPlanification() {
  if (!datePlanification.value) return

  // Construire la date/heure ISO
  const dateTimePlanification = new Date(`${datePlanification.value}T${heurePlanification.value}:00`)

  const success = await demandesStore.updateStatut(
    demandeId.value,
    'planifie',
    undefined,
    dateTimePlanification.toISOString()
  )
  if (success) {
    showPlanificationModal.value = false
  }
}

function getStatutLabel(statut: string): string {
  const map: Record<string, string> = {
    nouveau: 'Nouveau',
    en_moderation: 'Modération',
    envoye: 'Envoyé',
    accepte: 'Accepté',
    en_cours: 'En cours',
    planifie: 'Planifié',
    traite: 'Traité',
    rejete: 'Rejeté',
    cloture: 'Cloturé',
  }
  return map[statut] || statut
}

function getStatutBadgeClass(statut: string): string {
  switch (statut) {
    case 'nouveau': return 'badge-info'
    case 'envoye': return 'badge-info'
    case 'accepte': return 'badge-warning'
    case 'en_cours': return 'badge-info'
    case 'planifie': return 'badge-info'
    case 'traite': return 'badge-success'
    default: return 'badge-gray'
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getPhotoUrl(photo: string): string {
  if (photo.startsWith('http')) return photo
  if (photo.startsWith('/api/')) return photo
  return `/api/photos/demandes/${photo}`
}
</script>

<template>
  <div class="demande-detail">
    <!-- Header -->
    <div class="detail-header">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Retour
      </button>

      <div v-if="demande" class="header-info">
        <h1>{{ demande.numero || 'Demande' }}</h1>
        <span :class="['badge', 'badge-lg', getStatutBadgeClass(demande.statut)]">
          {{ getStatutLabel(demande.statut) }}
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <!-- Contenu -->
    <template v-else-if="demande">
      <div class="detail-content">
        <!-- Colonne principale -->
        <div class="main-column">
          <!-- Infos générales -->
          <div class="card">
            <div class="card-header">
              <h2 class="card-title">Informations</h2>
              <div v-if="demande.priorite === 'urgente'" class="badge badge-danger">Urgente</div>
              <div v-else-if="demande.priorite === 'haute'" class="badge badge-warning">Haute priorité</div>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">Catégorie</span>
                <span class="info-value">
                  <span
                    v-if="demande.categorie_couleur"
                    class="category-dot"
                    :style="{ backgroundColor: demande.categorie_couleur }"
                  ></span>
                  {{ demande.categorie_nom || 'Non catégorisé' }}
                </span>
              </div>

              <div class="info-item">
                <span class="info-label">Adresse</span>
                <span class="info-value">{{ demande.adresse || '-' }}</span>
              </div>

              <div class="info-item">
                <span class="info-label">Quartier</span>
                <span class="info-value">{{ demande.quartier_nom || '-' }}</span>
              </div>

              <div class="info-item">
                <span class="info-label">Date de création</span>
                <span class="info-value">{{ formatDate(demande.created_at) }}</span>
              </div>
            </div>

            <div class="description-section">
              <span class="info-label">Description</span>
              <p class="description-text">{{ demande.description }}</p>
            </div>
          </div>

          <!-- Localisation -->
          <div v-if="demande.latitude && demande.longitude" class="card">
            <h2 class="card-title">Localisation</h2>
            <MiniMap
              :latitude="demande.latitude"
              :longitude="demande.longitude"
            />
          </div>

          <!-- Photos -->
          <div v-if="demande.photos && demande.photos.length > 0" class="card">
            <h2 class="card-title">Photos du signalement</h2>
            <div class="photos-grid">
              <a
                v-for="(photo, index) in demande.photos"
                :key="index"
                :href="getPhotoUrl(photo)"
                target="_blank"
                class="photo-thumb"
              >
                <img :src="getPhotoUrl(photo)" :alt="`Photo ${index + 1}`" />
              </a>
            </div>
          </div>

          <!-- Documents joints -->
          <div v-if="demande.documents && demande.documents.length > 0" class="card">
            <h2 class="card-title">Documents joints</h2>
            <div class="documents-list">
              <a
                v-for="(doc, index) in demande.documents"
                :key="'doc-' + index"
                :href="getPhotoUrl(doc)"
                target="_blank"
                class="document-item"
              >
                <span class="document-icon">📄</span>
                <span class="document-name">{{ doc.split('/').pop() }}</span>
              </a>
            </div>
          </div>

          <!-- Photos d'intervention -->
          <div v-if="demande.photos_intervention && demande.photos_intervention.length > 0" class="card card-intervention">
            <h2 class="card-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: #10b981">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              Photos d'intervention
            </h2>
            <p class="intervention-hint">Photos prises par l'agent terrain après intervention</p>
            <div class="photos-grid">
              <a
                v-for="(photo, index) in demande.photos_intervention"
                :key="'intervention-' + index"
                :href="photo"
                target="_blank"
                class="photo-thumb intervention-thumb"
              >
                <img :src="photo" :alt="`Photo intervention ${index + 1}`" />
              </a>
            </div>
          </div>

          <!-- Déclarant (anonymisé) -->
          <div class="card">
            <h2 class="card-title">Déclarant</h2>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">Prénom</span>
                <span class="info-value">{{ demande.declarant_prenom || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Nom</span>
                <span class="info-value">{{ demande.declarant_initial_nom ? demande.declarant_initial_nom + '...' : '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Email</span>
                <span class="info-value">{{ demande.declarant_email_masque || '-' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Colonne latérale -->
        <div class="side-column">
          <!-- Actions -->
          <div class="card actions-card">
            <h2 class="card-title">Actions</h2>

            <div class="action-buttons">
              <button
                v-if="['nouveau', 'en_moderation', 'envoye', 'accepte'].includes(demande.statut)"
                class="btn btn-primary btn-block"
                @click="takeCharge"
              >
                Prendre en charge
              </button>

              <button
                v-if="demande.statut === 'en_cours'"
                class="btn btn-secondary btn-block"
                @click="openPlanificationModal"
              >
                📅 Planifier intervention
              </button>

              <button
                v-if="demande.statut === 'planifie'"
                class="btn btn-info btn-block"
                @click="openStatutModal('en_cours')"
              >
                Reprendre en cours
              </button>

              <button
                v-if="['en_cours', 'planifie'].includes(demande.statut)"
                class="btn btn-success btn-block"
                @click="openStatutModal('traite')"
              >
                Marquer comme traité
              </button>

              <button
                class="btn btn-outline btn-block"
                @click="openAgentModal"
              >
                Assigner un agent
              </button>
            </div>
          </div>

          <!-- Suivi -->
          <div class="card">
            <h2 class="card-title">Suivi</h2>
            <div class="timeline">
              <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-content">
                  <span class="timeline-label">Créée le</span>
                  <span class="timeline-value">{{ formatDate(demande.created_at) }}</span>
                </div>
              </div>

              <div v-if="demande.date_prise_en_charge" class="timeline-item">
                <div class="timeline-dot active"></div>
                <div class="timeline-content">
                  <span class="timeline-label">Prise en charge</span>
                  <span class="timeline-value">{{ formatDate(demande.date_prise_en_charge) }}</span>
                </div>
              </div>

              <div v-if="demande.date_planification" class="timeline-item">
                <div class="timeline-dot planned"></div>
                <div class="timeline-content">
                  <span class="timeline-label">Intervention prévue</span>
                  <span class="timeline-value planned-date">{{ formatDate(demande.date_planification) }}</span>
                </div>
              </div>

              <div v-if="demande.date_resolution" class="timeline-item">
                <div class="timeline-dot success"></div>
                <div class="timeline-content">
                  <span class="timeline-label">Résolue le</span>
                  <span class="timeline-value">{{ formatDate(demande.date_resolution) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Agent assigné -->
          <div class="card">
            <h2 class="card-title">Agent assigné</h2>
            <div v-if="demande.agent_service_nom" class="agent-info">
              <div class="agent-avatar">
                {{ demande.agent_service_nom.charAt(0).toUpperCase() }}
              </div>
              <span>{{ demande.agent_service_nom }}</span>
            </div>
            <div v-else class="text-gray text-sm">
              Aucun agent assigné
            </div>
          </div>
        </div>

        <!-- Colonnes Tchat -->
        <aside class="chat-column chat-backoffice">
          <ChatSection
            :demande-id="demandeId"
            canal="backoffice"
            title="Back-office"
            subtitle="Communication avec le back-office"
            empty-text="Échangez avec le back-office"
          />
        </aside>

        <aside class="chat-column chat-terrain">
          <ChatSection
            :demande-id="demandeId"
            canal="terrain"
            title="Terrain"
            subtitle="Communication avec les agents terrain"
            empty-text="Échangez avec les agents terrain"
          />
        </aside>
      </div>
    </template>

    <!-- Modal changement statut -->
    <div v-if="showStatutModal" class="modal-overlay" @click.self="showStatutModal = false">
      <div class="modal">
        <h3>Changer le statut</h3>
        <p>Passer la demande au statut : <strong>{{ getStatutLabel(newStatut) }}</strong></p>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showStatutModal = false">Annuler</button>
          <button class="btn btn-primary" @click="confirmStatutChange">Confirmer</button>
        </div>
      </div>
    </div>

    <!-- Modal assignation agent -->
    <div v-if="showAgentModal" class="modal-overlay" @click.self="showAgentModal = false">
      <div class="modal">
        <h3>Assigner un agent</h3>
        <p>Sélectionnez l'agent responsable de cette demande</p>

        <div class="form-group">
          <label class="form-label">Agent</label>
          <select v-model="selectedAgentId" class="form-input">
            <option value="">-- Sélectionner --</option>
            <option v-for="agent in agents" :key="agent.id" :value="agent.id">
              {{ agent.nom }} {{ agent.prenom }}
            </option>
          </select>
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showAgentModal = false">Annuler</button>
          <button
            class="btn btn-primary"
            :disabled="!selectedAgentId"
            @click="assignAgent"
          >
            Assigner
          </button>
        </div>
      </div>
    </div>

    <!-- Modal planification -->
    <div v-if="showPlanificationModal" class="modal-overlay" @click.self="showPlanificationModal = false">
      <div class="modal">
        <h3>📅 Planifier l'intervention</h3>
        <p>Choisissez la date et l'heure de l'intervention</p>

        <div class="form-group">
          <label class="form-label">Date</label>
          <input
            v-model="datePlanification"
            type="date"
            class="form-input"
            :min="new Date().toISOString().split('T')[0]"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Heure</label>
          <input
            v-model="heurePlanification"
            type="time"
            class="form-input"
          />
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showPlanificationModal = false">Annuler</button>
          <button
            class="btn btn-primary"
            :disabled="!datePlanification"
            @click="confirmPlanification"
          >
            Planifier
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.demande-detail {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  color: var(--gray-600);
  cursor: pointer;
  font-size: 0.875rem;
}

.back-btn:hover {
  color: var(--primary);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-info h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--gray-800);
}

.badge-lg {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

/* Layout 4 colonnes */
.detail-content {
  display: grid;
  grid-template-columns: 1fr 280px 300px 300px;
  gap: 1rem;
}

@media (max-width: 1400px) {
  .detail-content {
    grid-template-columns: 1fr 260px 280px 280px;
  }
}

@media (max-width: 1200px) {
  .detail-content {
    grid-template-columns: 1fr 280px;
  }
  .chat-backoffice,
  .chat-terrain {
    grid-column: 1 / -1;
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .detail-content {
    grid-template-columns: 1fr;
  }
}

/* Chat columns */
.chat-column {
  position: sticky;
  top: 1.5rem;
  height: fit-content;
  max-height: calc(100vh - 180px);
}

.chat-backoffice :deep(.card) {
  border-left: 3px solid var(--primary);
}

.chat-terrain :deep(.card) {
  border-left: 3px solid #10b981;
}

.main-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.side-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Info grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  font-size: 0.75rem;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 0.875rem;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.category-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.description-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--gray-100);
}

.description-text {
  margin-top: 0.5rem;
  color: var(--gray-700);
  line-height: 1.6;
}

/* Photos */
.photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.photo-thumb {
  aspect-ratio: 1;
  border-radius: var(--radius);
  overflow: hidden;
}

.photo-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Documents */
.documents-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--gray-50);
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--gray-700);
  transition: background 0.15s;
}

.document-item:hover {
  background: var(--gray-100);
}

.document-icon {
  font-size: 1.25rem;
}

.document-name {
  font-size: 0.875rem;
  word-break: break-all;
}

/* Actions */
.actions-card {
  background: var(--gray-50);
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn-block {
  width: 100%;
}

/* Timeline */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.timeline-item {
  display: flex;
  gap: 0.75rem;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--gray-300);
  margin-top: 0.25rem;
}

.timeline-dot.active {
  background: var(--primary);
}

.timeline-dot.success {
  background: var(--success);
}

.timeline-dot.planned {
  background: #f59e0b;
}

.planned-date {
  color: #f59e0b;
  font-weight: 600;
}

.timeline-content {
  display: flex;
  flex-direction: column;
}

.timeline-label {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.timeline-value {
  font-size: 0.875rem;
  color: var(--gray-800);
}

/* Agent */
.agent-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.agent-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
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
  max-width: 400px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}

.modal h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.modal p {
  color: var(--gray-600);
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

/* Additional button styles */
.btn-info {
  background: #0ea5e9;
  color: white;
}

.btn-info:hover {
  background: #0284c7;
}

.btn-outline {
  background: white;
  color: var(--gray-700);
  border: 1px solid var(--gray-300);
}

.btn-outline:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 0.875rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--gray-700);
}

.form-group {
  margin-bottom: 1rem;
}

/* Photos d'intervention */
.card-intervention {
  border-left: 3px solid #10b981;
  background: linear-gradient(to right, #f0fdf4, white);
}

.card-intervention .card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #059669;
}

.intervention-hint {
  font-size: 0.75rem;
  color: var(--gray-500);
  margin-bottom: 0.75rem;
}

.intervention-thumb {
  border: 2px solid #10b981;
}
</style>

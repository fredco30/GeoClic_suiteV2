<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDemandesStore } from '../stores/demandes'
import MobileMap from '../components/MobileMap.vue'

const route = useRoute()
const router = useRouter()
const demandesStore = useDemandesStore()

const demandeId = computed(() => route.params.id as string)
const demande = computed(() => demandesStore.currentDemande)
const loading = computed(() => demandesStore.loading)
const messages = computed(() => demandesStore.messages)

// Tabs
const activeTab = ref<'info' | 'carte' | 'photos' | 'chat'>('info')

// Chat
const newMessage = ref('')
const chatContainer = ref<HTMLElement | null>(null)
const sendingMessage = ref(false)

// Status modal
const showStatutModal = ref(false)
const newStatut = ref('')

onMounted(async () => {
  await demandesStore.loadDemande(demandeId.value)
  await demandesStore.loadMessages(demandeId.value)
  await demandesStore.markMessagesRead(demandeId.value)
})

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

async function sendMessage() {
  if (!newMessage.value.trim() || sendingMessage.value) return

  sendingMessage.value = true
  const success = await demandesStore.sendMessage(demandeId.value, newMessage.value.trim())
  if (success) {
    newMessage.value = ''
    await nextTick()
    scrollToBottom()
  }
  sendingMessage.value = false
}

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function switchToChat() {
  activeTab.value = 'chat'
  nextTick(() => scrollToBottom())
}

function getStatutLabel(statut: string): string {
  const map: Record<string, string> = {
    nouveau: 'Nouveau',
    envoye: 'Envoyé',
    accepte: 'Accepté',
    en_cours: 'En cours',
    planifie: 'Planifié',
    traite: 'Traité',
    rejete: 'Rejeté',
  }
  return map[statut] || statut
}

function getStatutBadgeClass(statut: string): string {
  switch (statut) {
    case 'nouveau': return 'badge-info'
    case 'envoye': return 'badge-info'
    case 'accepte': return 'badge-warning'
    case 'en_cours': return 'badge-primary'
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

function formatMessageTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getPhotoUrl(photo: string): string {
  if (photo.startsWith('http')) return photo
  if (photo.startsWith('/api/')) return photo
  return `/api/photos/demandes/${photo}`
}

// Photo upload
const uploadingPhoto = ref(false)

async function takePhoto() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.capture = 'environment' // Caméra arrière

  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file || !demande.value) return

    uploadingPhoto.value = true
    try {
      // Compresser l'image avant upload
      const compressedFile = await compressImage(file)
      await demandesStore.uploadPhoto(demandeId.value, compressedFile)
    } catch (err) {
      console.error('Erreur upload photo:', err)
    } finally {
      uploadingPhoto.value = false
    }
  }

  input.click()
}

// Compression image
const MAX_WIDTH = 1280
const MAX_HEIGHT = 960
const JPEG_QUALITY = 0.85

async function compressImage(file: File): Promise<File> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      let { width, height } = img

      // Calculer les nouvelles dimensions
      if (width > MAX_WIDTH || height > MAX_HEIGHT) {
        const ratio = Math.min(MAX_WIDTH / width, MAX_HEIGHT / height)
        width = Math.round(width * ratio)
        height = Math.round(height * ratio)
      }

      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height

      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('Canvas context not available'))
        return
      }

      ctx.drawImage(img, 0, 0, width, height)

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Compression failed'))
            return
          }
          const compressedFile = new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), {
            type: 'image/jpeg',
            lastModified: Date.now(),
          })
          resolve(compressedFile)
        },
        'image/jpeg',
        JPEG_QUALITY
      )
    }
    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = URL.createObjectURL(file)
  })
}
</script>

<template>
  <div class="demande-detail">
    <!-- Header fixe -->
    <header class="detail-header">
      <button class="back-btn" @click="goBack">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
      </button>

      <div v-if="demande" class="header-content">
        <span class="demande-numero">{{ demande.numero || '#' }}</span>
        <span :class="['badge', getStatutBadgeClass(demande.statut)]">
          {{ getStatutLabel(demande.statut) }}
        </span>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading-screen">
      <div class="spinner"></div>
    </div>

    <!-- Contenu -->
    <template v-else-if="demande">
      <!-- Actions rapides -->
      <div class="quick-actions">
        <button
          v-if="['nouveau', 'envoye', 'accepte'].includes(demande.statut)"
          class="action-btn primary"
          @click="openStatutModal('en_cours')"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          Prendre en charge
        </button>

        <button
          v-if="demande.statut === 'en_cours'"
          class="action-btn secondary"
          @click="openStatutModal('planifie')"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          Planifier
        </button>

        <button
          v-if="['en_cours', 'planifie'].includes(demande.statut)"
          class="action-btn success"
          @click="openStatutModal('traite')"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Terminer
        </button>
      </div>

      <!-- Onglets -->
      <div class="tabs">
        <button
          :class="['tab', { active: activeTab === 'info' }]"
          @click="activeTab = 'info'"
        >
          Infos
        </button>
        <button
          v-if="demande.latitude && demande.longitude"
          :class="['tab', { active: activeTab === 'carte' }]"
          @click="activeTab = 'carte'"
        >
          Carte
        </button>
        <button
          :class="['tab', { active: activeTab === 'photos' }]"
          @click="activeTab = 'photos'"
        >
          Photos
          <span v-if="demande.photos?.length" class="tab-badge">{{ demande.photos.length }}</span>
        </button>
        <button
          :class="['tab', { active: activeTab === 'chat' }]"
          @click="switchToChat"
        >
          Tchat
          <span v-if="demande.unread_messages > 0" class="tab-badge unread">{{ demande.unread_messages }}</span>
        </button>
      </div>

      <!-- Tab Infos -->
      <div v-if="activeTab === 'info'" class="tab-content">
        <div class="info-card">
          <div v-if="demande.priorite === 'urgente'" class="priority-banner urgent">
            Priorité urgente
          </div>
          <div v-else-if="demande.priorite === 'haute'" class="priority-banner haute">
            Priorité haute
          </div>

          <div class="info-section">
            <span class="info-label">Description</span>
            <p class="description">{{ demande.description }}</p>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Catégorie</span>
              <span class="info-value">
                <span
                  v-if="demande.categorie_couleur"
                  class="cat-dot"
                  :style="{ backgroundColor: demande.categorie_couleur }"
                ></span>
                {{ demande.categorie_nom || '-' }}
              </span>
            </div>

            <div class="info-item">
              <span class="info-label">Quartier</span>
              <span class="info-value">{{ demande.quartier_nom || '-' }}</span>
            </div>

            <div class="info-item full-width">
              <span class="info-label">Adresse</span>
              <span class="info-value">{{ demande.adresse || '-' }}</span>
            </div>

            <div class="info-item">
              <span class="info-label">Créée le</span>
              <span class="info-value">{{ formatDate(demande.created_at) }}</span>
            </div>

            <div class="info-item">
              <span class="info-label">Agent</span>
              <span class="info-value">{{ demande.agent_service_nom || 'Non assigné' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Carte -->
      <div v-if="activeTab === 'carte'" class="tab-content map-tab">
        <MobileMap
          v-if="demande.latitude && demande.longitude"
          :latitude="demande.latitude"
          :longitude="demande.longitude"
          :adresse="demande.adresse"
        />
      </div>

      <!-- Tab Photos -->
      <div v-if="activeTab === 'photos'" class="tab-content photos-tab">
        <!-- Photos du signalement (citoyen) -->
        <div class="photos-section">
          <h3 class="photos-section-title">📸 Photos du signalement</h3>
          <div v-if="demande.photos && demande.photos.length > 0" class="photos-grid">
            <a
              v-for="(photo, index) in demande.photos"
              :key="'citoyen-' + index"
              :href="getPhotoUrl(photo)"
              target="_blank"
              class="photo-item"
            >
              <img :src="getPhotoUrl(photo)" :alt="`Photo ${index + 1}`" />
            </a>
          </div>
          <div v-else class="empty-photos-small">
            <p>Aucune photo du citoyen</p>
          </div>
        </div>

        <!-- Documents joints -->
        <div v-if="demande.documents && demande.documents.length > 0" class="photos-section">
          <h3 class="photos-section-title">📄 Documents joints</h3>
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

        <!-- Photos d'intervention (agent terrain) -->
        <div class="photos-section">
          <div class="photos-section-header">
            <h3 class="photos-section-title">🔧 Photos d'intervention</h3>
            <button
              class="take-photo-btn"
              @click="takePhoto"
              :disabled="uploadingPhoto"
            >
              <span v-if="uploadingPhoto" class="mini-spinner"></span>
              <span v-else>📷 Prendre une photo</span>
            </button>
          </div>
          <div v-if="demande.photos_intervention && demande.photos_intervention.length > 0" class="photos-grid">
            <a
              v-for="(photo, index) in demande.photos_intervention"
              :key="'intervention-' + index"
              :href="photo"
              target="_blank"
              class="photo-item intervention"
            >
              <img :src="photo" :alt="`Intervention ${index + 1}`" />
              <span class="photo-badge">🔧</span>
            </a>
          </div>
          <div v-else class="empty-photos-small">
            <p>Aucune photo d'intervention</p>
          </div>
        </div>
      </div>

      <!-- Tab Tchat -->
      <div v-if="activeTab === 'chat'" class="tab-content chat-tab">
        <div ref="chatContainer" class="messages-container">
          <div v-if="messages.length === 0" class="empty-chat">
            <p>Pas encore de messages</p>
          </div>

          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['message', msg.sender_type === 'terrain' ? 'sent' : 'received']"
          >
            <div class="message-bubble">
              <span v-if="msg.sender_type !== 'terrain'" class="sender-name">
                {{ msg.sender_nom || 'Services' }}
              </span>
              <p class="message-text">{{ msg.message }}</p>
              <span class="message-time">{{ formatMessageTime(msg.created_at) }}</span>
            </div>
          </div>
        </div>

        <div class="chat-input">
          <input
            v-model="newMessage"
            type="text"
            placeholder="Votre message..."
            @keyup.enter="sendMessage"
          />
          <button
            class="send-btn"
            :disabled="!newMessage.trim() || sendingMessage"
            @click="sendMessage"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>
    </template>

    <!-- Modal statut -->
    <div v-if="showStatutModal" class="modal-overlay" @click.self="showStatutModal = false">
      <div class="modal">
        <h3>Confirmer le changement</h3>
        <p>Passer au statut : <strong>{{ getStatutLabel(newStatut) }}</strong></p>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showStatutModal = false">Annuler</button>
          <button class="btn-confirm" @click="confirmStatutChange">Confirmer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.demande-detail {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 52px);
  min-height: calc(100dvh - 52px);
  background: var(--gray-50);
}

/* Header */
.detail-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: white;
  border-bottom: 1px solid var(--gray-200);
  position: sticky;
  top: 0;
  z-index: 10;
}

.back-btn {
  padding: 0.5rem;
  background: none;
  border: none;
  color: var(--gray-600);
  cursor: pointer;
  border-radius: 8px;
  -webkit-tap-highlight-color: transparent;
}

.back-btn:active {
  background: var(--gray-100);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.demande-numero {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--gray-800);
}

/* Badge */
.badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.badge-info { background: #dbeafe; color: #1d4ed8; }
.badge-primary { background: #dbeafe; color: #1d4ed8; }
.badge-warning { background: #fef3c7; color: #b45309; }
.badge-success { background: #dcfce7; color: #15803d; }
.badge-gray { background: var(--gray-100); color: var(--gray-600); }

/* Loading */
.loading-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--gray-200);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Actions rapides */
.quick-actions {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: white;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.action-btn:active {
  transform: scale(0.95);
}

.action-btn.primary {
  background: var(--primary);
  color: white;
}

.action-btn.secondary {
  background: #dbeafe;
  color: #1d4ed8;
}

.action-btn.success {
  background: #dcfce7;
  color: #15803d;
}

/* Tabs */
.tabs {
  display: flex;
  background: white;
  border-bottom: 1px solid var(--gray-200);
}

.tab {
  flex: 1;
  padding: 0.875rem;
  background: none;
  border: none;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--gray-500);
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  -webkit-tap-highlight-color: transparent;
}

.tab.active {
  color: var(--primary);
}

.tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 1rem;
  right: 1rem;
  height: 2px;
  background: var(--primary);
  border-radius: 2px 2px 0 0;
}

.tab-badge {
  background: var(--gray-200);
  color: var(--gray-600);
  font-size: 0.7rem;
  padding: 0.125rem 0.375rem;
  border-radius: 999px;
}

.tab-badge.unread {
  background: #ef4444;
  color: white;
}

/* Tab content */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

/* Info card */
.info-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.priority-banner {
  padding: 0.5rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
}

.priority-banner.urgent {
  background: #fef2f2;
  color: #ef4444;
}

.priority-banner.haute {
  background: #fef3c7;
  color: #b45309;
}

.info-section {
  padding: 1rem;
  border-bottom: 1px solid var(--gray-100);
}

.info-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--gray-400);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.description {
  font-size: 0.9rem;
  color: var(--gray-700);
  line-height: 1.5;
  margin: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-value {
  font-size: 0.875rem;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.cat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* Photos */
.photos-tab {
  padding: 0.5rem 1rem;
}

.photos-section {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.photos-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.photos-section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--gray-700);
  margin: 0 0 0.75rem 0;
}

.photos-section-header .photos-section-title {
  margin: 0;
}

.take-photo-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.take-photo-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.take-photo-btn:disabled {
  background: var(--gray-300);
}

.mini-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.photo-item {
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.photo-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-item.intervention {
  border: 2px solid var(--primary);
}

.photo-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: white;
  border-radius: 50%;
  padding: 2px 4px;
  font-size: 0.7rem;
}

.empty-photos {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--gray-400);
}

.empty-photos svg {
  margin-bottom: 0.5rem;
}

.empty-photos p {
  font-size: 0.9rem;
}

.empty-photos-small {
  text-align: center;
  padding: 1rem;
  color: var(--gray-400);
  font-size: 0.8rem;
}

/* Documents */
.documents-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--gray-50);
  border-radius: 8px;
  text-decoration: none;
  color: var(--gray-700);
}

.document-item:active {
  background: var(--gray-100);
}

.document-icon {
  font-size: 1.25rem;
}

.document-name {
  font-size: 0.85rem;
  word-break: break-all;
}

/* Map */
.map-tab {
  display: flex;
  flex-direction: column;
  padding: 0;
  height: calc(100vh - 220px);
  height: calc(100dvh - 220px);
}

/* Chat */
.chat-tab {
  display: flex;
  flex-direction: column;
  padding: 0;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.empty-chat {
  text-align: center;
  padding: 2rem;
  color: var(--gray-400);
  font-size: 0.9rem;
}

.message {
  display: flex;
  max-width: 80%;
}

.message.sent {
  align-self: flex-end;
}

.message.received {
  align-self: flex-start;
}

.message-bubble {
  padding: 0.75rem 1rem;
  border-radius: 16px;
  max-width: 100%;
}

.message.sent .message-bubble {
  background: var(--primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.received .message-bubble {
  background: white;
  color: var(--gray-800);
  border-bottom-left-radius: 4px;
}

.sender-name {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: var(--gray-500);
}

.message-text {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.4;
  word-break: break-word;
}

.message-time {
  display: block;
  font-size: 0.65rem;
  margin-top: 0.25rem;
  opacity: 0.7;
  text-align: right;
}

.message.received .message-time {
  color: var(--gray-400);
}

/* Chat input */
.chat-input {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: white;
  border-top: 1px solid var(--gray-200);
}

.chat-input input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid var(--gray-200);
  border-radius: 999px;
  font-size: 0.875rem;
  outline: none;
}

.chat-input input:focus {
  border-color: var(--primary);
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.send-btn:disabled {
  background: var(--gray-300);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.9);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  width: 100%;
  max-width: 400px;
}

.modal h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
}

.modal p {
  color: var(--gray-600);
  font-size: 0.9rem;
  margin: 0;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  padding: 0.875rem;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  -webkit-tap-highlight-color: transparent;
}

.btn-cancel {
  background: var(--gray-100);
  color: var(--gray-700);
}

.btn-confirm {
  background: var(--primary);
  color: white;
}

.btn-cancel:active,
.btn-confirm:active {
  transform: scale(0.98);
}
</style>

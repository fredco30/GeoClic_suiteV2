<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useDemandesStore } from '../stores/demandes'
import { useAuthStore } from '../stores/auth'

const props = withDefaults(defineProps<{
  demandeId: string
  canal?: 'backoffice' | 'terrain'
  title?: string
  subtitle?: string
  emptyText?: string
}>(), {
  canal: 'backoffice',
  title: 'Messages',
  subtitle: 'Communication avec le back-office',
  emptyText: 'Commencez la conversation avec le back-office'
})

const demandesStore = useDemandesStore()
const authStore = useAuthStore()

const newMessage = ref('')
const sending = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
let pollingInterval: number | null = null

const messages = computed(() =>
  props.canal === 'terrain' ? demandesStore.messagesTerrain : demandesStore.messages
)

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

// Cache pour les couleurs attribuées
const senderColorMap = new Map<string, typeof senderColors[0]>()

function getSenderColor(senderId: string | null, senderNom: string | null) {
  const key = senderId || senderNom || 'unknown'

  if (!senderColorMap.has(key)) {
    // Hash simple pour obtenir un index consistent
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

async function sendMessage() {
  if (!newMessage.value.trim() || sending.value) return

  sending.value = true
  const success = await demandesStore.sendMessage(props.demandeId, newMessage.value.trim(), props.canal)
  if (success) {
    newMessage.value = ''
    scrollToBottom()
  }
  sending.value = false
}

function scrollToBottom() {
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }, 100)
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return "Aujourd'hui"
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Hier'
  }
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })
}

// Grouper messages par date
function getMessageDate(dateStr: string): string {
  return new Date(dateStr).toDateString()
}

// Polling pour nouveaux messages
function startPolling() {
  pollingInterval = window.setInterval(async () => {
    await demandesStore.loadMessages(props.demandeId, props.canal)
  }, 30000) // 30 secondes
}

function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

onMounted(() => {
  scrollToBottom()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

watch(messages, () => {
  scrollToBottom()
}, { deep: true })
</script>

<template>
  <div class="chat-section card">
    <div class="chat-header">
      <h2 class="card-title">{{ title }}</h2>
      <span class="chat-info">{{ subtitle }}</span>
    </div>

    <div ref="messagesContainer" class="messages-container">
      <div v-if="messages.length === 0" class="no-messages">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z"/>
        </svg>
        <p>Aucun message</p>
        <span>{{ emptyText }}</span>
      </div>

      <template v-else>
        <template v-for="(message, index) in messages" :key="message.id">
          <!-- Séparateur de date -->
          <div
            v-if="index === 0 || getMessageDate(messages[index - 1].created_at) !== getMessageDate(message.created_at)"
            class="date-separator"
          >
            {{ formatDate(message.created_at) }}
          </div>

          <!-- Message -->
          <div
            :class="['message', message.sender_type === 'service' ? 'message-own' : 'message-other']"
            :style="message.sender_type !== 'service' ? {
              backgroundColor: getSenderColor(message.sender_id, message.sender_nom).bg,
              color: getSenderColor(message.sender_id, message.sender_nom).text
            } : {}"
          >
            <div class="message-header">
              <span
                class="message-sender"
                :style="message.sender_type !== 'service' ? {
                  color: getSenderColor(message.sender_id, message.sender_nom).name
                } : {}"
              >
                {{ message.sender_type === 'service' ? 'Vous' : message.sender_nom || (canal === 'terrain' ? 'Agent terrain' : 'Back-office') }}
              </span>
              <span class="message-time">{{ formatTime(message.created_at) }}</span>
            </div>
            <div class="message-content">
              {{ message.message }}
            </div>
          </div>
        </template>
      </template>
    </div>

    <form @submit.prevent="sendMessage" class="message-form">
      <input
        v-model="newMessage"
        type="text"
        class="form-input"
        placeholder="Tapez votre message..."
        :disabled="sending"
      />
      <button
        type="submit"
        class="btn btn-primary"
        :disabled="!newMessage.trim() || sending"
      >
        <svg v-if="!sending" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
        </svg>
        <span v-else class="spinner" style="width: 18px; height: 18px;"></span>
      </button>
    </form>
  </div>
</template>

<style scoped>
.chat-section {
  display: flex;
  flex-direction: column;
  min-height: 500px;
  max-height: calc(100vh - 200px);
  height: 100%;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--gray-200);
}

.chat-info {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0;
}

.no-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--gray-400);
  text-align: center;
}

.no-messages p {
  margin-top: 1rem;
  font-weight: 500;
  color: var(--gray-600);
}

.no-messages span {
  font-size: 0.875rem;
}

.date-separator {
  text-align: center;
  font-size: 0.75rem;
  color: var(--gray-500);
  margin: 1rem 0;
  position: relative;
}

.date-separator::before,
.date-separator::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 30%;
  height: 1px;
  background: var(--gray-200);
}

.date-separator::before {
  left: 0;
}

.date-separator::after {
  right: 0;
}

.message {
  max-width: 80%;
  margin-bottom: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 12px;
}

.message-own {
  margin-left: auto;
  background: var(--primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-other {
  margin-right: auto;
  background: var(--gray-100);
  border-bottom-left-radius: 4px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.25rem;
  font-size: 0.75rem;
}

.message-own .message-header {
  color: rgba(255, 255, 255, 0.8);
}

.message-other .message-header {
  color: var(--gray-500);
}

.message-sender {
  font-weight: 500;
}

.message-content {
  font-size: 0.875rem;
  line-height: 1.4;
  word-break: break-word;
}

.message-form {
  display: flex;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--gray-200);
}

.message-form .form-input {
  flex: 1;
}

.message-form .btn {
  padding: 0.5rem 1rem;
}
</style>

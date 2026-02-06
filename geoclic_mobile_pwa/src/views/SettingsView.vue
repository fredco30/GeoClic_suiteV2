<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'
import { offlineService } from '@/services/offline'

const router = useRouter()
const authStore = useAuthStore()

const serverUrl = ref(api.getServerUrl())
const showAdvancedServer = ref(false)
const testingConnection = ref(false)
const connectionStatus = ref<{ success: boolean; message: string } | null>(null)
const cacheStats = ref({
  points: 0,
  lexique: 0,
  projects: 0,
  pendingPoints: 0,
  pendingPhotos: 0
})

// Charger les stats du cache
const loadCacheStats = async () => {
  try {
    const stats = await offlineService.getStats()
    cacheStats.value = {
      points: stats.totalPoints,
      lexique: stats.lexiqueItems,
      projects: stats.projects,
      pendingPoints: stats.pendingPoints,
      pendingPhotos: stats.pendingPhotos
    }
  } catch (err) {
    console.error('Erreur chargement stats cache:', err)
  }
}

// Tester la connexion
const testConnection = async () => {
  testingConnection.value = true
  connectionStatus.value = null

  api.setServerUrl(serverUrl.value)
  const result = await api.testConnection()

  connectionStatus.value = result
  testingConnection.value = false
}

// Sauvegarder l'URL
const saveServerUrl = () => {
  api.setServerUrl(serverUrl.value)
  alert('URL du serveur enregistrée')
}

// Vider le cache
const clearCache = async () => {
  if (!confirm('Vider tout le cache local ? Les points non synchronisés seront perdus !')) {
    return
  }

  try {
    await offlineService.clearAll()
    await loadCacheStats()
    alert('Cache vidé avec succès')
  } catch (err) {
    console.error('Erreur vidage cache:', err)
    alert('Erreur lors du vidage du cache')
  }
}

// Déconnexion
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// Installer la PWA
const installPWA = async () => {
  const deferredPrompt = (window as unknown as { deferredPrompt?: BeforeInstallPromptEvent }).deferredPrompt

  if (deferredPrompt) {
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') {
      alert('Application installée !')
    }
  } else {
    alert('Pour installer l\'application:\n\n' +
      '• Sur iOS: Appuyez sur "Partager" puis "Sur l\'écran d\'accueil"\n' +
      '• Sur Android: Appuyez sur le menu (⋮) puis "Installer l\'application"')
  }
}

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

// Capturer l'événement d'installation
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    ;(window as unknown as { deferredPrompt?: BeforeInstallPromptEvent }).deferredPrompt = e as BeforeInstallPromptEvent
  })
}

onMounted(() => {
  loadCacheStats()
})
</script>

<template>
  <div class="settings-page page">
    <header class="settings-header">
      <button class="back-btn" @click="router.back()">
        ← Retour
      </button>
      <h1>Paramètres</h1>
    </header>

    <div class="settings-content">
      <!-- Profil -->
      <section class="settings-section">
        <h2>👤 Profil</h2>
        <div class="profile-card">
          <div class="profile-avatar">
            {{ authStore.userName.charAt(0).toUpperCase() }}
          </div>
          <div class="profile-info">
            <div class="profile-name">{{ authStore.userName }}</div>
            <div class="profile-email">{{ authStore.user?.email }}</div>
            <div class="profile-role">{{ authStore.userRole }}</div>
          </div>
        </div>
      </section>

      <!-- Serveur -->
      <section class="settings-section">
        <h2>🌐 Serveur</h2>

        <div class="server-info">
          <span class="server-label">Connecté à</span>
          <span class="server-url">{{ api.getAutoDetectedUrl() }}</span>
        </div>

        <div class="form-group" v-if="showAdvancedServer">
          <label class="form-label">URL personnalisée (optionnel)</label>
          <input
            v-model="serverUrl"
            type="url"
            class="form-input"
            placeholder="Laisser vide pour utiliser le serveur actuel"
          />
          <div class="btn-group">
            <button
              class="btn btn-secondary"
              :disabled="testingConnection"
              @click="testConnection"
            >
              {{ testingConnection ? 'Test...' : 'Tester' }}
            </button>
            <button class="btn btn-primary" @click="saveServerUrl">
              Enregistrer
            </button>
          </div>
        </div>

        <button class="btn-link" @click="showAdvancedServer = !showAdvancedServer">
          {{ showAdvancedServer ? 'Masquer les options avancées' : 'Options avancées' }}
        </button>

        <div
          v-if="connectionStatus"
          class="connection-result"
          :class="{ success: connectionStatus.success, error: !connectionStatus.success }"
        >
          {{ connectionStatus.success ? '✓' : '✕' }} {{ connectionStatus.message }}
        </div>
      </section>

      <!-- Cache -->
      <section class="settings-section">
        <h2>💾 Données locales</h2>

        <div class="cache-stats">
          <div class="cache-stat">
            <span>Points en cache</span>
            <strong>{{ cacheStats.points }}</strong>
          </div>
          <div class="cache-stat">
            <span>Catégories</span>
            <strong>{{ cacheStats.lexique }}</strong>
          </div>
          <div class="cache-stat">
            <span>Projets</span>
            <strong>{{ cacheStats.projects }}</strong>
          </div>
          <div class="cache-stat warning" v-if="cacheStats.pendingPoints > 0">
            <span>Points en attente</span>
            <strong>{{ cacheStats.pendingPoints }}</strong>
          </div>
          <div class="cache-stat warning" v-if="cacheStats.pendingPhotos > 0">
            <span>Photos en attente</span>
            <strong>{{ cacheStats.pendingPhotos }}</strong>
          </div>
        </div>

        <button class="btn btn-danger btn-block" @click="clearCache">
          🗑️ Vider le cache
        </button>
      </section>

      <!-- Installation -->
      <section class="settings-section">
        <h2>📲 Installation</h2>
        <p class="section-description">
          Installez Geoclic Mobile sur votre écran d'accueil pour un accès rapide.
        </p>
        <button class="btn btn-primary btn-block" @click="installPWA">
          Installer l'application
        </button>
      </section>

      <!-- À propos -->
      <section class="settings-section">
        <h2>ℹ️ À propos</h2>
        <div class="about-info">
          <div class="about-row">
            <span>Application</span>
            <span>Geoclic Mobile PWA</span>
          </div>
          <div class="about-row">
            <span>Version</span>
            <span>1.0.0</span>
          </div>
          <div class="about-row">
            <span>Type</span>
            <span>Progressive Web App</span>
          </div>
        </div>
      </section>

      <!-- Déconnexion -->
      <button class="btn btn-secondary btn-block logout-btn" @click="handleLogout">
        🚪 Se déconnecter
      </button>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  background: var(--background-color);
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  padding-top: calc(env(safe-area-inset-top, 12px) + 12px);
  background: var(--primary-color);
  color: white;
}

.back-btn {
  background: none;
  border: none;
  color: white;
  font-size: 16px;
  cursor: pointer;
  padding: 8px;
  margin: -8px;
}

.settings-header h1 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.settings-content {
  padding: 16px;
}

.settings-section {
  background: var(--surface-color);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}

.settings-section h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
}

.section-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 16px;
}

/* Profile */
.profile-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.profile-avatar {
  width: 60px;
  height: 60px;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 600;
}

.profile-name {
  font-size: 18px;
  font-weight: 600;
}

.profile-email {
  font-size: 14px;
  color: var(--text-secondary);
}

.profile-role {
  font-size: 13px;
  color: var(--primary-color);
  text-transform: capitalize;
  margin-top: 2px;
}

/* Server info */
.server-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.server-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.server-url {
  font-size: 14px;
  font-weight: 500;
  color: var(--primary-color);
  word-break: break-all;
}

.btn-link {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 13px;
  padding: 8px 0;
  cursor: pointer;
  text-decoration: underline;
}

/* Buttons */
.btn-group {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.btn-group .btn {
  flex: 1;
}

.connection-result {
  margin-top: 12px;
  padding: 12px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  text-align: center;
}

.connection-result.success {
  background: rgba(76, 175, 80, 0.1);
  color: var(--success-color);
}

.connection-result.error {
  background: rgba(244, 67, 54, 0.1);
  color: var(--error-color);
}

/* Cache stats */
.cache-stats {
  margin-bottom: 16px;
}

.cache-stat {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 14px;
}

.cache-stat:last-child {
  border-bottom: none;
}

.cache-stat.warning {
  color: var(--warning-color);
}

.cache-stat strong {
  font-weight: 600;
}

/* About */
.about-info {
  font-size: 14px;
}

.about-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.about-row:last-child {
  border-bottom: none;
}

.logout-btn {
  margin-top: 8px;
}
</style>

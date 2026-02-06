<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const showServerConfig = ref(false)
const serverUrl = ref(api.getServerUrl())
const testingConnection = ref(false)
const connectionStatus = ref<{ success: boolean; message: string } | null>(null)

// Tenter la connexion
const handleLogin = async () => {
  if (!email.value || !password.value) {
    return
  }

  const success = await authStore.login(email.value, password.value)
  if (success) {
    router.push('/')
  }
}

// Tester la connexion au serveur
const testConnection = async () => {
  testingConnection.value = true
  connectionStatus.value = null

  // Sauvegarder d'abord l'URL
  api.setServerUrl(serverUrl.value)

  const result = await api.testConnection()
  connectionStatus.value = result
  testingConnection.value = false
}

// Sauvegarder l'URL du serveur
const saveServerUrl = () => {
  api.setServerUrl(serverUrl.value)
  showServerConfig.value = false
  connectionStatus.value = null
}

// Restaurer la session si disponible
onMounted(() => {
  if (authStore.restoreSession()) {
    router.push('/')
  }
})
</script>

<template>
  <div class="login-page">
    <div class="login-header">
      <div class="logo">📍</div>
      <h1>Geoclic Mobile</h1>
      <p>Collecte terrain géolocalisée</p>
    </div>

    <div class="login-form">
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input
            v-model="email"
            type="email"
            class="form-input"
            placeholder="votre@email.fr"
            autocomplete="email"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">Mot de passe</label>
          <div class="password-input">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              placeholder="••••••••"
              autocomplete="current-password"
              required
            />
            <button
              type="button"
              class="toggle-password"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? '🙈' : '👁️' }}
            </button>
          </div>
        </div>

        <div v-if="authStore.error" class="error-message">
          {{ authStore.error }}
        </div>

        <button
          type="submit"
          class="btn btn-primary btn-block login-btn"
          :disabled="authStore.isLoading || !email || !password"
        >
          <span v-if="authStore.isLoading" class="spinner"></span>
          <span v-else>Se connecter</span>
        </button>
      </form>

      <button class="server-config-btn" @click="showServerConfig = !showServerConfig">
        ⚙️ Configurer le serveur
      </button>

      <!-- Configuration serveur -->
      <div v-if="showServerConfig" class="server-config">
        <div class="form-group">
          <label class="form-label">URL du serveur</label>
          <input
            v-model="serverUrl"
            type="text"
            class="form-input"
            placeholder="Laisser vide pour proxy automatique"
          />
          <div class="input-hint">
            Vide = proxy automatique (via ngrok) | Ou: https://monserveur.fr:8443
          </div>
        </div>

        <div class="server-actions">
          <button
            type="button"
            class="btn btn-secondary"
            :disabled="testingConnection"
            @click="testConnection"
          >
            <span v-if="testingConnection" class="spinner small"></span>
            <span v-else>Tester</span>
          </button>
          <button
            type="button"
            class="btn btn-primary"
            @click="saveServerUrl"
          >
            Enregistrer
          </button>
        </div>

        <div
          v-if="connectionStatus"
          class="connection-status"
          :class="{ success: connectionStatus.success, error: !connectionStatus.success }"
        >
          {{ connectionStatus.success ? '✓' : '✕' }} {{ connectionStatus.message }}
        </div>
      </div>
    </div>

    <div class="login-footer">
      <p>Version PWA 1.0</p>
      <p class="https-notice">
        🔒 HTTPS requis pour le GPS
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
  padding: 20px;
  padding-top: calc(env(safe-area-inset-top, 20px) + 40px);
}

.login-header {
  text-align: center;
  color: white;
  margin-bottom: 40px;
}

.logo {
  width: 80px;
  height: 80px;
  background: white;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  margin: 0 auto 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
}

.login-header p {
  margin: 8px 0 0;
  opacity: 0.9;
}

.login-form {
  background: white;
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow-lg);
}

.password-input {
  position: relative;
}

.password-input .form-input {
  padding-right: 50px;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
}

.error-message {
  background: rgba(244, 67, 54, 0.1);
  color: var(--error-color);
  padding: 12px;
  border-radius: var(--radius-sm);
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
}

.login-btn {
  height: 50px;
  font-size: 17px;
}

.server-config-btn {
  display: block;
  width: 100%;
  margin-top: 16px;
  padding: 12px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  text-align: center;
}

.server-config {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.input-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 6px;
}

.server-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.server-actions .btn {
  flex: 1;
}

.connection-status {
  margin-top: 12px;
  padding: 10px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  text-align: center;
}

.connection-status.success {
  background: rgba(76, 175, 80, 0.1);
  color: var(--success-color);
}

.connection-status.error {
  background: rgba(244, 67, 54, 0.1);
  color: var(--error-color);
}

.login-footer {
  margin-top: auto;
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  padding: 20px 0;
}

.login-footer p {
  margin: 4px 0;
}

.https-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner.small {
  width: 16px;
  height: 16px;
  border-color: var(--border-color);
  border-top-color: var(--primary-color);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

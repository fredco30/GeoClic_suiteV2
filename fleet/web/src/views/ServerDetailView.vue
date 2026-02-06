<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const props = defineProps<{ name: string }>()
const router = useRouter()

const server = ref<any>(null)
const loading = ref(true)
const logs = ref('')
const logsService = ref('api')
const logsLoading = ref(false)
const actionLoading = ref('')
const taskId = ref('')
const taskStatus = ref<any>(null)
const taskLog = ref('')
let pollInterval: ReturnType<typeof setInterval>

async function loadServer() {
  loading.value = true
  try {
    server.value = await api.serverStatus(props.name)
  } catch (e: any) {
    // Fallback: get from list
    try {
      const data = await api.listServers()
      server.value = data.servers.find((s: any) => s.name === props.name)
    } catch {
      server.value = null
    }
  } finally {
    loading.value = false
  }
}

async function loadLogs() {
  logsLoading.value = true
  try {
    const data = await api.serverLogs(props.name, logsService.value)
    logs.value = data.logs
  } catch (e: any) {
    logs.value = `Erreur: ${e.message}`
  } finally {
    logsLoading.value = false
  }
}

async function doUpdate() {
  if (!confirm(`Mettre à jour ${props.name} ?`)) return
  actionLoading.value = 'update'
  try {
    const result = await api.updateServer(props.name)
    taskId.value = result.task_id
    startPolling()
  } catch (e: any) {
    alert(`Erreur: ${e.message}`)
    actionLoading.value = ''
  }
}

async function doBackup() {
  actionLoading.value = 'backup'
  try {
    const result = await api.backupServer(props.name)
    taskId.value = result.task_id
    startPolling()
  } catch (e: any) {
    alert(`Erreur: ${e.message}`)
    actionLoading.value = ''
  }
}

async function doRemove() {
  if (!confirm(`Retirer ${props.name} du registre ? Le serveur ne sera PAS supprimé, juste retiré de la liste.`)) return
  try {
    await api.removeServer(props.name)
    router.push('/')
  } catch (e: any) {
    alert(`Erreur: ${e.message}`)
  }
}

function startPolling() {
  pollInterval = setInterval(async () => {
    try {
      const status = await api.getTask(taskId.value)
      taskStatus.value = status

      const logData = await api.getTaskLog(taskId.value)
      taskLog.value = logData.log

      if (status.status === 'completed' || status.status === 'failed') {
        clearInterval(pollInterval)
        actionLoading.value = ''
        loadServer() // Refresh
      }
    } catch {
      // Ignore
    }
  }, 3000)
}

onMounted(() => {
  loadServer()
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

const services = ['api', 'db', 'nginx', 'admin', 'portail', 'demandes', 'mobile', 'sig', 'services', 'terrain']
</script>

<template>
  <div class="server-detail">
    <div class="page-header">
      <div>
        <router-link to="/" class="back-link">&larr; Dashboard</router-link>
        <h1>{{ name }}</h1>
        <p v-if="server" class="subtitle">
          <a :href="`https://${server.domain}`" target="_blank">{{ server.domain }}</a>
          &mdash; {{ server.ip }}
        </p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" :disabled="!!actionLoading" @click="doBackup">
          {{ actionLoading === 'backup' ? 'Sauvegarde...' : 'Sauvegarder' }}
        </button>
        <button class="btn btn-primary" :disabled="!!actionLoading" @click="doUpdate">
          {{ actionLoading === 'update' ? 'Mise à jour...' : 'Mettre à jour' }}
        </button>
        <button class="btn btn-danger btn-sm" @click="doRemove">Retirer</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Vérification du serveur...</p>
    </div>

    <template v-else-if="server">
      <!-- Status cards -->
      <div class="status-grid">
        <div class="status-card">
          <div class="status-label">API</div>
          <div class="status-value">
            <span class="badge" :class="server.health_http === '200' ? 'badge-ok' : 'badge-error'">
              {{ server.health_http === '200' ? 'En ligne' : `HTTP ${server.health_http || '???'}` }}
            </span>
          </div>
        </div>
        <div class="status-card">
          <div class="status-label">SSH</div>
          <div class="status-value">
            <span class="badge" :class="server.ssh_ok ? 'badge-ok' : 'badge-error'">
              {{ server.ssh_ok ? 'Accessible' : 'Inaccessible' }}
            </span>
          </div>
        </div>
        <div class="status-card">
          <div class="status-label">SSL</div>
          <div class="status-value">
            <span v-if="server.ssl_expiry" class="badge badge-ok">{{ server.ssl_expiry }}</span>
            <span v-else class="badge badge-warn">Non vérifié</span>
          </div>
        </div>
        <div class="status-card">
          <div class="status-label">Ajouté le</div>
          <div class="status-value">{{ server.date_ajout || '—' }}</div>
        </div>
      </div>

      <!-- Task progress -->
      <div v-if="taskId" class="card task-section">
        <h3>
          {{ taskStatus?.status === 'completed' ? 'Opération terminée' :
             taskStatus?.status === 'failed' ? 'Opération échouée' :
             'Opération en cours...' }}
        </h3>
        <div v-if="taskStatus" class="task-info">
          <span class="badge" :class="{
            'badge-ok': taskStatus.status === 'completed',
            'badge-error': taskStatus.status === 'failed',
            'badge-warn': taskStatus.status === 'running',
          }">
            {{ taskStatus.label || taskStatus.status }}
          </span>
          <span v-if="taskStatus.step && taskStatus.total">
            Étape {{ taskStatus.step }}/{{ taskStatus.total }}
          </span>
        </div>
        <div class="log-box" v-if="taskLog">
          <pre>{{ taskLog }}</pre>
        </div>
      </div>

      <!-- Logs -->
      <div class="card logs-section">
        <div class="logs-header">
          <h3>Logs Docker</h3>
          <div class="logs-controls">
            <select v-model="logsService" class="input logs-select">
              <option v-for="svc in services" :key="svc" :value="svc">{{ svc }}</option>
            </select>
            <button class="btn btn-sm btn-outline" :disabled="logsLoading" @click="loadLogs">
              {{ logsLoading ? 'Chargement...' : 'Charger' }}
            </button>
          </div>
        </div>
        <div v-if="logs" class="log-box">
          <pre>{{ logs }}</pre>
        </div>
        <p v-else class="logs-empty">Cliquez "Charger" pour voir les logs du service sélectionné.</p>
      </div>
    </template>

    <div v-else class="card error-state">
      <p>Serveur non trouvé</p>
      <router-link to="/" class="btn btn-primary">Retour</router-link>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.back-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
}

.back-link:hover {
  color: var(--primary);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  margin-top: 4px;
}

.subtitle a {
  color: var(--primary-light);
  text-decoration: none;
}

.subtitle a:hover {
  text-decoration: underline;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.loading-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.status-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.status-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.status-value {
  font-size: 14px;
  font-weight: 500;
}

.task-section {
  margin-bottom: 20px;
}

.task-section h3 {
  font-size: 16px;
  margin-bottom: 12px;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 14px;
}

.logs-section {
  margin-bottom: 20px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.logs-header h3 {
  font-size: 16px;
}

.logs-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.logs-select {
  width: 140px;
  padding: 6px 10px;
}

.logs-empty {
  color: var(--text-secondary);
  font-size: 14px;
  font-style: italic;
}

.log-box {
  background: #1a1a2e;
  color: #a4e400;
  border-radius: 6px;
  padding: 16px;
  max-height: 400px;
  overflow: auto;
  font-family: 'Fira Code', 'Consolas', monospace;
}

.log-box pre {
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.error-state {
  text-align: center;
  padding: 40px;
}
</style>

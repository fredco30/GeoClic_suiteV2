<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { api } from '../services/api'

interface Server {
  name: string
  domain: string
  ip: string
  ssh_user?: string
  ssh_port?: number
  date_ajout?: string
  health_http?: string
  ssl_expiry?: string
  ssh_ok?: boolean
}

const servers = ref<Server[]>([])
const loading = ref(true)
const refreshing = ref(false)
const error = ref('')
const sshKey = ref('')
const showSshKey = ref(false)
let interval: ReturnType<typeof setInterval>

const onlineCount = computed(() => servers.value.filter(s => s.health_http === '200').length)
const offlineCount = computed(() => servers.value.length - onlineCount.value)

async function loadServers() {
  try {
    const data = await api.listServers()
    servers.value = data.servers
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadSshKey() {
  try {
    const data = await api.getSshKey()
    sshKey.value = data.public_key
  } catch { /* ignore */ }
}

function copySshKey() {
  navigator.clipboard.writeText(sshKey.value)
  alert('Clé SSH copiée !')
}

async function refreshStatus() {
  refreshing.value = true
  try {
    const data = await api.serversStatus()
    servers.value = data.servers
  } catch (e: any) {
    error.value = e.message
  } finally {
    refreshing.value = false
  }
}

async function updateAll() {
  if (!confirm('Mettre à jour TOUS les serveurs ? Cette opération peut prendre plusieurs minutes.')) return
  try {
    const result = await api.updateAllServers()
    alert(`Mise à jour lancée ! ID: ${result.task_id}`)
  } catch (e: any) {
    alert(`Erreur: ${e.message}`)
  }
}

onMounted(() => {
  loadServers()
  loadSshKey()
  // Auto-refresh toutes les 60 secondes
  interval = setInterval(() => {
    if (!refreshing.value) refreshStatus()
  }, 60000)
})

onUnmounted(() => {
  clearInterval(interval)
})

function getStatusIcon(server: Server): string {
  if (!server.health_http) return '?'
  return server.health_http === '200' ? '🟢' : '🔴'
}

function getStatusClass(server: Server): string {
  if (!server.health_http) return ''
  return server.health_http === '200' ? 'badge-ok' : 'badge-error'
}
</script>

<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h1>Tableau de bord</h1>
        <p class="subtitle">Vue d'ensemble de vos serveurs GéoClic</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" :disabled="refreshing" @click="refreshStatus">
          {{ refreshing ? 'Actualisation...' : 'Actualiser' }}
        </button>
        <button v-if="servers.length > 1" class="btn btn-primary" @click="updateAll">
          Tout mettre à jour
        </button>
        <router-link to="/add" class="btn btn-accent">
          + Nouveau serveur
        </router-link>
      </div>
    </div>

    <!-- KPI -->
    <div class="kpi-row" v-if="!loading">
      <div class="kpi-card">
        <div class="kpi-value">{{ servers.length }}</div>
        <div class="kpi-label">Serveurs</div>
      </div>
      <div class="kpi-card kpi-ok">
        <div class="kpi-value">{{ onlineCount }}</div>
        <div class="kpi-label">En ligne</div>
      </div>
      <div class="kpi-card kpi-error" v-if="offlineCount > 0">
        <div class="kpi-value">{{ offlineCount }}</div>
        <div class="kpi-label">Hors ligne</div>
      </div>
    </div>

    <!-- Clé SSH Fleet -->
    <div v-if="sshKey" class="ssh-key-card card">
      <div class="ssh-key-header" @click="showSshKey = !showSshKey">
        <span>🔑 Clé SSH Fleet</span>
        <span class="chevron">{{ showSshKey ? '▼' : '▶' }}</span>
      </div>
      <div v-show="showSshKey" class="ssh-key-content">
        <p class="ssh-key-info">Cette clé doit être ajoutée sur chaque nouveau VPS pour permettre la connexion.</p>
        <code class="ssh-key-value">{{ sshKey }}</code>
        <button class="btn btn-outline btn-sm" @click="copySshKey">Copier la clé</button>
      </div>
    </div>

    <!-- Chargement -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Chargement des serveurs...</p>
    </div>

    <!-- Erreur -->
    <div v-else-if="error" class="error-state card">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadServers">Réessayer</button>
    </div>

    <!-- Aucun serveur -->
    <div v-else-if="servers.length === 0" class="empty-state card">
      <div class="empty-icon">🖥️</div>
      <h2>Aucun serveur enregistré</h2>
      <p>Ajoutez votre premier serveur client pour commencer.</p>
      <router-link to="/add" class="btn btn-accent">+ Ajouter un serveur</router-link>
    </div>

    <!-- Liste des serveurs -->
    <div v-else class="servers-grid">
      <router-link
        v-for="server in servers"
        :key="server.name"
        :to="`/server/${server.name}`"
        class="server-card card"
      >
        <div class="server-header">
          <span class="server-status">{{ getStatusIcon(server) }}</span>
          <div class="server-info">
            <h3>{{ server.name }}</h3>
            <a
              :href="`https://${server.domain}`"
              class="server-domain"
              target="_blank"
              @click.stop
            >
              {{ server.domain }}
            </a>
          </div>
          <span
            v-if="server.health_http"
            class="badge"
            :class="getStatusClass(server)"
          >
            HTTP {{ server.health_http }}
          </span>
        </div>
        <div class="server-details">
          <div class="detail">
            <span class="detail-label">IP</span>
            <span>{{ server.ip }}</span>
          </div>
          <div class="detail" v-if="server.ssh_ok !== undefined">
            <span class="detail-label">SSH</span>
            <span>{{ server.ssh_ok ? 'OK' : 'Inaccessible' }}</span>
          </div>
          <div class="detail" v-if="server.ssl_expiry">
            <span class="detail-label">SSL expire</span>
            <span>{{ server.ssl_expiry }}</span>
          </div>
          <div class="detail" v-if="server.date_ajout">
            <span class="detail-label">Ajouté le</span>
            <span>{{ server.date_ajout }}</span>
          </div>
        </div>
      </router-link>
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

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 4px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.kpi-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 24px;
  flex: 1;
  max-width: 180px;
}

.kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--primary);
}

.kpi-ok .kpi-value { color: #2e7d32; }
.kpi-error .kpi-value { color: var(--danger); }

.kpi-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
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

.error-state {
  text-align: center;
  padding: 40px;
  color: var(--danger);
}

.empty-state {
  text-align: center;
  padding: 60px 40px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h2 {
  font-size: 20px;
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.servers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.server-card {
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
  cursor: pointer;
}

.server-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(26, 35, 126, 0.1);
  transform: translateY(-1px);
}

.server-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.server-status {
  font-size: 20px;
}

.server-info {
  flex: 1;
}

.server-info h3 {
  font-size: 16px;
  font-weight: 600;
}

.server-domain {
  color: var(--primary-light);
  font-size: 13px;
  text-decoration: none;
}

.server-domain:hover {
  text-decoration: underline;
}

.server-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail span:last-child {
  font-size: 13px;
}

.ssh-key-card {
  margin-bottom: 24px;
  background: #fafbff;
  border: 1px solid #c5cae9;
}

.ssh-key-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
}

.ssh-key-header:hover { color: var(--primary); }

.ssh-key-content {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.ssh-key-info {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.ssh-key-value {
  display: block;
  background: #1a1a2e;
  color: #a4e400;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 12px;
  word-break: break-all;
  margin-bottom: 10px;
  line-height: 1.4;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

.chevron {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePointsStore } from '@/stores/points'
import { offlineService } from '@/services/offline'
import type { GeometryType } from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const pointsStore = usePointsStore()

const stats = ref({
  totalPoints: 0,
  pendingPoints: 0,
  pendingPhotos: 0,
  lastSync: ''
})

const isOnline = computed(() => pointsStore.isOnline)

// Menu de création de géométrie
const showCreateMenu = ref(false)

const openCreateMenu = () => {
  showCreateMenu.value = true
}

const closeCreateMenu = () => {
  showCreateMenu.value = false
}

const createGeometry = (type: GeometryType) => {
  closeCreateMenu()
  router.push({ name: 'geometry-new', query: { type } })
}

// Charger les statistiques
const loadStats = async () => {
  try {
    await offlineService.init()
    const offlineStats = await offlineService.getStats()
    stats.value = {
      totalPoints: offlineStats.totalPoints,
      pendingPoints: offlineStats.pendingPoints,
      pendingPhotos: offlineStats.pendingPhotos,
      lastSync: offlineStats.lastSync || 'Jamais'
    }
  } catch (err) {
    console.error('Erreur chargement stats:', err)
  }
}

// Actions rapides
const quickActions = [
  {
    icon: '➕',
    label: 'Nouveau',
    color: '#4CAF50',
    action: openCreateMenu
  },
  {
    icon: '📋',
    label: 'Mes points',
    color: '#2196F3',
    action: () => router.push('/points')
  },
  {
    icon: '🗺️',
    label: 'Carte',
    color: '#FF9800',
    action: () => router.push('/map')
  },
  {
    icon: '🔄',
    label: 'Synchroniser',
    color: '#9C27B0',
    action: () => router.push('/sync')
  }
]

// Déconnexion
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// Formater la date de dernière sync
const formatLastSync = (dateStr: string) => {
  if (!dateStr || dateStr === 'Jamais') return 'Jamais'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

onMounted(async () => {
  await loadStats()
  await pointsStore.initOffline()
  await pointsStore.loadReferenceData()
})
</script>

<template>
  <div class="home-page page">
    <!-- Header -->
    <div class="page-header home-header">
      <div class="header-content">
        <div class="user-info">
          <div class="user-avatar">
            {{ authStore.userName.charAt(0).toUpperCase() }}
          </div>
          <div class="user-details">
            <div class="user-name">{{ authStore.userName }}</div>
            <div class="user-role">{{ authStore.userRole }}</div>
          </div>
        </div>
        <button class="settings-btn" @click="router.push('/settings')">
          ⚙️
        </button>
      </div>

      <!-- Status en ligne -->
      <div class="connection-status" :class="{ online: isOnline, offline: !isOnline }">
        <span class="status-dot"></span>
        {{ isOnline ? 'En ligne' : 'Hors ligne' }}
      </div>
    </div>

    <div class="page-content">
      <!-- Statistiques -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ stats.totalPoints }}</div>
          <div class="stat-label">Points en cache</div>
        </div>
        <div class="stat-card" :class="{ highlight: stats.pendingPoints > 0 }">
          <div class="stat-value">{{ stats.pendingPoints }}</div>
          <div class="stat-label">En attente</div>
        </div>
        <div class="stat-card" :class="{ highlight: stats.pendingPhotos > 0 }">
          <div class="stat-value">{{ stats.pendingPhotos }}</div>
          <div class="stat-label">Photos à envoyer</div>
        </div>
        <div class="stat-card">
          <div class="stat-value sync-date">{{ formatLastSync(stats.lastSync) }}</div>
          <div class="stat-label">Dernière sync</div>
        </div>
      </div>

      <!-- Actions rapides -->
      <h2 class="section-title">Actions rapides</h2>
      <div class="actions-grid">
        <button
          v-for="action in quickActions"
          :key="action.label"
          class="action-card"
          @click="action.action"
        >
          <span class="action-icon" :style="{ background: action.color }">
            {{ action.icon }}
          </span>
          <span class="action-label">{{ action.label }}</span>
        </button>
      </div>

      <!-- Alerte si éléments en attente -->
      <div v-if="stats.pendingPoints > 0 || stats.pendingPhotos > 0" class="sync-alert">
        <div class="alert-icon">⚠️</div>
        <div class="alert-content">
          <div class="alert-title">Éléments à synchroniser</div>
          <div class="alert-text">
            {{ stats.pendingPoints }} point(s) et {{ stats.pendingPhotos }} photo(s)
            en attente d'envoi.
          </div>
        </div>
        <button class="btn btn-primary btn-sm" @click="router.push('/sync')">
          Sync
        </button>
      </div>

      <!-- Déconnexion -->
      <button class="logout-btn" @click="handleLogout">
        🚪 Se déconnecter
      </button>
    </div>

    <!-- Menu de création de géométrie -->
    <Teleport to="body">
      <div v-if="showCreateMenu" class="create-menu-overlay" @click.self="closeCreateMenu">
        <div class="create-menu">
          <h3>Créer un élément</h3>
          <button class="menu-item" @click="createGeometry('POINT')">
            <span class="menu-icon point-icon">📍</span>
            <div class="menu-text">
              <span class="menu-label">Point</span>
              <span class="menu-desc">Un seul emplacement GPS</span>
            </div>
          </button>
          <button class="menu-item" @click="createGeometry('LINESTRING')">
            <span class="menu-icon line-icon">📏</span>
            <div class="menu-text">
              <span class="menu-label">Ligne</span>
              <span class="menu-desc">Tracé linéaire (chemin, réseau...)</span>
            </div>
          </button>
          <button class="menu-item" @click="createGeometry('POLYGON')">
            <span class="menu-icon polygon-icon">⬛</span>
            <div class="menu-text">
              <span class="menu-label">Zone</span>
              <span class="menu-desc">Surface fermée (parcelle, espace...)</span>
            </div>
          </button>
          <button class="cancel-btn" @click="closeCreateMenu">Annuler</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.home-page {
  background: var(--background-color);
}

.home-header {
  padding-bottom: 20px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
}

.user-name {
  font-size: 18px;
  font-weight: 600;
}

.user-role {
  font-size: 13px;
  opacity: 0.8;
  text-transform: capitalize;
}

.settings-btn {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
}

.connection-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.connection-status.online {
  background: rgba(76, 175, 80, 0.2);
}

.connection-status.offline {
  background: rgba(255, 152, 0, 0.2);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.online .status-dot {
  background: #4CAF50;
}

.offline .status-dot {
  background: #FF9800;
  animation: pulse 1.5s infinite;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--surface-color);
  border-radius: var(--radius);
  padding: 16px;
  text-align: center;
  box-shadow: var(--shadow);
}

.stat-card.highlight {
  background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.stat-value.sync-date {
  font-size: 14px;
  font-weight: 600;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 6px;
}

.stat-card.highlight .stat-label {
  color: rgba(255, 255, 255, 0.9);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--text-secondary);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 16px;
  background: var(--surface-color);
  border: none;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.action-card:active {
  transform: scale(0.98);
}

.action-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}

.action-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.sync-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 152, 0, 0.1);
  border: 1px solid rgba(255, 152, 0, 0.3);
  border-radius: var(--radius);
  margin-bottom: 24px;
}

.alert-icon {
  font-size: 24px;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  font-size: 14px;
}

.alert-text {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 14px;
}

.logout-btn {
  display: block;
  width: 100%;
  padding: 14px;
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 15px;
  color: var(--text-secondary);
  cursor: pointer;
  margin-top: 20px;
}

.logout-btn:active {
  background: var(--background-color);
}

/* Menu de création de géométrie */
.create-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.create-menu {
  background: var(--surface-color);
  border-radius: 16px 16px 0 0;
  padding: 20px;
  width: 100%;
  max-width: 400px;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.create-menu h3 {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  color: var(--text-primary);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 16px;
  background: var(--background-color);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  margin-bottom: 10px;
  transition: background 0.2s;
}

.menu-item:active {
  background: var(--border-color);
}

.menu-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.point-icon {
  background: linear-gradient(135deg, #4CAF50, #45a049);
}

.line-icon {
  background: linear-gradient(135deg, #2196F3, #1976D2);
}

.polygon-icon {
  background: linear-gradient(135deg, #FF9800, #F57C00);
}

.menu-text {
  text-align: left;
  flex: 1;
}

.menu-label {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.menu-desc {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.cancel-btn {
  width: 100%;
  padding: 14px;
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 15px;
  color: var(--text-secondary);
  cursor: pointer;
  margin-top: 8px;
}

.cancel-btn:active {
  background: var(--background-color);
}
</style>

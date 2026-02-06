<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePointsStore } from '@/stores/points'

const router = useRouter()
const pointsStore = usePointsStore()

const searchQuery = ref('')
const isRefreshing = ref(false)

// Points filtrés
const filteredPoints = computed(() => {
  if (!searchQuery.value) return pointsStore.points

  const query = searchQuery.value.toLowerCase()
  return pointsStore.points.filter(point =>
    point.name?.toLowerCase().includes(query) ||
    point.comment?.toLowerCase().includes(query) ||
    pointsStore.getLexiqueLabel(point.lexique_code || '').toLowerCase().includes(query)
  )
})

// Charger les points
const loadPoints = async () => {
  await pointsStore.loadPoints()
}

// Rafraîchir (pull to refresh style)
const refresh = async () => {
  isRefreshing.value = true
  await loadPoints()
  isRefreshing.value = false
}

// Ouvrir un point
const openPoint = (point: typeof pointsStore.points[0]) => {
  const id = point.id || point._localId
  if (id) {
    router.push(`/point/${id}`)
  }
}

// Formater la date
const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit'
    })
  } catch {
    return ''
  }
}

// Status badge - vocabulaire adapté à l'agent terrain
const getStatusBadge = (status?: string) => {
  switch (status) {
    case 'draft': return { text: 'Envoyé ✓', class: 'badge-info' }
    case 'pending': return { text: 'Envoyé ✓', class: 'badge-info' }
    case 'validated': return { text: 'Validé ✓✓', class: 'badge-success' }
    case 'rejected': return { text: 'Rejeté ✗', class: 'badge-error' }
    default: return null
  }
}

onMounted(() => {
  loadPoints()
})
</script>

<template>
  <div class="points-page page">
    <!-- Header -->
    <div class="page-header">
      <h1>Mes points</h1>
      <div class="header-stats">
        {{ pointsStore.totalPoints }} point(s)
        <span v-if="pointsStore.pendingCount > 0" class="pending-badge">
          {{ pointsStore.pendingCount }} à envoyer
        </span>
      </div>
    </div>

    <div class="page-content">
      <!-- Barre de recherche -->
      <div class="search-bar">
        <span class="search-icon">🔍</span>
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Rechercher un point..."
          class="search-input"
        />
        <button
          v-if="searchQuery"
          class="clear-btn"
          @click="searchQuery = ''"
        >
          ✕
        </button>
      </div>

      <!-- Bouton rafraîchir -->
      <button
        class="refresh-btn"
        :disabled="isRefreshing"
        @click="refresh"
      >
        <span :class="{ spinning: isRefreshing }">🔄</span>
        {{ isRefreshing ? 'Chargement...' : 'Actualiser' }}
      </button>

      <!-- Liste des points -->
      <div v-if="pointsStore.isLoading && !pointsStore.points.length" class="loader">
        <div class="spinner"></div>
      </div>

      <div v-else-if="filteredPoints.length === 0" class="empty-state">
        <div class="empty-state-icon">📍</div>
        <div class="empty-state-title">
          {{ searchQuery ? 'Aucun résultat' : 'Aucun point' }}
        </div>
        <div class="empty-state-text">
          {{ searchQuery
            ? 'Essayez avec d\'autres termes'
            : 'Créez votre premier point en appuyant sur le bouton +'
          }}
        </div>
      </div>

      <div v-else class="points-list">
        <div
          v-for="point in filteredPoints"
          :key="point.id || point._localId"
          class="point-item"
          :class="{ pending: point._pendingSync }"
          @click="openPoint(point)"
        >
          <div class="point-icon" :class="{ 'has-photo': point.photos?.length }">
            {{ point.photos?.length ? '📷' : '📍' }}
          </div>

          <div class="point-content">
            <div class="point-name">{{ point.name || 'Sans nom' }}</div>
            <div class="point-meta">
              <span v-if="point.lexique_code" class="point-category">
                {{ pointsStore.getLexiqueLabel(point.lexique_code) }}
              </span>
              <span v-if="point.created_at" class="point-date">
                {{ formatDate(point.created_at) }}
              </span>
            </div>
          </div>

          <div class="point-status">
            <span
              v-if="point._pendingSync"
              class="badge badge-warning"
            >
              À envoyer
            </span>
            <span
              v-else-if="getStatusBadge(point.sync_status)"
              class="badge"
              :class="getStatusBadge(point.sync_status)?.class"
            >
              {{ getStatusBadge(point.sync_status)?.text }}
            </span>
            <span class="arrow">›</span>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="pointsStore.totalPages > 1" class="pagination">
        <button
          :disabled="pointsStore.currentPage <= 1"
          @click="pointsStore.loadPoints(pointsStore.currentPage - 1)"
        >
          ← Précédent
        </button>
        <span>{{ pointsStore.currentPage }} / {{ pointsStore.totalPages }}</span>
        <button
          :disabled="pointsStore.currentPage >= pointsStore.totalPages"
          @click="pointsStore.loadPoints(pointsStore.currentPage + 1)"
        >
          Suivant →
        </button>
      </div>
    </div>

    <!-- FAB Nouveau point -->
    <button class="fab" @click="router.push('/point/new')">
      ➕
    </button>
  </div>
</template>

<style scoped>
.points-page {
  background: var(--background-color);
}

.header-stats {
  font-size: 14px;
  font-weight: normal;
  opacity: 0.9;
  margin-top: 4px;
}

.pending-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 8px;
  font-size: 12px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--surface-color);
  border-radius: var(--radius-sm);
  padding: 4px 12px;
  margin-bottom: 12px;
  box-shadow: var(--shadow);
}

.search-icon {
  font-size: 16px;
  opacity: 0.5;
}

.search-input {
  flex: 1;
  border: none;
  background: none;
  font-size: 16px;
  padding: 10px 0;
  outline: none;
}

.clear-btn {
  background: none;
  border: none;
  font-size: 16px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px 8px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  margin-bottom: 16px;
}

.refresh-btn:disabled {
  opacity: 0.6;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.points-list {
  background: var(--surface-color);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
}

.point-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background 0.2s;
}

.point-item:last-child {
  border-bottom: none;
}

.point-item:active {
  background: var(--background-color);
}

.point-item.pending {
  background: rgba(255, 152, 0, 0.05);
}

.point-icon {
  width: 44px;
  height: 44px;
  background: var(--primary-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.point-icon.has-photo {
  background: var(--success-color);
}

.point-content {
  flex: 1;
  min-width: 0;
}

.point-name {
  font-weight: 500;
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.point-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}

.point-category {
  max-width: 150px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.point-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.arrow {
  font-size: 20px;
  color: var(--text-secondary);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
  padding: 12px;
}

.pagination button {
  padding: 8px 16px;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.badge-info {
  background: rgba(33, 150, 243, 0.15);
  color: #1976D2;
}
</style>

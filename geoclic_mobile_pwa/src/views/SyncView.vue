<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { usePointsStore } from '@/stores/points'
import { api } from '@/services/api'
import { offlineService } from '@/services/offline'

const pointsStore = usePointsStore()

const isSyncing = ref(false)
const syncProgress = ref(0)
const syncMessage = ref('')
const syncResults = ref<{
  success: boolean
  uploaded: number
  downloaded: number
  errors: string[]
} | null>(null)

const stats = ref({
  pendingPoints: 0,
  pendingPhotos: 0,
  lastSync: ''
})

const isOnline = computed(() => pointsStore.isOnline)

// Charger les statistiques
const loadStats = async () => {
  try {
    await offlineService.init()
    const offlineStats = await offlineService.getStats()
    stats.value = {
      pendingPoints: offlineStats.pendingPoints,
      pendingPhotos: offlineStats.pendingPhotos,
      lastSync: offlineStats.lastSync || ''
    }
    await pointsStore.updatePendingCount()
  } catch (err) {
    console.error('Erreur chargement stats:', err)
  }
}

// Synchroniser
const sync = async () => {
  if (!isOnline.value) {
    alert('Pas de connexion internet')
    return
  }

  isSyncing.value = true
  syncProgress.value = 0
  syncMessage.value = 'Préparation...'
  syncResults.value = null

  try {
    // Étape 1: Récupérer les points en attente
    syncMessage.value = 'Récupération des points en attente...'
    syncProgress.value = 10
    const pendingPoints = await offlineService.getPendingPoints()

    // Étape 2: Récupérer les photos en attente
    syncMessage.value = 'Récupération des photos...'
    syncProgress.value = 20
    const pendingPhotos = await offlineService.getPendingPhotos()

    // Étape 3: Upload des photos
    if (pendingPhotos.length > 0) {
      syncMessage.value = `Upload des photos (0/${pendingPhotos.length})...`
      syncProgress.value = 30

      for (let i = 0; i < pendingPhotos.length; i++) {
        const photo = pendingPhotos[i]
        try {
          const file = new File([photo.blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' })
          await api.uploadPhoto(photo.pointId, file, {
            gps_lat: photo.gps_lat,
            gps_lng: photo.gps_lng,
            gps_accuracy: photo.gps_accuracy
          })
          await offlineService.deletePendingPhoto(photo.id)
          syncMessage.value = `Upload des photos (${i + 1}/${pendingPhotos.length})...`
        } catch (err) {
          console.error('Erreur upload photo:', err)
        }
        syncProgress.value = 30 + (i / pendingPhotos.length) * 20
      }
    }

    // Étape 4: Synchronisation des points
    syncMessage.value = 'Synchronisation des points...'
    syncProgress.value = 60

    const deviceId = localStorage.getItem('geoclic_device_id') || crypto.randomUUID()
    localStorage.setItem('geoclic_device_id', deviceId)

    const lastSyncAt = await offlineService.getLastSyncTimestamp()

    const response = await api.sync({
      device_id: deviceId,
      last_sync_at: lastSyncAt || undefined,
      points_to_upload: pendingPoints
    })

    syncProgress.value = 80

    // Étape 5: Traiter les résultats
    syncMessage.value = 'Traitement des résultats...'

    // Supprimer les points synchronisés
    for (const point of pendingPoints) {
      if (point._localId) {
        await offlineService.deletePendingPoint(point._localId)
      }
    }

    // Sauvegarder les points téléchargés
    const downloadedPoints = Array.isArray(response.points_to_download) ? response.points_to_download : []
    for (const point of downloadedPoints) {
      await offlineService.savePoint(point)
    }

    // Mettre à jour le timestamp
    if (response.server_time) {
      await offlineService.setLastSyncTimestamp(response.server_time)
    }

    syncProgress.value = 100
    syncMessage.value = 'Terminé !'

    syncResults.value = {
      success: true,
      uploaded: response.points_uploaded || 0,
      downloaded: downloadedPoints.length,
      errors: Array.isArray(response.errors) ? response.errors : []
    }

    // Recharger les données
    await loadStats()
    await pointsStore.loadPoints()

  } catch (err: unknown) {
    console.error('Erreur sync:', err)
    let errorMessage = 'Erreur de synchronisation'
    if (axios.isAxiosError(err) && err.response) {
      if (err.response.status === 422) {
        const detail = err.response.data?.detail
        errorMessage = 'Données invalides: ' + (Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg).join(', ') : JSON.stringify(detail))
      } else if (err.response.status === 401) {
        errorMessage = 'Session expirée, veuillez vous reconnecter'
      } else {
        errorMessage = `Erreur serveur (${err.response.status}): ${err.response.data?.detail || err.message}`
      }
    } else if (err instanceof Error) {
      errorMessage = err.message
    }
    syncResults.value = {
      success: false,
      uploaded: 0,
      downloaded: 0,
      errors: [errorMessage]
    }
  } finally {
    isSyncing.value = false
  }
}

// Télécharger le package hors-ligne
const downloadOfflinePackage = async () => {
  if (!isOnline.value) {
    alert('Connexion requise')
    return
  }

  syncMessage.value = 'Téléchargement des données...'
  isSyncing.value = true

  try {
    const pkg = await api.getOfflinePackage()

    const lexiqueEntries = Array.isArray(pkg?.lexique_entries) ? pkg.lexique_entries : []
    const projectsList = Array.isArray(pkg?.projects) ? pkg.projects : []
    const rawChamps = Array.isArray(pkg?.champs_dynamiques) ? pkg.champs_dynamiques : []

    // Normaliser les champs du sync (noms API → noms mobile)
    // API sync retourne: min_value/max_value, lexique_code
    // Mobile attend: min/max, lexique_code
    const champsList = rawChamps.map((ch: Record<string, unknown>) => ({
      id: String(ch.id || ''),
      lexique_code: String(ch.lexique_code || ''),
      nom: String(ch.nom || ''),
      type: ch.type as string,
      obligatoire: Boolean(ch.obligatoire),
      ordre: Number(ch.ordre) || 0,
      options: Array.isArray(ch.options) ? ch.options : undefined,
      min: ch.min_value != null ? Number(ch.min_value) : (ch.min != null ? Number(ch.min) : undefined),
      max: ch.max_value != null ? Number(ch.max_value) : (ch.max != null ? Number(ch.max) : undefined),
      default_value: ch.default_value ? String(ch.default_value) : undefined,
      project_id: ch.project_id ? String(ch.project_id) : undefined,
      condition_field: ch.condition_field ? String(ch.condition_field) : undefined,
      condition_operator: ch.condition_operator ? String(ch.condition_operator) : undefined,
      condition_value: ch.condition_value ? String(ch.condition_value) : undefined
    }))

    await offlineService.saveLexique(lexiqueEntries)
    await offlineService.saveProjects(projectsList)
    await offlineService.saveChamps(champsList)

    await pointsStore.loadReferenceData()

    alert(`Données téléchargées: ${lexiqueEntries.length} catégories, ${projectsList.length} projets, ${champsList.length} champs`)
  } catch (err) {
    console.error('Erreur téléchargement:', err)
    alert('Erreur lors du téléchargement')
  } finally {
    isSyncing.value = false
    syncMessage.value = ''
  }
}

// Formater la date
const formatDate = (dateStr: string) => {
  if (!dateStr) return 'Jamais'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="sync-page page">
    <div class="page-header">
      <h1>Synchronisation</h1>
    </div>

    <div class="page-content">
      <!-- Status connexion -->
      <div class="connection-card" :class="{ online: isOnline, offline: !isOnline }">
        <div class="connection-icon">{{ isOnline ? '🌐' : '📴' }}</div>
        <div class="connection-info">
          <div class="connection-status">{{ isOnline ? 'En ligne' : 'Hors ligne' }}</div>
          <div class="connection-hint">
            {{ isOnline
              ? 'Prêt pour la synchronisation'
              : 'Connectez-vous à internet pour synchroniser'
            }}
          </div>
        </div>
      </div>

      <!-- Statistiques -->
      <div class="stats-card">
        <div class="stat-row">
          <span class="stat-label">Points à envoyer</span>
          <span class="stat-value" :class="{ highlight: stats.pendingPoints > 0 }">
            {{ stats.pendingPoints }}
          </span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Photos à envoyer</span>
          <span class="stat-value" :class="{ highlight: stats.pendingPhotos > 0 }">
            {{ stats.pendingPhotos }}
          </span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Dernière synchronisation</span>
          <span class="stat-value">{{ formatDate(stats.lastSync) }}</span>
        </div>
      </div>

      <!-- Progression -->
      <div v-if="isSyncing" class="progress-card">
        <div class="progress-message">{{ syncMessage }}</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: syncProgress + '%' }"></div>
        </div>
        <div class="progress-percent">{{ Math.round(syncProgress) }}%</div>
      </div>

      <!-- Résultats -->
      <div v-if="syncResults" class="results-card" :class="{ success: syncResults.success, error: !syncResults.success }">
        <div class="results-icon">{{ syncResults.success ? '✅' : '❌' }}</div>
        <div class="results-content">
          <div class="results-title">
            {{ syncResults.success ? 'Synchronisation réussie' : 'Erreur de synchronisation' }}
          </div>
          <div v-if="syncResults.success" class="results-details">
            <div v-if="syncResults.uploaded > 0">
              {{ syncResults.uploaded }} point(s) envoyé(s) au serveur
            </div>
            <div v-else class="results-allsync">
              Tous vos points sont à jour
            </div>
            <div class="results-total">
              Total sur le serveur : {{ syncResults.downloaded + syncResults.uploaded }} point(s)
            </div>
          </div>
          <div v-if="syncResults.errors.length > 0" class="results-errors">
            <div v-for="(error, index) in syncResults.errors" :key="index" class="error-item">
              ⚠️ {{ error }}
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="actions">
        <button
          class="btn btn-primary btn-block sync-btn"
          :disabled="isSyncing || !isOnline"
          @click="sync"
        >
          <span v-if="isSyncing" class="spinner"></span>
          <span v-else>🔄 Synchroniser maintenant</span>
        </button>

        <button
          class="btn btn-secondary btn-block"
          :disabled="isSyncing || !isOnline"
          @click="downloadOfflinePackage"
        >
          📦 Télécharger les données hors-ligne
        </button>
      </div>

      <!-- Info -->
      <div class="info-card">
        <h3>💡 Comment ça marche ?</h3>
        <ul>
          <li>Les points créés hors-ligne sont sauvegardés localement</li>
          <li>Quand vous êtes en ligne, appuyez sur "Synchroniser"</li>
          <li>Vos points seront envoyés au serveur</li>
          <li>Les nouveaux points du serveur seront téléchargés</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sync-page {
  background: var(--background-color);
}

.connection-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: var(--radius);
  margin-bottom: 16px;
}

.connection-card.online {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.connection-card.offline {
  background: rgba(255, 152, 0, 0.1);
  border: 1px solid rgba(255, 152, 0, 0.3);
}

.connection-icon {
  font-size: 36px;
}

.connection-status {
  font-size: 18px;
  font-weight: 600;
}

.connection-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.stats-card {
  background: var(--surface-color);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-label {
  color: var(--text-secondary);
}

.stat-value {
  font-weight: 600;
}

.stat-value.highlight {
  color: var(--warning-color);
}

.progress-card {
  background: var(--surface-color);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
  text-align: center;
  box-shadow: var(--shadow);
}

.progress-message {
  margin-bottom: 12px;
  color: var(--text-secondary);
}

.progress-bar {
  height: 8px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-percent {
  margin-top: 8px;
  font-weight: 600;
  color: var(--primary-color);
}

.results-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  border-radius: var(--radius);
  margin-bottom: 16px;
}

.results-card.success {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.results-card.error {
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.results-icon {
  font-size: 32px;
}

.results-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.results-details {
  font-size: 14px;
  color: var(--text-secondary);
}

.results-allsync {
  color: #4CAF50;
  font-weight: 500;
}

.results-total {
  margin-top: 4px;
  font-size: 13px;
  opacity: 0.8;
}

.results-errors {
  margin-top: 8px;
}

.error-item {
  font-size: 13px;
  color: var(--error-color);
  margin-top: 4px;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.sync-btn {
  height: 54px;
  font-size: 17px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.info-card {
  background: rgba(33, 150, 243, 0.08);
  border-radius: var(--radius);
  padding: 20px;
}

.info-card h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.info-card ul {
  margin: 0;
  padding-left: 20px;
}

.info-card li {
  margin: 8px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

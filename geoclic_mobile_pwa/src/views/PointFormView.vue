<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePointsStore } from '@/stores/points'
import { gpsService, type GpsPosition } from '@/services/gps'
import GpsStatus from '@/components/GpsStatus.vue'
import LexiqueSelector from '@/components/LexiqueSelector.vue'
import type { Point, PhotoMetadata } from '@/services/api'

const route = useRoute()
const router = useRouter()
const pointsStore = usePointsStore()

const isNew = computed(() => route.name === 'point-new')
const pointId = computed(() => route.params.id as string)

// État du formulaire
const form = ref({
  name: '',
  comment: '',
  lexique_code: '',
  project_id: '',
  latitude: null as number | null,
  longitude: null as number | null,
  accuracy: null as number | null,
  altitude: null as number | null,
  gps_source: 'mobile'
})

const photos = ref<(PhotoMetadata & { localBlob?: Blob })[]>([])
const isSaving = ref(false)
const isGpsLoading = ref(false)
const showDeleteConfirm = ref(false)

// Charger un point existant
const loadPoint = async () => {
  if (isNew.value) return

  const point = pointsStore.getPointById(pointId.value)
  if (point) {
    form.value = {
      name: point.name || '',
      comment: point.comment || '',
      lexique_code: point.lexique_code || '',
      project_id: point.project_id || '',
      latitude: point.coordinates?.[0]?.latitude ?? null,
      longitude: point.coordinates?.[0]?.longitude ?? null,
      accuracy: point.gps_precision ?? null,
      altitude: point.altitude ?? null,
      gps_source: point.gps_source || 'mobile'
    }
    photos.value = point.photos || []
  }
}

// Obtenir la position GPS
const refreshGps = async () => {
  isGpsLoading.value = true

  try {
    const position = await gpsService.getCurrentPosition({
      enableHighAccuracy: true,
      timeout: 30000,
      maximumAge: 0
    })

    form.value.latitude = position.latitude
    form.value.longitude = position.longitude
    form.value.accuracy = position.accuracy
    form.value.altitude = position.altitude
    form.value.gps_source = 'mobile'
  } catch (err) {
    console.error('Erreur GPS:', err)
  } finally {
    isGpsLoading.value = false
  }
}

// Démarrer le suivi GPS continu
const startGpsTracking = () => {
  gpsService.startWatching((position: GpsPosition) => {
    form.value.latitude = position.latitude
    form.value.longitude = position.longitude
    form.value.accuracy = position.accuracy
    form.value.altitude = position.altitude
  })
}

// Compression image max 720x576
const MAX_WIDTH = 720
const MAX_HEIGHT = 576
const JPEG_QUALITY = 0.85

async function compressImage(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      let { width, height } = img

      // Calculer les nouvelles dimensions en conservant le ratio
      if (width > MAX_WIDTH || height > MAX_HEIGHT) {
        const ratio = Math.min(MAX_WIDTH / width, MAX_HEIGHT / height)
        width = Math.round(width * ratio)
        height = Math.round(height * ratio)
      }

      // Créer un canvas pour redimensionner
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height

      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('Canvas context not available'))
        return
      }

      ctx.drawImage(img, 0, 0, width, height)

      // Convertir en blob JPEG
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Compression failed'))
            return
          }
          resolve(blob)
        },
        'image/jpeg',
        JPEG_QUALITY
      )
    }

    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = URL.createObjectURL(file)
  })
}

// Prendre une photo
const takePhoto = async () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.capture = 'environment' // Caméra arrière

  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return

    try {
      // Compresser l'image à 720p max
      const compressedBlob = await compressImage(file)
      const localUrl = URL.createObjectURL(compressedBlob)

      photos.value.push({
        localPath: localUrl,
        localBlob: compressedBlob,
        gps_lat: form.value.latitude ?? undefined,
        gps_lng: form.value.longitude ?? undefined,
        gps_accuracy: form.value.accuracy ?? undefined
      })
    } catch (err) {
      console.error('Erreur compression photo:', err)
      // Fallback: utiliser l'image non compressée
      const localUrl = URL.createObjectURL(file)
      photos.value.push({
        localPath: localUrl,
        localBlob: file,
        gps_lat: form.value.latitude ?? undefined,
        gps_lng: form.value.longitude ?? undefined,
        gps_accuracy: form.value.accuracy ?? undefined
      })
    }
  }

  input.click()
}

// Supprimer une photo
const removePhoto = (index: number) => {
  const photo = photos.value[index]
  if (photo.localPath && photo.localPath.startsWith('blob:')) {
    URL.revokeObjectURL(photo.localPath)
  }
  photos.value.splice(index, 1)
}

// Sauvegarder
const save = async () => {
  if (!form.value.name.trim()) {
    alert('Le nom est obligatoire')
    return
  }

  if (!form.value.latitude || !form.value.longitude) {
    alert('La position GPS est requise')
    return
  }

  isSaving.value = true

  try {
    const pointData: Partial<Point> = {
      name: form.value.name.trim(),
      comment: form.value.comment.trim() || undefined,
      lexique_code: form.value.lexique_code || undefined,
      project_id: form.value.project_id || undefined,
      coordinates: [{
        latitude: form.value.latitude,
        longitude: form.value.longitude
      }],
      gps_precision: form.value.accuracy ?? undefined,
      gps_source: form.value.gps_source,
      altitude: form.value.altitude ?? undefined
    }

    let savedPoint: Point | null = null

    if (isNew.value) {
      savedPoint = await pointsStore.createPoint(pointData)
    } else {
      savedPoint = await pointsStore.updatePoint(pointId.value, pointData)
    }

    if (savedPoint) {
      // Uploader les photos locales vers le serveur
      const savedId = savedPoint.id || savedPoint._localId
      const localPhotos = photos.value.filter(p => p.localBlob)
      if (savedId && localPhotos.length > 0) {
        try {
          const uploaded = await pointsStore.uploadPhotosForPoint(
            savedId,
            localPhotos as Array<{ localBlob: Blob; gps_lat?: number; gps_lng?: number; gps_accuracy?: number }>
          )
          console.log(`${uploaded}/${localPhotos.length} photos uploadées`)
          if (uploaded < localPhotos.length) {
            alert(`${uploaded}/${localPhotos.length} photos uploadées. Les autres seront synchronisées plus tard.`)
          }
        } catch (err) {
          console.error('Erreur upload photos:', err)
          alert('Erreur lors de l\'upload des photos. Elles seront synchronisées plus tard.')
        }
      }
      router.back()
    }
  } catch (err) {
    console.error('Erreur sauvegarde:', err)
    alert('Erreur lors de la sauvegarde')
  } finally {
    isSaving.value = false
  }
}

// Supprimer le point
const deletePoint = async () => {
  if (!pointId.value) return

  const success = await pointsStore.deletePoint(pointId.value)
  if (success) {
    router.back()
  }
  showDeleteConfirm.value = false
}

// Formater les coordonnées
const formatCoords = computed(() => {
  if (!form.value.latitude || !form.value.longitude) return ''
  return `${form.value.latitude.toFixed(6)}, ${form.value.longitude.toFixed(6)}`
})

onMounted(async () => {
  await pointsStore.loadReferenceData()
  await loadPoint()

  // Démarrer le GPS automatiquement si nouveau point
  if (isNew.value) {
    refreshGps()
  }
})

onUnmounted(() => {
  gpsService.stopWatching()
})
</script>

<template>
  <div class="point-form-page">
    <!-- Header -->
    <header class="form-header">
      <button class="back-btn" @click="router.back()">
        ← Retour
      </button>
      <h1>{{ isNew ? 'Nouveau point' : 'Modifier le point' }}</h1>
      <button
        v-if="!isNew"
        class="delete-btn"
        @click="showDeleteConfirm = true"
      >
        🗑️
      </button>
    </header>

    <!-- Formulaire -->
    <div class="form-content">
      <!-- GPS Status -->
      <div class="gps-section">
        <div class="section-header">
          <h2>📍 Position GPS</h2>
          <button
            class="refresh-gps-btn"
            :disabled="isGpsLoading"
            @click="refreshGps"
          >
            {{ isGpsLoading ? '⏳' : '🔄' }} Actualiser
          </button>
        </div>

        <GpsStatus />

        <div v-if="form.latitude && form.longitude" class="coords-display">
          <div class="coord-value">{{ formatCoords }}</div>
          <div class="coord-accuracy">
            Précision: {{ form.accuracy ? `${Math.round(form.accuracy)}m` : '-' }}
          </div>
        </div>

        <div v-else class="no-gps-warning">
          ⚠️ Position GPS requise. Appuyez sur "Actualiser".
        </div>
      </div>

      <!-- Informations -->
      <div class="form-section">
        <h2>📝 Informations</h2>

        <div class="form-group">
          <label class="form-label">Nom du point *</label>
          <input
            v-model="form.name"
            type="text"
            class="form-input"
            placeholder="Ex: Lampadaire n°42"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Catégorie</label>
          <LexiqueSelector
            v-model="form.lexique_code"
            placeholder="Sélectionner une catégorie"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Projet</label>
          <select v-model="form.project_id" class="form-select">
            <option value="">Aucun projet</option>
            <option
              v-for="project in pointsStore.projects"
              :key="project.id"
              :value="project.id"
            >
              {{ project.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Commentaire</label>
          <textarea
            v-model="form.comment"
            class="form-textarea"
            placeholder="Description, remarques..."
            rows="3"
          ></textarea>
        </div>
      </div>

      <!-- Photos -->
      <div class="form-section">
        <div class="section-header">
          <h2>📷 Photos</h2>
          <button class="add-photo-btn" @click="takePhoto">
            + Ajouter
          </button>
        </div>

        <div v-if="photos.length === 0" class="no-photos">
          Aucune photo
        </div>

        <div v-else class="photos-grid">
          <div
            v-for="(photo, index) in photos"
            :key="index"
            class="photo-item"
          >
            <img
              :src="photo.localPath || photo.url"
              alt="Photo"
              class="photo-thumb"
            />
            <button
              class="photo-delete"
              @click="removePhoto(index)"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bouton Sauvegarder -->
    <div class="form-actions">
      <button
        class="btn btn-primary btn-block save-btn"
        :disabled="isSaving || !form.name || !form.latitude"
        @click="save"
      >
        <span v-if="isSaving" class="spinner"></span>
        <span v-else>{{ isNew ? 'Créer le point' : 'Enregistrer' }}</span>
      </button>
    </div>

    <!-- Modal confirmation suppression -->
    <Teleport to="body">
      <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
        <div class="confirm-modal">
          <h3>Supprimer ce point ?</h3>
          <p>Cette action est irréversible.</p>
          <div class="confirm-actions">
            <button class="btn btn-secondary" @click="showDeleteConfirm = false">
              Annuler
            </button>
            <button class="btn btn-danger" @click="deletePoint">
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.point-form-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--background-color);
}

.form-header {
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

.form-header h1 {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.delete-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  margin: -8px;
}

.form-content {
  flex: 1;
  padding: 16px;
  padding-bottom: 100px;
  overflow-y: auto;
}

.form-section,
.gps-section {
  background: var(--surface-color);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.form-section h2,
.gps-section h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.refresh-gps-btn,
.add-photo-btn {
  padding: 6px 12px;
  background: var(--primary-light);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
}

.refresh-gps-btn:disabled {
  opacity: 0.6;
}

.coords-display {
  margin-top: 12px;
  padding: 12px;
  background: var(--background-color);
  border-radius: var(--radius-sm);
}

.coord-value {
  font-family: monospace;
  font-size: 15px;
  font-weight: 500;
}

.coord-accuracy {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.no-gps-warning {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 152, 0, 0.1);
  border-radius: var(--radius-sm);
  color: var(--warning-color);
  font-size: 14px;
}

.no-photos {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.photo-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.photo-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-delete {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 14px;
  cursor: pointer;
}

.form-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  padding-bottom: calc(var(--safe-area-inset-bottom) + 16px);
  background: var(--surface-color);
  border-top: 1px solid var(--border-color);
}

.save-btn {
  height: 50px;
  font-size: 16px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Confirm Modal */
.confirm-modal {
  background: var(--surface-color);
  border-radius: var(--radius);
  padding: 24px;
  margin: 16px;
  text-align: center;
}

.confirm-modal h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.confirm-modal p {
  margin: 0 0 20px;
  color: var(--text-secondary);
}

.confirm-actions {
  display: flex;
  gap: 12px;
}

.confirm-actions .btn {
  flex: 1;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

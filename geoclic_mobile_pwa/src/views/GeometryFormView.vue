<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePointsStore } from '@/stores/points'
import { gpsService } from '@/services/gps'
import type { Point, Coordinate, GeometryType, PhotoMetadata, ChampDynamique } from '@/services/api'

import GeometryTypeSelector from '@/components/GeometryTypeSelector.vue'
import GeometryDrawing from '@/components/GeometryDrawing.vue'
import LexiqueSelector from '@/components/LexiqueSelector.vue'

const route = useRoute()
const router = useRouter()
const pointsStore = usePointsStore()

const isNew = computed(() => route.name === 'geometry-new')
const pointId = computed(() => route.params.id as string)
const initialGeomType = computed(() => (route.query.type as GeometryType) || 'POINT')

// Onglet actif: 'map' ou 'form'
const activeTab = ref<'map' | 'form'>('map')

// Type de géométrie
const geomType = ref<GeometryType>(initialGeomType.value)

// Coordonnées
const coordinates = ref<Coordinate[]>([])

// Position GPS actuelle
const currentPosition = ref<{ latitude: number; longitude: number } | null>(null)
const currentAccuracy = ref<number | null>(null)

// État du formulaire
const form = ref({
  name: '',
  comment: '',
  lexique_code: '',
  project_id: ''
})

// Propriétés personnalisées (champs dynamiques)
const customProperties = ref<Record<string, unknown>>({})

// Champs dynamiques pour la catégorie sélectionnée (ref au lieu de computed pour mise à jour explicite)
const dynamicFields = ref<ChampDynamique[]>([])

// Vérifier si un champ doit être visible (conditions remplies)
const isFieldVisible = (field: ChampDynamique): boolean => {
  // Si pas de condition, le champ est toujours visible
  if (!field.condition_field) {
    return true
  }

  const triggerValue = customProperties.value[field.condition_field]
  const expectedValue = field.condition_value
  const operator = field.condition_operator || '='

  switch (operator) {
    case '=':
      // Égal à : la valeur doit correspondre exactement
      return triggerValue === expectedValue
    case '!=':
      // Différent de : la valeur ne doit pas correspondre
      return triggerValue !== expectedValue
    case 'contains':
      // Contient : le texte doit contenir la valeur attendue
      if (typeof triggerValue === 'string' && expectedValue) {
        return triggerValue.toLowerCase().includes(expectedValue.toLowerCase())
      }
      return false
    case 'not_empty':
      // Non vide : la valeur doit être définie et non vide
      if (Array.isArray(triggerValue)) {
        return triggerValue.length > 0
      }
      return triggerValue !== undefined && triggerValue !== null && triggerValue !== ''
    default:
      return true
  }
}

// Champs visibles (filtrés selon les conditions)
const visibleFields = computed(() => {
  return dynamicFields.value.filter(field => isFieldVisible(field))
})

const photos = ref<(PhotoMetadata & { localBlob?: Blob })[]>([])
const isSaving = ref(false)
const showDeleteConfirm = ref(false)

// Charger une géométrie existante
const loadGeometry = async () => {
  if (isNew.value) return

  const point = pointsStore.getPointById(pointId.value)
  if (point) {
    form.value = {
      name: point.name || '',
      comment: point.comment || '',
      lexique_code: point.lexique_code || '',
      project_id: point.project_id || ''
    }
    geomType.value = (point.geom_type as GeometryType) || 'POINT'
    coordinates.value = point.coordinates || []
    photos.value = point.photos || []
    // Charger les propriétés personnalisées
    if (point.custom_properties) {
      customProperties.value = { ...point.custom_properties }
    }
  }
}

// Obtenir la position GPS actuelle
const refreshGps = async () => {
  try {
    const position = await gpsService.getCurrentPosition({
      enableHighAccuracy: true,
      timeout: 30000,
      maximumAge: 0
    })

    currentPosition.value = {
      latitude: position.latitude,
      longitude: position.longitude
    }
    currentAccuracy.value = position.accuracy

    // Si point et pas encore de coordonnées, les définir
    if (geomType.value === 'POINT' && coordinates.value.length === 0) {
      coordinates.value = [{
        latitude: position.latitude,
        longitude: position.longitude
      }]
    }
  } catch (err) {
    console.error('Erreur GPS:', err)
  }
}

// Validation des coordonnées
const isCoordinatesValid = computed(() => {
  switch (geomType.value) {
    case 'POINT':
      return coordinates.value.length === 1
    case 'LINESTRING':
      return coordinates.value.length >= 2
    case 'POLYGON':
      return coordinates.value.length >= 3
    default:
      return false
  }
})

const coordinatesError = computed(() => {
  if (isCoordinatesValid.value) return ''
  switch (geomType.value) {
    case 'POINT':
      return 'Veuillez placer un point sur la carte'
    case 'LINESTRING':
      return 'Veuillez tracer une ligne avec au moins 2 points'
    case 'POLYGON':
      return 'Veuillez dessiner une zone avec au moins 3 points'
    default:
      return 'Géométrie invalide'
  }
})

// Titre de la page
const pageTitle = computed(() => {
  if (isNew.value) {
    switch (geomType.value) {
      case 'LINESTRING': return 'Nouvelle ligne'
      case 'POLYGON': return 'Nouvelle zone'
      default: return 'Nouveau point'
    }
  } else {
    switch (geomType.value) {
      case 'LINESTRING': return 'Modifier la ligne'
      case 'POLYGON': return 'Modifier la zone'
      default: return 'Modifier le point'
    }
  }
})

// Compression image max 720x576
const MAX_WIDTH = 720
const MAX_HEIGHT = 576
const JPEG_QUALITY = 0.85

async function compressImage(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      let { width, height } = img

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
  input.capture = 'environment'

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
        gps_lat: currentPosition.value?.latitude,
        gps_lng: currentPosition.value?.longitude,
        gps_accuracy: currentAccuracy.value ?? undefined
      })
    } catch (err) {
      console.error('Erreur compression photo:', err)
      // Fallback: utiliser l'image non compressée
      const localUrl = URL.createObjectURL(file)
      photos.value.push({
        localPath: localUrl,
        localBlob: file,
        gps_lat: currentPosition.value?.latitude,
        gps_lng: currentPosition.value?.longitude,
        gps_accuracy: currentAccuracy.value ?? undefined
      })
    }
  }

  input.click()
}

// Supprimer une photo
const removePhoto = (index: number) => {
  const photo = photos.value[index]
  if (photo.localPath?.startsWith('blob:')) {
    URL.revokeObjectURL(photo.localPath)
  }
  photos.value.splice(index, 1)
}

// Toggle pour champs multiselect
const toggleMultiselect = (fieldName: string, value: string) => {
  if (!Array.isArray(customProperties.value[fieldName])) {
    customProperties.value[fieldName] = []
  }
  const arr = customProperties.value[fieldName] as string[]
  const index = arr.indexOf(value)
  if (index === -1) {
    arr.push(value)
  } else {
    arr.splice(index, 1)
  }
}

// Sauvegarder
const save = async () => {
  if (!form.value.name.trim()) {
    alert('Le nom est obligatoire')
    activeTab.value = 'form'
    return
  }

  if (!isCoordinatesValid.value) {
    alert(coordinatesError.value)
    activeTab.value = 'map'
    return
  }

  isSaving.value = true

  try {
    // Nettoyer les custom_properties (retirer les valeurs vides)
    const cleanedCustomProps: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(customProperties.value)) {
      if (value !== undefined && value !== null && value !== '') {
        cleanedCustomProps[key] = value
      }
    }

    // Extraire type et subtype depuis lexique_code (ex: BANC_METAL → type: BANC, subtype: METAL)
    let pointType = 'AUTRE'
    let pointSubtype: string | undefined = undefined
    if (form.value.lexique_code) {
      const parts = form.value.lexique_code.split('_')
      if (parts.length > 0) {
        pointType = parts[0]
        if (parts.length > 1) {
          pointSubtype = parts.slice(1).join('_')
        }
      }
    }

    const pointData: Partial<Point> = {
      name: form.value.name.trim(),
      comment: form.value.comment.trim() || undefined,
      lexique_code: form.value.lexique_code || undefined,
      project_id: form.value.project_id || undefined,
      type: pointType,
      subtype: pointSubtype,
      geom_type: geomType.value,
      coordinates: coordinates.value,
      gps_precision: currentAccuracy.value ?? undefined,
      gps_source: 'mobile',
      custom_properties: Object.keys(cleanedCustomProps).length > 0 ? cleanedCustomProps : undefined
    }

    let savedPoint: Point | null = null

    if (isNew.value) {
      savedPoint = await pointsStore.createPoint(pointData)
    } else {
      savedPoint = await pointsStore.updatePoint(pointId.value, pointData)
    }

    if (savedPoint) {
      // Upload des photos si présentes
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

// Supprimer
const deleteGeometry = async () => {
  if (!pointId.value) return

  const success = await pointsStore.deletePoint(pointId.value)
  if (success) {
    router.back()
  }
  showDeleteConfirm.value = false
}

// Vérifier si le nom est auto-généré
// Patterns: "Point X", "Ligne X", "Zone X" (ancien) ou "BanB 01", "Arb 01" (nouveau)
const isNameAutoGenerated = (name: string): boolean => {
  if (!name) return true
  // Ancien pattern: "Point 1", "Ligne 2", "Zone 3"
  if (/^(Point|Ligne|Zone)\s+\d+$/i.test(name)) return true
  // Nouveau pattern: "BanB 01", "Arb 02", etc. (3-4 lettres + espace + 2 chiffres)
  if (/^[A-Z][a-z]{2}[A-Z]?\s+\d{2}$/.test(name)) return true
  return false
}

// Changement de type de géométrie
watch(geomType, (newType, oldType) => {
  if (newType !== oldType && isNew.value) {
    // Réinitialiser les coordonnées si le type change
    if (newType === 'POINT' && currentPosition.value) {
      coordinates.value = [{
        latitude: currentPosition.value.latitude,
        longitude: currentPosition.value.longitude
      }]
    } else if (newType !== 'POINT') {
      coordinates.value = []
    }
  }
})

// Charger les champs dynamiques quand la catégorie change
watch(() => form.value.lexique_code, async (newCode) => {
  if (newCode) {
    // Charger les champs pour cette catégorie et ses parents
    await loadChampsForCategory(newCode)

    // Mise à jour EXPLICITE des champs dynamiques après chargement
    const champs = pointsStore.getChampsByLexique(newCode, form.value.project_id || undefined)
    dynamicFields.value = JSON.parse(JSON.stringify(champs)) // Copie pour éviter les problèmes de réactivité

    console.log('[GeometryFormView] dynamicFields mis à jour:', dynamicFields.value.length, 'champs')

    // Générer automatiquement le nom si le champ est vide ou auto-généré
    if (isNew.value && isNameAutoGenerated(form.value.name)) {
      const categoryLabel = pointsStore.getLexiqueLabel(newCode)
      form.value.name = pointsStore.getNextGeometryName(categoryLabel, newCode)
    }
  } else {
    dynamicFields.value = []
  }

  // Appliquer les valeurs par défaut pour les nouveaux champs
  for (const field of dynamicFields.value) {
    if (field.default_value && customProperties.value[field.nom] === undefined) {
      customProperties.value[field.nom] = field.default_value
    }
  }
})

// Charger les champs pour une catégorie et ses parents (récursif)
const loadChampsForCategory = async (code: string) => {
  // Charger les champs pour ce code
  await pointsStore.loadChampsForLexique(code, form.value.project_id || undefined)

  // Trouver le parent et charger ses champs aussi
  const item = pointsStore.lexique.find(l => l.code === code)
  if (item?.parent_code) {
    await loadChampsForCategory(item.parent_code)
  }
}

onMounted(async () => {
  await pointsStore.loadReferenceData()
  await loadGeometry()

  if (isNew.value) {
    refreshGps()
    // Le nom sera généré automatiquement quand l'utilisateur sélectionne une catégorie
  }
})

onUnmounted(() => {
  gpsService.stopWatching()
})
</script>

<template>
  <div class="geometry-form-page">
    <!-- Header -->
    <header class="form-header">
      <button class="back-btn" @click="router.back()">
        ← Retour
      </button>
      <h1>{{ pageTitle }}</h1>
      <button
        v-if="!isNew"
        class="delete-btn"
        @click="showDeleteConfirm = true"
      >
        🗑️
      </button>
    </header>

    <!-- Tabs -->
    <div class="tabs">
      <button
        :class="['tab', { active: activeTab === 'map' }]"
        @click="activeTab = 'map'"
      >
        🗺️ Carte
        <span v-if="coordinates.length > 0" class="tab-badge">{{ coordinates.length }}</span>
      </button>
      <button
        :class="['tab', { active: activeTab === 'form' }]"
        @click="activeTab = 'form'"
      >
        📝 Formulaire
      </button>
    </div>

    <!-- Contenu -->
    <div class="content">
      <!-- Onglet Carte -->
      <div v-show="activeTab === 'map'" class="tab-content map-tab">
        <!-- Sélecteur de type (seulement pour nouveau) -->
        <div v-if="isNew" class="type-selector-wrapper">
          <GeometryTypeSelector
            v-model="geomType"
            :disabled="!isNew"
          />
        </div>

        <!-- Widget de dessin -->
        <div class="drawing-wrapper">
          <GeometryDrawing
            v-model="coordinates"
            :geometry-type="geomType"
            :current-position="currentPosition"
            :current-accuracy="currentAccuracy"
          />
        </div>
      </div>

      <!-- Onglet Formulaire -->
      <div v-show="activeTab === 'form'" class="tab-content form-tab">
        <!-- Informations -->
        <div class="form-section">
          <h2>📝 Informations</h2>

          <div class="form-group">
            <label class="form-label">Nom *</label>
            <input
              v-model="form.name"
              type="text"
              class="form-input"
              placeholder="Ex: Chemin de la Forêt"
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

        <!-- Données techniques (champs dynamiques) -->
        <div v-if="visibleFields.length > 0" class="form-section">
          <h2>🔧 Données techniques</h2>

          <div
            v-for="field in visibleFields"
            :key="field.id"
            class="form-group"
          >
            <label class="form-label">
              {{ field.nom }}
              <span v-if="field.obligatoire" class="required">*</span>
            </label>

            <!-- Champ texte -->
            <input
              v-if="field.type === 'text'"
              v-model="customProperties[field.nom]"
              type="text"
              class="form-input"
              :placeholder="field.default_value || ''"
            />

            <!-- Champ nombre -->
            <input
              v-else-if="field.type === 'number' || field.type === 'slider'"
              v-model.number="customProperties[field.nom]"
              type="number"
              class="form-input"
              :min="field.min"
              :max="field.max"
              :placeholder="field.default_value || ''"
            />

            <!-- Champ date -->
            <input
              v-else-if="field.type === 'date'"
              v-model="customProperties[field.nom]"
              type="date"
              class="form-input"
            />

            <!-- Champ select -->
            <select
              v-else-if="field.type === 'select'"
              v-model="customProperties[field.nom]"
              class="form-select"
            >
              <option value="">Sélectionner...</option>
              <option
                v-for="opt in field.options"
                :key="opt"
                :value="opt"
              >
                {{ opt }}
              </option>
            </select>

            <!-- Champ multiselect (checkboxes) -->
            <div v-else-if="field.type === 'multiselect'" class="checkbox-group">
              <label
                v-for="opt in field.options"
                :key="opt"
                class="checkbox-label"
              >
                <input
                  type="checkbox"
                  :value="opt"
                  :checked="Array.isArray(customProperties[field.nom]) && (customProperties[field.nom] as string[]).includes(opt)"
                  @change="toggleMultiselect(field.nom, opt)"
                />
                {{ opt }}
              </label>
            </div>

            <!-- Champ checkbox simple -->
            <label v-else-if="field.type === 'checkbox'" class="checkbox-label single">
              <input
                type="checkbox"
                v-model="customProperties[field.nom]"
              />
              Oui
            </label>

            <!-- Champ couleur -->
            <input
              v-else-if="field.type === 'color'"
              v-model="customProperties[field.nom]"
              type="color"
              class="form-color"
            />

            <!-- Fallback: champ texte -->
            <input
              v-else
              v-model="customProperties[field.nom]"
              type="text"
              class="form-input"
              :placeholder="field.default_value || ''"
            />
          </div>
        </div>

        <!-- Coordonnées info -->
        <div class="form-section">
          <h2>📍 Géométrie</h2>
          <div class="geom-info">
            <div class="geom-type-badge">
              {{ geomType === 'POINT' ? '📍 Point' : geomType === 'LINESTRING' ? '📏 Ligne' : '⬛ Zone' }}
            </div>
            <div class="geom-stats">
              {{ coordinates.length }} point(s)
              <span v-if="!isCoordinatesValid" class="geom-warning">
                ⚠️ {{ coordinatesError }}
              </span>
            </div>
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
              <button class="photo-delete" @click="removePhoto(index)">
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bouton Sauvegarder -->
    <div class="form-actions">
      <button
        class="btn btn-primary btn-block save-btn"
        :disabled="isSaving || !form.name"
        @click="save"
      >
        <span v-if="isSaving" class="spinner"></span>
        <span v-else>{{ isNew ? 'Créer' : 'Enregistrer' }}</span>
      </button>
    </div>

    <!-- Modal suppression -->
    <Teleport to="body">
      <div
        v-if="showDeleteConfirm"
        class="modal-overlay"
        @click.self="showDeleteConfirm = false"
      >
        <div class="confirm-modal">
          <h3>Supprimer cette géométrie ?</h3>
          <p>Cette action est irréversible.</p>
          <div class="confirm-actions">
            <button class="btn btn-secondary" @click="showDeleteConfirm = false">
              Annuler
            </button>
            <button class="btn btn-danger" @click="deleteGeometry">
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.geometry-form-page {
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

/* Tabs */
.tabs {
  display: flex;
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
}

.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.tab-badge {
  background: var(--primary-color);
  color: white;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
}

/* Content */
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map-tab {
  padding: 0;
}

.type-selector-wrapper {
  padding: 8px;
  flex-shrink: 0;
}

.drawing-wrapper {
  flex: 1;
  min-height: 0;
}

.form-tab {
  padding: 16px;
  padding-bottom: 100px;
  overflow-y: auto;
}

/* Form sections */
.form-section {
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

.form-section h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px;
}

.section-header h2 {
  margin: 0;
}

/* Geom info */
.geom-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.geom-type-badge {
  padding: 6px 12px;
  background: var(--primary-light);
  color: white;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.geom-stats {
  font-size: 14px;
  color: var(--text-secondary);
}

.geom-warning {
  display: block;
  margin-top: 4px;
  color: var(--warning-color);
  font-size: 12px;
}

/* Photos */
.add-photo-btn {
  padding: 6px 12px;
  background: var(--primary-light);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
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

/* Actions */
.form-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  padding-bottom: calc(var(--safe-area-inset-bottom) + 16px);
  background: var(--surface-color);
  border-top: 1px solid var(--border-color);
  z-index: 100;
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

/* Modal */
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

/* Dynamic fields */
.required {
  color: var(--error-color, #f44336);
  margin-left: 4px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.checkbox-label.single {
  margin-top: 4px;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--primary-color);
}

.form-color {
  width: 60px;
  height: 40px;
  padding: 4px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
}
</style>

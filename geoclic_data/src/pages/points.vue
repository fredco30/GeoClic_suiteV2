<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          Gestion des Points
          <HelpButton page-key="points" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          {{ total }} points au total
        </p>
      </div>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-map-marker-plus" to="/carte">
        Nouveau point
      </v-btn>
    </div>

    <!-- Filters -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="2">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Rechercher"
              clearable
              hide-details
              @update:model-value="debouncedSearch"
            />
          </v-col>
          <v-col cols="12" md="2">
            <v-select
              v-model="filterProjet"
              label="Projet"
              :items="projets"
              item-title="nom"
              item-value="id"
              clearable
              hide-details
              @update:model-value="applyFilters"
            />
          </v-col>
          <v-col cols="12" md="2">
            <v-autocomplete
              v-model="filterFamille"
              label="Famille"
              :items="familleOptions"
              item-title="libelle"
              item-value="code"
              clearable
              hide-details
              auto-select-first
              @update:model-value="onFamilleChange"
            />
          </v-col>
          <v-col cols="12" md="2">
            <v-autocomplete
              v-model="filterCategorie"
              label="Catégorie"
              :items="categorieOptions"
              item-title="libelle"
              item-value="code"
              clearable
              hide-details
              :disabled="!filterFamille"
              auto-select-first
              @update:model-value="onCategorieChange"
            />
          </v-col>
          <v-col cols="12" md="2">
            <v-autocomplete
              v-model="filterType"
              label="Type / Modèle"
              :items="typeOptions"
              item-title="libelle"
              item-value="code"
              clearable
              hide-details
              :disabled="!filterCategorie"
              auto-select-first
              @update:model-value="applyFilters"
            />
          </v-col>
          <v-col cols="12" md="2" class="d-flex gap-2 justify-end flex-wrap">
            <v-btn variant="outlined" size="small" @click="exportCSV">
              <v-icon start>mdi-file-excel</v-icon>
              CSV
            </v-btn>
            <v-btn variant="outlined" size="small" @click="exportGeoJSON">
              <v-icon start>mdi-code-json</v-icon>
              GeoJSON
            </v-btn>
            <v-btn variant="outlined" size="small" color="secondary" @click="openPhotoExport">
              <v-icon start>mdi-image-multiple</v-icon>
              Photos
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Points table -->
    <v-card>
      <v-data-table
        :headers="headers"
        :items="points"
        :loading="loading"
        :items-per-page="pagination.page_size"
        :page="pagination.page"
        @update:page="onPageChange"
        hover
      >
        <template v-slot:item.nom="{ item }">
          <div class="d-flex align-center">
            <v-avatar
              :color="getValidColor(getCategory(item.lexique_code || item.lexique_id)?.couleur)"
              size="32"
              class="mr-3"
            >
              <v-icon size="16" color="white">
                {{ getCategory(item.lexique_code || item.lexique_id)?.icone || 'mdi-map-marker' }}
              </v-icon>
            </v-avatar>
            <div>
              <div class="font-weight-medium">{{ item.name || item.nom }}</div>
              <div class="text-caption text-grey" v-if="item.comment || item.description">
                {{ truncate(item.comment || item.description || '', 50) }}
              </div>
            </div>
          </div>
        </template>

        <template v-slot:item.famille="{ item }">
          <span class="text-body-2">
            {{ getHierarchy(item.lexique_code || item.lexique_id).famille || '-' }}
          </span>
        </template>

        <template v-slot:item.categorie="{ item }">
          <span class="text-body-2">
            {{ getHierarchy(item.lexique_code || item.lexique_id).categorie || '-' }}
          </span>
        </template>

        <template v-slot:item.type_lexique="{ item }">
          <v-chip size="small" :color="getValidColor(getCategory(item.lexique_code || item.lexique_id)?.couleur)">
            {{ getHierarchy(item.lexique_code || item.lexique_id).type || getCategory(item.lexique_code || item.lexique_id)?.libelle || '-' }}
          </v-chip>
        </template>

        <template v-slot:item.projet="{ item }">
          {{ getProjet(item.project_id || item.projet_id)?.nom || '-' }}
        </template>

        <template v-slot:item.coords="{ item }">
          <span class="text-caption font-monospace">
            {{ item.latitude.toFixed(4) }}, {{ item.longitude.toFixed(4) }}
          </span>
        </template>

        <template v-slot:item.synced="{ item }">
          <v-icon :color="(item.sync_status === 'validated' || item.synced) ? 'success' : 'warning'" size="small">
            {{ (item.sync_status === 'validated' || item.synced) ? 'mdi-cloud-check' : 'mdi-cloud-sync' }}
          </v-icon>
        </template>

        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn icon size="small" variant="text" @click="viewOnMap(item)">
            <v-icon>mdi-map</v-icon>
            <v-tooltip activator="parent" location="top">Voir sur la carte</v-tooltip>
          </v-btn>
          <v-btn icon size="small" variant="text" @click="editPoint(item)">
            <v-icon>mdi-pencil</v-icon>
            <v-tooltip activator="parent" location="top">Modifier</v-tooltip>
          </v-btn>
          <v-btn icon size="small" variant="text" color="error" @click="confirmDelete(item)">
            <v-icon>mdi-delete</v-icon>
            <v-tooltip activator="parent" location="top">Supprimer</v-tooltip>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Edit dialog -->
    <v-dialog v-model="showEditDialog" max-width="700" persistent>
      <v-card>
        <v-card-title>Modifier le point</v-card-title>
        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <v-text-field
              v-model="editForm.nom"
              label="Nom du point *"
              :rules="[v => !!v || 'Nom requis']"
            />
            <v-textarea
              v-model="editForm.description"
              label="Description"
              rows="2"
              class="mt-4"
            />
            <v-row class="mt-4">
              <v-col cols="6">
                <v-text-field
                  v-model.number="editForm.latitude"
                  label="Latitude"
                  type="number"
                  step="0.000001"
                  readonly
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="editForm.longitude"
                  label="Longitude"
                  type="number"
                  step="0.000001"
                  readonly
                />
              </v-col>
            </v-row>

            <!-- Photos -->
            <template v-if="editForm.photos?.length">
              <v-divider class="my-4" />
              <div class="text-subtitle-2 mb-2">Photos ({{ editForm.photos.length }})</div>
              <div class="d-flex flex-wrap gap-2">
                <div
                  v-for="(photo, index) in editForm.photos"
                  :key="index"
                  class="photo-item position-relative"
                >
                  <v-img
                    :src="getPhotoUrl(photo, true)"
                    width="100"
                    height="100"
                    cover
                    class="rounded cursor-pointer"
                    @click="openPhotoViewer(photo)"
                  >
                    <template v-slot:placeholder>
                      <div class="d-flex align-center justify-center fill-height bg-grey-lighten-2">
                        <v-progress-circular indeterminate size="20" />
                      </div>
                    </template>
                  </v-img>
                  <v-btn
                    icon
                    size="x-small"
                    color="error"
                    class="photo-delete-btn"
                    @click.stop="confirmDeletePhoto(index)"
                  >
                    <v-icon size="small">mdi-close</v-icon>
                  </v-btn>
                </div>
              </div>
            </template>

            <v-select
              v-model="editForm.lexique_id"
              label="Catégorie"
              :items="allCategories"
              item-title="libelle"
              item-value="id"
              class="mt-4"
            />
            <v-select
              v-model="editForm.projet_id"
              label="Projet"
              :items="projets"
              item-title="nom"
              item-value="id"
              class="mt-4"
            />

            <!-- Données techniques -->
            <v-divider class="my-4" />
            <div class="text-subtitle-2 mb-2">Données techniques</div>
            <v-row v-for="(value, key) in editForm.donnees_techniques" :key="key" dense>
              <v-col cols="4">
                <v-text-field
                  :model-value="key"
                  label="Champ"
                  readonly
                  density="compact"
                />
              </v-col>
              <v-col cols="8">
                <v-text-field
                  v-model="editForm.donnees_techniques[key]"
                  label="Valeur"
                  density="compact"
                />
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showEditDialog = false">Annuler</v-btn>
          <v-btn color="primary" :disabled="!formValid" @click="savePoint">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">Supprimer le point</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer le point
          <strong>{{ selectedPoint?.nom }}</strong> ?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Annuler</v-btn>
          <v-btn color="error" @click="deletePoint">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete photo dialog -->
    <v-dialog v-model="showDeletePhotoDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">Supprimer la photo</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer cette photo ?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeletePhotoDialog = false">Annuler</v-btn>
          <v-btn color="error" @click="deletePhoto">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Photo viewer dialog -->
    <v-dialog v-model="showPhotoViewer" max-width="900">
      <v-card>
        <v-img
          :src="getPhotoUrl(viewingPhoto, false)"
          max-height="80vh"
          contain
        />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showPhotoViewer = false">Fermer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Photo export dialog -->
    <v-dialog v-model="showPhotoExportDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon start color="secondary">mdi-image-multiple</v-icon>
          Export des photos
        </v-card-title>
        <v-card-text>
          <div v-if="photoExportLoading" class="text-center py-4">
            <v-progress-circular indeterminate color="primary" />
            <p class="mt-2">Analyse en cours...</p>
          </div>

          <div v-else-if="photoExportInfo">
            <v-alert
              v-if="!photoExportInfo.can_export && photoExportInfo.message"
              type="warning"
              variant="tonal"
              class="mb-4"
            >
              {{ photoExportInfo.message }}
            </v-alert>

            <v-alert
              v-else-if="photoExportInfo.can_export"
              type="info"
              variant="tonal"
              class="mb-4"
            >
              Export prêt: <strong>{{ photoExportInfo.total_photos }}</strong> photo(s)
              de <strong>{{ photoExportInfo.total_points }}</strong> point(s)
            </v-alert>

            <div class="text-body-2 mb-4">
              <p><strong>Filtres actuels:</strong></p>
              <ul class="ml-4">
                <li v-if="filterProjet">Projet: {{ getProjet(filterProjet)?.nom }}</li>
                <li v-if="filterCategorie">Catégorie: {{ getCategory(filterCategorie)?.libelle }}</li>
                <li v-if="search">Recherche: "{{ search }}"</li>
                <li v-if="!filterProjet && !filterCategorie && !search">Aucun filtre (tous les points)</li>
              </ul>
            </div>

            <v-divider class="my-3" />

            <div class="text-body-2">
              <p><strong>Contenu du ZIP:</strong></p>
              <ul class="ml-4">
                <li>Photos originales (noms conservés)</li>
                <li>metadata.csv (compatible Excel/QGIS)</li>
                <li>metadata.json (scripts/développement)</li>
              </ul>
            </div>
          </div>

          <div v-if="photoExportDownloading" class="mt-4">
            <v-progress-linear indeterminate color="secondary" />
            <p class="text-center mt-2 text-caption">Génération du ZIP en cours...</p>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showPhotoExportDialog = false">Annuler</v-btn>
          <v-btn
            color="secondary"
            :disabled="!photoExportInfo?.can_export || photoExportDownloading"
            :loading="photoExportDownloading"
            @click="downloadPhotosExport"
          >
            <v-icon start>mdi-download</v-icon>
            Télécharger
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import HelpButton from '@/components/help/HelpButton.vue'
import { usePointsStore, type Point } from '@/stores/points'
import { useLexiqueStore } from '@/stores/lexique'
import { projetsAPI } from '@/services/api'

defineOptions({
  meta: {
    layout: 'admin',
  },
})

const router = useRouter()
const pointsStore = usePointsStore()
const lexiqueStore = useLexiqueStore()

// State
const search = ref('')
const filterProjet = ref<string | null>(null)
const filterFamille = ref<string | null>(null)
const filterCategorie = ref<string | null>(null)
const filterType = ref<string | null>(null)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showDeletePhotoDialog = ref(false)
const showPhotoViewer = ref(false)
const showPhotoExportDialog = ref(false)
const photoExportLoading = ref(false)
const photoExportDownloading = ref(false)
const photoExportInfo = ref<{ total_photos: number; total_points: number; can_export: boolean; message?: string } | null>(null)
const selectedPoint = ref<Point | null>(null)
const formValid = ref(false)
const projets = ref<any[]>([])
const photoToDeleteIndex = ref<number | null>(null)
const viewingPhoto = ref<any>(null)

const editForm = ref({
  nom: '',
  description: '',
  latitude: 0,
  longitude: 0,
  lexique_id: '',
  projet_id: '',
  donnees_techniques: {} as Record<string, any>,
  photos: [] as any[],
})

// Debounce timer
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// Headers
const headers = [
  { title: 'Point', key: 'nom', width: '20%' },
  { title: 'Famille', key: 'famille', width: '12%' },
  { title: 'Catégorie', key: 'categorie', width: '12%' },
  { title: 'Type', key: 'type_lexique', width: '10%' },
  { title: 'Projet', key: 'projet', width: '12%' },
  { title: 'Coordonnées', key: 'coords', width: '12%' },
  { title: 'Sync', key: 'synced', width: '5%' },
  { title: 'Actions', key: 'actions', sortable: false, width: '17%' },
]

// Computed
const loading = computed(() => pointsStore.loading)
const points = computed(() => pointsStore.points)
const total = computed(() => pointsStore.total)
const pagination = computed(() => pointsStore.pagination)
// Filtres cascade: Famille (N0) → Catégorie (N1) → Type (N2)
const familleOptions = computed(() =>
  lexiqueStore.entries.filter(e => e.niveau === 0).sort((a, b) => a.libelle.localeCompare(b.libelle))
)
const categorieOptions = computed(() => {
  if (!filterFamille.value) return []
  return lexiqueStore.entries
    .filter(e => e.niveau === 1 && e.parent_id === filterFamille.value)
    .sort((a, b) => a.libelle.localeCompare(b.libelle))
})
const typeOptions = computed(() => {
  if (!filterCategorie.value) return []
  return lexiqueStore.entries
    .filter(e => e.niveau === 2 && e.parent_id === filterCategorie.value)
    .sort((a, b) => a.libelle.localeCompare(b.libelle))
})
const allCategories = computed(() => lexiqueStore.entries)

// Methods

/**
 * Valide et retourne une couleur hexadécimale valide
 * Retourne 'primary' si la couleur est invalide
 */
function getValidColor(color: string | undefined | null): string {
  if (!color) return 'primary'
  // Regex pour couleur hex valide: #RGB, #RRGGBB, #RRGGBBAA
  const hexRegex = /^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$/
  if (hexRegex.test(color)) return color
  // Si c'est un nom de couleur Vuetify (sans #), on le retourne
  if (!color.startsWith('#')) return color
  // Sinon, couleur par défaut
  return 'primary'
}

function getCategory(lexiqueId: string | undefined) {
  if (!lexiqueId) return null
  return lexiqueStore.getByCode(lexiqueId) || lexiqueStore.getById(lexiqueId)
}

/**
 * Récupère la hiérarchie complète d'un lexique_code
 * Retourne { famille (N0), categorie (N1), type (N2) }
 */
function getHierarchy(lexiqueCode: string | undefined): { famille: string | null, categorie: string | null, type: string | null } {
  if (!lexiqueCode) return { famille: null, categorie: null, type: null }

  const entry = lexiqueStore.getByCode(lexiqueCode)
  if (!entry) return { famille: null, categorie: null, type: null }

  // Remonter la hiérarchie
  const hierarchy: any[] = [entry]
  let current = entry
  while (current.parent_id) {
    const parent = lexiqueStore.getByCode(current.parent_id) || lexiqueStore.getById(current.parent_id)
    if (parent) {
      hierarchy.unshift(parent)
      current = parent
    } else {
      break
    }
  }

  // Mapper selon les niveaux
  return {
    famille: hierarchy.find(h => h.niveau === 0)?.libelle || null,
    categorie: hierarchy.find(h => h.niveau === 1)?.libelle || null,
    type: hierarchy.find(h => h.niveau === 2)?.libelle || null,
  }
}

function getProjet(projetId: string | undefined) {
  if (!projetId) return null
  return projets.value.find(p => p.id === projetId)
}

function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    applyFilters()
  }, 300)
}

function onFamilleChange() {
  filterCategorie.value = null
  filterType.value = null
  applyFilters()
}

function onCategorieChange() {
  filterType.value = null
  applyFilters()
}

async function applyFilters() {
  // Utiliser le filtre le plus précis disponible
  const lexiqueId = filterType.value || filterCategorie.value || filterFamille.value || null
  pointsStore.setFilters({
    projet_id: filterProjet.value,
    lexique_id: lexiqueId,
    search: search.value,
  })
  await pointsStore.fetchPoints()
}

function onPageChange(page: number) {
  pointsStore.pagination.page = page
  pointsStore.fetchPoints()
}

function viewOnMap(point: Point) {
  router.push({
    path: '/carte',
    query: { point: point.id },
  })
}

function editPoint(point: Point) {
  selectedPoint.value = point
  editForm.value = {
    nom: point.name || point.nom || '',
    description: point.comment || point.description || '',
    latitude: point.latitude,
    longitude: point.longitude,
    lexique_id: point.lexique_code || point.lexique_id || '',
    projet_id: point.project_id || point.projet_id || '',
    donnees_techniques: { ...(point.custom_properties || point.donnees_techniques || {}) },
    photos: [...(point.photos || [])],
  }
  showEditDialog.value = true
}

function getPhotoUrl(photo: any, _useThumbnail: boolean = false): string {
  if (!photo) return ''
  if (typeof photo === 'string') return photo
  // Thumbnail désactivée - on utilise toujours l'URL principale
  return photo.url || ''
}

function openPhotoViewer(photo: any) {
  viewingPhoto.value = photo
  showPhotoViewer.value = true
}

function confirmDeletePhoto(index: number) {
  photoToDeleteIndex.value = index
  showDeletePhotoDialog.value = true
}

async function deletePhoto() {
  if (photoToDeleteIndex.value === null || !selectedPoint.value) return

  const photoToDelete = editForm.value.photos[photoToDeleteIndex.value]

  // Supprimer la photo via l'API
  try {
    const photoId = photoToDelete.id || photoToDelete.url?.split('/').pop()?.replace('.jpg', '')
    if (photoId) {
      await fetch(`/api/photos/${photoId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('data_auth_token')}`,
        },
      })
    }
  } catch (e) {
    console.error('Erreur suppression photo:', e)
  }

  // Supprimer de la liste locale
  editForm.value.photos.splice(photoToDeleteIndex.value, 1)

  // Fermer le dialog
  showDeletePhotoDialog.value = false
  photoToDeleteIndex.value = null
}

async function savePoint() {
  if (!selectedPoint.value) return
  await pointsStore.updatePoint(selectedPoint.value.id, editForm.value)
  showEditDialog.value = false
}

function confirmDelete(point: Point) {
  selectedPoint.value = point
  showDeleteDialog.value = true
}

async function deletePoint() {
  if (!selectedPoint.value) return
  await pointsStore.deletePoint(selectedPoint.value.id)
  showDeleteDialog.value = false
}

async function exportCSV() {
  const blob = await pointsStore.exportCSV()
  if (blob) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'points_export.csv'
    a.click()
    URL.revokeObjectURL(url)
  }
}

async function exportGeoJSON() {
  const geojson = await pointsStore.getGeoJSON()
  if (geojson) {
    const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'points_export.geojson'
    a.click()
    URL.revokeObjectURL(url)
  }
}

async function openPhotoExport() {
  showPhotoExportDialog.value = true
  photoExportLoading.value = true
  photoExportInfo.value = null

  try {
    const response = await fetch('/api/photos/export/info', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('data_auth_token')}`,
      },
      body: JSON.stringify({
        project_id: filterProjet.value || undefined,
        lexique_code: filterCategorie.value || undefined,
      }),
    })

    if (!response.ok) {
      throw new Error('Erreur lors de la récupération des informations')
    }

    photoExportInfo.value = await response.json()
  } catch (error) {
    console.error('Erreur info export photos:', error)
    photoExportInfo.value = {
      total_photos: 0,
      total_points: 0,
      can_export: false,
      message: 'Erreur lors de la récupération des informations',
    }
  } finally {
    photoExportLoading.value = false
  }
}

async function downloadPhotosExport() {
  photoExportDownloading.value = true

  try {
    const response = await fetch('/api/photos/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('data_auth_token')}`,
      },
      body: JSON.stringify({
        project_id: filterProjet.value || undefined,
        lexique_code: filterCategorie.value || undefined,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Erreur lors de l\'export')
    }

    // Télécharger le fichier ZIP
    const blob = await response.blob()
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = 'export_photos.zip'
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=(.+)/)
      if (match) {
        filename = match[1]
      }
    }

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)

    showPhotoExportDialog.value = false
  } catch (error) {
    console.error('Erreur export photos:', error)
    alert('Erreur lors de l\'export des photos: ' + (error as Error).message)
  } finally {
    photoExportDownloading.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await lexiqueStore.fetchAll()
  try {
    projets.value = await projetsAPI.getAll()
  } catch (e) {
    console.error('Erreur chargement projets:', e)
  }

  // Check for search query param
  const urlParams = new URLSearchParams(window.location.search)
  if (urlParams.has('search')) {
    search.value = urlParams.get('search') || ''
  }

  await applyFilters()
})
</script>

<style scoped>
.photo-item {
  position: relative;
}

.photo-delete-btn {
  position: absolute;
  top: -8px;
  right: -8px;
}

.cursor-pointer {
  cursor: pointer;
}
</style>

<template>
  <div>
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          Exports
          <HelpButton page-key="exports" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          Téléchargez vos données dans différents formats
        </p>
      </div>
    </div>

    <v-row>
      <!-- Filtres -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-filter</v-icon>
            Filtres
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="selectedProjet"
              label="Projet"
              :items="projets"
              item-title="nom"
              item-value="id"
              clearable
            />
            <v-select
              v-model="selectedCategorie"
              label="Catégorie"
              :items="categories"
              item-title="libelle"
              item-value="code"
              clearable
              class="mt-4"
            />
            <v-text-field
              v-model="dateDebut"
              label="Date début"
              type="date"
              class="mt-4"
            />
            <v-text-field
              v-model="dateFin"
              label="Date fin"
              type="date"
              class="mt-4"
            />
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Formats d'export -->
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-file-export</v-icon>
            Formats disponibles
          </v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item @click="exportFormat('csv')">
                <template v-slot:prepend>
                  <v-avatar color="success" size="40">
                    <v-icon>mdi-file-excel</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>CSV (Excel)</v-list-item-title>
                <v-list-item-subtitle>
                  Tableur compatible Excel, LibreOffice, Google Sheets
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn icon variant="text">
                    <v-icon>mdi-download</v-icon>
                  </v-btn>
                </template>
              </v-list-item>

              <v-divider />

              <v-list-item @click="exportFormat('geojson')">
                <template v-slot:prepend>
                  <v-avatar color="primary" size="40">
                    <v-icon>mdi-code-json</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>GeoJSON</v-list-item-title>
                <v-list-item-subtitle>
                  Format géographique pour QGIS, MapBox, Leaflet
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn icon variant="text">
                    <v-icon>mdi-download</v-icon>
                  </v-btn>
                </template>
              </v-list-item>

              <v-divider />

              <v-list-item @click="exportFormat('shapefile')">
                <template v-slot:prepend>
                  <v-avatar color="warning" size="40">
                    <v-icon>mdi-shape</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>Shapefile</v-list-item-title>
                <v-list-item-subtitle>
                  Format SIG classique (ESRI) - ZIP contenant .shp, .dbf, .shx
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn icon variant="text">
                    <v-icon>mdi-download</v-icon>
                  </v-btn>
                </template>
              </v-list-item>

              <v-divider />

              <v-list-item @click="exportFormat('kml')">
                <template v-slot:prepend>
                  <v-avatar color="error" size="40">
                    <v-icon>mdi-google-earth</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>KML (Google Earth)</v-list-item-title>
                <v-list-item-subtitle>
                  Compatible Google Earth et Google Maps
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn icon variant="text">
                    <v-icon>mdi-download</v-icon>
                  </v-btn>
                </template>
              </v-list-item>

              <v-divider />

              <v-list-item @click="exportFormat('pdf')">
                <template v-slot:prepend>
                  <v-avatar color="secondary" size="40">
                    <v-icon>mdi-file-pdf-box</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>PDF (Rapport)</v-list-item-title>
                <v-list-item-subtitle>
                  Rapport PDF avec carte et tableau des points
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn icon variant="text">
                    <v-icon>mdi-download</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- Export Photos -->
        <v-card class="mt-4">
          <v-card-title>
            <v-icon class="mr-2" color="secondary">mdi-image-multiple</v-icon>
            Export des photos
          </v-card-title>
          <v-card-text>
            <p class="text-body-2 mb-4">
              Téléchargez les photos des points en archive ZIP avec métadonnées (CSV + JSON).
              Les noms de fichiers originaux sont conservés pour compatibilité SIG.
            </p>

            <v-alert
              v-if="photoExportLoading"
              type="info"
              variant="tonal"
              class="mb-4"
            >
              <v-progress-circular indeterminate size="16" class="mr-2" />
              Analyse en cours...
            </v-alert>

            <v-alert
              v-else-if="photoExportInfo && !photoExportInfo.can_export"
              type="warning"
              variant="tonal"
              class="mb-4"
            >
              {{ photoExportInfo.message }}
            </v-alert>

            <v-alert
              v-else-if="photoExportInfo && photoExportInfo.can_export"
              type="success"
              variant="tonal"
              class="mb-4"
            >
              <strong>{{ photoExportInfo.total_photos }}</strong> photo(s) disponible(s)
              pour <strong>{{ photoExportInfo.total_points }}</strong> point(s)
            </v-alert>

            <div class="text-body-2 mb-4">
              <strong>Contenu du ZIP:</strong>
              <ul class="ml-4 mt-1">
                <li>Photos originales (noms conservés)</li>
                <li>metadata.csv (Excel, QGIS)</li>
                <li>metadata.json (scripts, développement)</li>
              </ul>
            </div>

            <v-btn
              color="secondary"
              :disabled="!photoExportInfo?.can_export || photoExportDownloading"
              :loading="photoExportDownloading"
              @click="downloadPhotos"
              block
            >
              <v-icon start>mdi-download</v-icon>
              Télécharger les photos (ZIP)
            </v-btn>

            <p class="text-caption text-grey mt-2 text-center">
              Maximum 500 photos par export
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Export en cours -->
    <v-dialog v-model="exporting" persistent max-width="300">
      <v-card class="text-center pa-6">
        <v-progress-circular indeterminate color="primary" size="64" class="mb-4" />
        <p>Export en cours...</p>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, watch } from 'vue'
import { projetsAPI, pointsAPI } from '@/services/api'
import { useLexiqueStore } from '@/stores/lexique'
import HelpButton from '@/components/help/HelpButton.vue'

const lexiqueStore = useLexiqueStore()

const projets = ref<any[]>([])
const categories = ref<any[]>([])
const selectedProjet = ref<string | null>(null)
const selectedCategorie = ref<string | null>(null)
const dateDebut = ref('')
const dateFin = ref('')
const exporting = ref(false)
const photoExportLoading = ref(false)
const photoExportDownloading = ref(false)
const photoExportInfo = ref<{ total_photos: number; total_points: number; can_export: boolean; message?: string } | null>(null)

async function exportFormat(format: string) {
  exporting.value = true

  try {
    let blob: Blob | null = null
    let filename = `geoclic_export_${new Date().toISOString().split('T')[0]}`

    // Paramètres communs avec filtres
    const params = {
      project_id: selectedProjet.value || undefined,
      lexique_code: selectedCategorie.value || undefined,
      date_start: dateDebut.value || undefined,
      date_end: dateFin.value || undefined,
    }

    switch (format) {
      case 'csv':
        blob = await pointsAPI.exportCSV(params)
        filename += '.csv'
        break
      case 'geojson':
        const geojson = await pointsAPI.getGeoJSON(params)
        blob = new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/geo+json' })
        filename += '.geojson'
        break
      default:
        alert(`Export ${format} non implémenté - prévu pour une version future`)
        exporting.value = false
        return
    }

    if (blob) {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch (e) {
    console.error('Erreur export:', e)
    alert('Erreur lors de l\'export. Vérifiez la console pour plus de détails.')
  } finally {
    exporting.value = false
  }
}

async function fetchPhotoExportInfo() {
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
        project_id: selectedProjet.value || undefined,
        lexique_code: selectedCategorie.value || undefined,
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

async function downloadPhotos() {
  photoExportDownloading.value = true

  try {
    const response = await fetch('/api/photos/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('data_auth_token')}`,
      },
      body: JSON.stringify({
        project_id: selectedProjet.value || undefined,
        lexique_code: selectedCategorie.value || undefined,
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
  } catch (error) {
    console.error('Erreur export photos:', error)
    alert('Erreur lors de l\'export des photos: ' + (error as Error).message)
  } finally {
    photoExportDownloading.value = false
  }
}

// Watcher pour mettre à jour les infos photo quand les filtres changent
watch([selectedProjet, selectedCategorie], () => {
  fetchPhotoExportInfo()
})

onMounted(async () => {
  try {
    projets.value = await projetsAPI.getAll()
  } catch (e) {
    console.error('Erreur chargement projets:', e)
  }
  await lexiqueStore.fetchAll()
  categories.value = lexiqueStore.entries.filter(e => e.niveau === 1)

  // Charger les infos d'export photos
  fetchPhotoExportInfo()
})
</script>

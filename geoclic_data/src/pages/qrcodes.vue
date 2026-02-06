<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          Génération de QR Codes
          <HelpButton page-key="qrcodes" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          Générez des étiquettes QR pour vos équipements
        </p>
      </div>
    </div>

    <v-row>
      <!-- Configuration -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-cog</v-icon>
            Configuration
          </v-card-title>
          <v-card-text>
            <!-- Sélection des points -->
            <v-select
              v-model="selectedProjet"
              label="Filtrer par projet"
              :items="projets"
              item-title="nom"
              item-value="id"
              clearable
              @update:model-value="loadPoints"
            />

            <v-select
              v-model="selectedCategorie"
              label="Filtrer par catégorie"
              :items="categories"
              item-title="libelle"
              item-value="id"
              clearable
              class="mt-4"
              @update:model-value="loadPoints"
            />

            <v-divider class="my-4" />

            <!-- Format d'étiquette -->
            <div class="text-subtitle-2 mb-2">Format d'étiquette</div>
            <v-radio-group v-model="labelFormat" inline>
              <v-radio label="Petit (2cm)" value="small" />
              <v-radio label="Moyen (4cm)" value="medium" />
              <v-radio label="Grand (6cm)" value="large" />
            </v-radio-group>

            <v-divider class="my-4" />

            <!-- Options -->
            <div class="text-subtitle-2 mb-2">Options</div>
            <v-checkbox
              v-model="includeText"
              label="Inclure le nom du point"
              hide-details
              density="compact"
            />
            <v-checkbox
              v-model="includeLocation"
              label="Inclure l'adresse/lieu"
              hide-details
              density="compact"
            />
            <v-checkbox
              v-model="includeLogo"
              label="Inclure le logo"
              hide-details
              density="compact"
            />

            <v-divider class="my-4" />

            <!-- Format de sortie -->
            <div class="text-subtitle-2 mb-2">Format de sortie</div>
            <v-radio-group v-model="outputFormat">
              <v-radio label="PDF - Planche A4 (24 étiquettes)" value="pdf_a4" />
              <v-radio label="PDF - Étiquettes individuelles" value="pdf_single" />
              <v-radio label="ZIP - Images PNG" value="zip_png" />
            </v-radio-group>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Sélection des points -->
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-map-marker-multiple</v-icon>
            Sélection des points
            <v-spacer />
            <v-chip color="primary" class="mr-2">
              {{ selectedPoints.length }} sélectionné(s)
            </v-chip>
            <v-btn
              v-if="selectedPoints.length"
              color="primary"
              @click="generateQRCodes"
              :loading="generating"
            >
              <v-icon start>mdi-qrcode</v-icon>
              Générer
            </v-btn>
          </v-card-title>

          <v-card-text class="pa-0">
            <v-data-table
              v-model="selectedPoints"
              :headers="headers"
              :items="points"
              :loading="loading"
              show-select
              item-value="id"
              hover
            >
              <template v-slot:item.nom="{ item }">
                <div class="d-flex align-center">
                  <v-icon :color="item.couleur || undefined" class="mr-2" size="small">
                    {{ item.icone || 'mdi-map-marker' }}
                  </v-icon>
                  {{ item.nom }}
                </div>
              </template>

              <template v-slot:item.categorie="{ item }">
                <v-chip size="small">{{ getCategoryName(item.lexique_code || item.lexique_id || '') }}</v-chip>
              </template>

              <template v-slot:item.preview="{ item }">
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  @click="previewQR(item)"
                >
                  <v-icon>mdi-eye</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>

          <v-card-actions v-if="points.length">
            <v-btn variant="text" @click="selectAll">Tout sélectionner</v-btn>
            <v-btn variant="text" @click="clearSelection">Tout désélectionner</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Aperçu QR -->
    <v-dialog v-model="showPreview" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          Aperçu QR Code
          <v-spacer />
          <v-btn icon size="small" variant="text" @click="showPreview = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="text-center">
          <div class="qr-preview-container" ref="qrPreviewContainer">
            <canvas ref="qrCanvas" />
            <div v-if="includeText" class="qr-label mt-2">
              <strong>{{ previewPoint?.nom }}</strong>
            </div>
            <div v-if="includeLocation" class="qr-location text-caption text-grey">
              {{ previewPoint?.latitude.toFixed(4) }}, {{ previewPoint?.longitude.toFixed(4) }}
            </div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="downloadSingleQR">
            <v-icon start>mdi-download</v-icon>
            Télécharger
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Génération en cours -->
    <v-dialog v-model="generating" persistent max-width="300">
      <v-card>
        <v-card-text class="text-center pa-6">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
            class="mb-4"
          />
          <p>Génération en cours...</p>
          <p class="text-caption text-grey">{{ generationProgress }}</p>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { usePointsStore, type Point } from '@/stores/points'
import HelpButton from '@/components/help/HelpButton.vue'
import { useLexiqueStore } from '@/stores/lexique'
import { projetsAPI, qrcodesAPI } from '@/services/api'
import QRCode from 'qrcode'

defineOptions({
  meta: {
    layout: 'admin',
  },
})

const pointsStore = usePointsStore()
const lexiqueStore = useLexiqueStore()

// Refs
const qrCanvas = ref<HTMLCanvasElement | null>(null)
const qrPreviewContainer = ref<HTMLElement | null>(null)

// State
const selectedProjet = ref<string | null>(null)
const selectedCategorie = ref<string | null>(null)
const selectedPoints = ref<string[]>([])
const labelFormat = ref('medium')
const outputFormat = ref('pdf_a4')
const includeText = ref(true)
const includeLocation = ref(false)
const includeLogo = ref(false)
const loading = ref(false)
const generating = ref(false)
const generationProgress = ref('')
const showPreview = ref(false)
const previewPoint = ref<Point | null>(null)
const projets = ref<any[]>([])

// Table headers
const headers = [
  { title: 'Nom', key: 'nom' },
  { title: 'Catégorie', key: 'categorie' },
  { title: 'Projet', key: 'projet' },
  { title: 'Aperçu', key: 'preview', sortable: false, width: 80 },
]

// Computed
const points = computed(() => pointsStore.points)
const categories = computed(() => lexiqueStore.entries.filter(e => e.niveau === 1))

// Methods
async function loadPoints() {
  loading.value = true
  pointsStore.setFilters({
    projet_id: selectedProjet.value,
    lexique_id: selectedCategorie.value,
  })
  await pointsStore.fetchPoints()
  loading.value = false
}

function getCategoryName(lexiqueId: string): string {
  const cat = lexiqueStore.getById(lexiqueId)
  return cat?.libelle || 'Inconnu'
}

function selectAll() {
  selectedPoints.value = points.value.map(p => p.id)
}

function clearSelection() {
  selectedPoints.value = []
}

async function previewQR(point: Point) {
  previewPoint.value = point
  showPreview.value = true

  await nextTick()

  if (qrCanvas.value) {
    const url = `${window.location.origin}/point/${point.id}`
    const size = labelFormat.value === 'small' ? 100 : labelFormat.value === 'medium' ? 150 : 200

    await QRCode.toCanvas(qrCanvas.value, url, {
      width: size,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#FFFFFF',
      },
    })
  }
}

async function downloadSingleQR() {
  if (!previewPoint.value || !qrCanvas.value) return

  const link = document.createElement('a')
  const pointName = previewPoint.value.name || previewPoint.value.nom || 'point'
  link.download = `qr_${pointName.replace(/\s+/g, '_')}.png`
  link.href = qrCanvas.value.toDataURL('image/png')
  link.click()
}

async function generateQRCodes() {
  if (selectedPoints.value.length === 0) return

  generating.value = true
  generationProgress.value = `0 / ${selectedPoints.value.length}`

  try {
    const format = outputFormat.value.startsWith('pdf') ? 'pdf' : 'png'
    const blob = await qrcodesAPI.generateBatch(selectedPoints.value, format)

    // Download the file
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url

    if (outputFormat.value === 'pdf_a4') {
      a.download = 'qrcodes_planche.pdf'
    } else if (outputFormat.value === 'pdf_single') {
      a.download = 'qrcodes_individuels.pdf'
    } else {
      a.download = 'qrcodes.zip'
    }

    a.click()
    URL.revokeObjectURL(url)

    generationProgress.value = 'Terminé !'
  } catch (error) {
    console.error('Erreur génération QR:', error)
    generationProgress.value = 'Erreur lors de la génération'
  } finally {
    setTimeout(() => {
      generating.value = false
    }, 1000)
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
  await loadPoints()
})
</script>

<style scoped>
.qr-preview-container {
  display: inline-block;
  padding: 16px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.qr-label {
  font-size: 14px;
}

.qr-location {
  font-size: 11px;
}
</style>

<template>
  <v-container fluid>
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          Gestion des Zones
          <HelpButton page-key="zones" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          Quartiers et secteurs géographiques pour filtrer et organiser vos données
        </p>
      </div>
      <div class="d-flex gap-2">
        <v-btn
          color="secondary"
          variant="outlined"
          prepend-icon="mdi-download"
          @click="showImportDialog = true"
        >
          Importer IRIS
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          to="/zones/nouvelle"
        >
          Créer une zone
        </v-btn>
      </div>
    </div>

    <!-- Stats Cards -->
    <v-row class="mb-4">
      <v-col cols="12" md="3">
        <v-card variant="outlined">
          <v-card-text class="d-flex align-center">
            <v-icon color="primary" size="40" class="mr-4">mdi-map-marker-radius</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ zones.length }}</div>
              <div class="text-body-2 text-grey">Zones définies</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="outlined">
          <v-card-text class="d-flex align-center">
            <v-icon color="success" size="40" class="mr-4">mdi-map-marker-check</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ totalPoints }}</div>
              <div class="text-body-2 text-grey">Points localisés</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="outlined">
          <v-card-text class="d-flex align-center">
            <v-icon color="info" size="40" class="mr-4">mdi-home-city</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ quartierCount }}</div>
              <div class="text-body-2 text-grey">Quartiers</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="outlined">
          <v-card-text class="d-flex align-center">
            <v-icon color="warning" size="40" class="mr-4">mdi-domain</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ communeCount }}</div>
              <div class="text-body-2 text-grey">Communes</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filters -->
    <v-card variant="outlined" class="mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="search"
              label="Rechercher"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filterLevel"
              :items="levelOptions"
              label="Niveau"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filterType"
              :items="zoneTypes"
              label="Type de zone"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Zones Table -->
    <v-card>
      <v-data-table
        :headers="headers"
        :items="filteredZones"
        :loading="loading"
        :search="search"
        class="elevation-0"
        hover
      >
        <template #item.name="{ item }">
          <div class="d-flex align-center">
            <v-icon
              :icon="getLevelIcon(item.level)"
              :color="getLevelColor(item.level)"
              size="small"
              class="mr-2"
            />
            <span class="font-weight-medium">{{ item.name }}</span>
          </div>
        </template>

        <template #item.level="{ item }">
          <v-chip
            :color="getLevelColor(item.level)"
            size="small"
            variant="tonal"
          >
            {{ getLevelLabel(item.level) }}
          </v-chip>
        </template>

        <template #item.parent_name="{ item }">
          <span v-if="item.parent_name" class="text-body-2">
            {{ item.parent_name }}
          </span>
          <span v-else class="text-grey text-body-2">—</span>
        </template>

        <template #item.point_count="{ item }">
          <span class="font-weight-medium">{{ item.point_count || 0 }}</span>
        </template>

        <template #item.actions="{ item }">
          <v-btn
            icon="mdi-pencil"
            size="small"
            variant="text"
            :to="`/zones/${item.id}/edit`"
          />
          <v-btn
            icon="mdi-delete"
            size="small"
            variant="text"
            color="error"
            @click="confirmDelete(item)"
          />
        </template>

        <template #no-data>
          <div class="text-center py-8">
            <v-icon size="64" color="grey-lighten-1">mdi-map-marker-radius-outline</v-icon>
            <p class="text-h6 text-grey mt-4">Aucune zone définie</p>
            <p class="text-body-2 text-grey mb-4">
              Importez des zones IRIS ou créez vos propres zones manuellement.
            </p>
            <v-btn color="primary" @click="showImportDialog = true">
              Importer IRIS
            </v-btn>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Import IRIS Dialog -->
    <v-dialog v-model="showImportDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-download</v-icon>
          Importer des zones IRIS
        </v-card-title>

        <v-card-text>
          <p class="text-body-2 mb-4">
            Importez automatiquement les quartiers IRIS depuis
            <a href="https://geo.api.gouv.fr" target="_blank">geo.api.gouv.fr</a>.
            Les zones IRIS sont les quartiers statistiques définis par l'INSEE.
          </p>

          <v-text-field
            v-model="importCodeCommune"
            label="Code INSEE de la commune"
            placeholder="Ex: 59350 (Lille), 75056 (Paris)"
            variant="outlined"
            :rules="[v => !!v || 'Requis', v => /^\d{5}$/.test(v) || '5 chiffres requis']"
            hint="Code à 5 chiffres (trouvable sur insee.fr)"
            persistent-hint
          />

          <v-checkbox
            v-model="importReplace"
            label="Remplacer les zones existantes de cette commune"
            density="compact"
            hide-details
            class="mt-2"
          />

          <v-alert
            v-if="importError"
            type="error"
            variant="tonal"
            class="mt-4"
          >
            {{ importError }}
          </v-alert>

          <v-alert
            v-if="importSuccess"
            type="success"
            variant="tonal"
            class="mt-4"
          >
            {{ importSuccess }}
          </v-alert>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeImportDialog">Fermer</v-btn>
          <v-btn
            color="primary"
            :loading="importing"
            :disabled="!importCodeCommune || !/^\d{5}$/.test(importCodeCommune)"
            @click="importIRIS"
          >
            Importer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6">Supprimer la zone ?</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer la zone
          <strong>{{ zoneToDelete?.name }}</strong> ?
          <br><br>
          <span class="text-warning" v-if="zoneToDelete?.point_count > 0">
            Cette zone contient {{ zoneToDelete.point_count }} point(s).
            Ils ne seront pas supprimés mais ne seront plus associés à cette zone.
          </span>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Annuler</v-btn>
          <v-btn color="error" :loading="deleting" @click="deleteZone">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import HelpButton from '@/components/help/HelpButton.vue'

interface Zone {
  id: string
  name: string
  code: string | null
  zone_type: string
  metadata: Record<string, any>
  created_at: string
  updated_at?: string
  point_count: number
  // Champs hiérarchiques
  level: number
  parent_id: string | null
  parent_name: string | null
  is_global: boolean
  project_id: string | null
  population?: number
  code_iris?: string
  code_insee?: string
}

// Labels et icônes par niveau
const LEVEL_LABELS: Record<number, string> = {
  1: 'Commune',
  2: 'Quartier',
  3: 'Secteur',
}

const LEVEL_ICONS: Record<number, string> = {
  1: 'mdi-domain',
  2: 'mdi-home-city',
  3: 'mdi-map-marker',
}

const LEVEL_COLORS: Record<number, string> = {
  1: 'success',
  2: 'info',
  3: 'warning',
}

// State
const zones = ref<Zone[]>([])
const loading = ref(false)
const search = ref('')
const filterType = ref<string | null>(null)
const filterLevel = ref<number | null>(null)

// Import dialog
const showImportDialog = ref(false)
const importCodeCommune = ref('')
const importReplace = ref(false)
const importing = ref(false)
const importError = ref('')
const importSuccess = ref('')

// Delete dialog
const showDeleteDialog = ref(false)
const zoneToDelete = ref<Zone | null>(null)
const deleting = ref(false)

// Table headers
const headers = [
  { title: 'Nom', key: 'name', sortable: true },
  { title: 'Niveau', key: 'level', sortable: true },
  { title: 'Parent', key: 'parent_name', sortable: true },
  { title: 'Code', key: 'code', sortable: true },
  { title: 'Points', key: 'point_count', sortable: true, align: 'end' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' },
]

const zoneTypes = [
  { title: 'Quartier', value: 'quartier' },
  { title: 'Commune', value: 'commune' },
  { title: 'Secteur', value: 'secteur' },
  { title: 'IRIS', value: 'iris' },
]

const levelOptions = [
  { title: 'Communes', value: 1 },
  { title: 'Quartiers', value: 2 },
  { title: 'Secteurs', value: 3 },
]

// Computed
const filteredZones = computed(() => {
  let result = zones.value

  if (filterType.value) {
    result = result.filter(z => z.zone_type === filterType.value)
  }

  if (filterLevel.value !== null) {
    result = result.filter(z => z.level === filterLevel.value)
  }

  return result
})

const totalPoints = computed(() =>
  zones.value.reduce((sum, z) => sum + (z.point_count || 0), 0)
)

const communeCount = computed(() =>
  zones.value.filter(z => z.level === 1).length
)

const quartierCount = computed(() =>
  zones.value.filter(z => z.level === 2).length
)

const secteurCount = computed(() =>
  zones.value.filter(z => z.level === 3).length
)

// Methods
async function loadZones() {
  loading.value = true
  try {
    const response = await api.get('/zones')
    zones.value = response.data
  } catch (error) {
    console.error('Erreur chargement zones:', error)
  } finally {
    loading.value = false
  }
}

function getTypeColor(type: string): string {
  switch (type) {
    case 'quartier': return 'info'
    case 'commune': return 'success'
    case 'secteur': return 'warning'
    case 'iris': return 'info'
    default: return 'grey'
  }
}

function getLevelColor(level: number): string {
  return LEVEL_COLORS[level] || 'grey'
}

function getLevelLabel(level: number): string {
  return LEVEL_LABELS[level] || `Niveau ${level}`
}

function getLevelIcon(level: number): string {
  return LEVEL_ICONS[level] || 'mdi-map-marker'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function closeImportDialog() {
  showImportDialog.value = false
  importError.value = ''
  importSuccess.value = ''
}

async function importIRIS() {
  importing.value = true
  importError.value = ''
  importSuccess.value = ''

  try {
    const response = await api.post('/zones/import-iris', {
      code_commune: importCodeCommune.value,
      remplacer_existants: importReplace.value,
    })

    if (response.data.success) {
      importSuccess.value = response.data.message
      await loadZones()
      // Close dialog after success
      setTimeout(() => {
        closeImportDialog()
        importCodeCommune.value = ''
        importReplace.value = false
      }, 2000)
    } else {
      importError.value = response.data.message || 'Erreur lors de l\'import'
    }
  } catch (error: any) {
    importError.value = error.response?.data?.detail || 'Erreur lors de l\'import'
  } finally {
    importing.value = false
  }
}

function confirmDelete(zone: Zone) {
  zoneToDelete.value = zone
  showDeleteDialog.value = true
}

async function deleteZone() {
  if (!zoneToDelete.value) return

  deleting.value = true
  try {
    await api.delete(`/zones/${zoneToDelete.value.id}`)
    await loadZones()
    showDeleteDialog.value = false
  } catch (error: any) {
    console.error('Erreur suppression:', error)
  } finally {
    deleting.value = false
  }
}

onMounted(loadZones)
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}
</style>

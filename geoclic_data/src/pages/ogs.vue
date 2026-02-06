<template>
  <div>
    <!-- En-tête -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          OneGeo Suite
          <HelpButton page-key="ogs" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          Publiez vos données validées vers le SIG de la collectivité
        </p>
      </div>
      <v-btn
        color="primary"
        variant="outlined"
        prepend-icon="mdi-refresh"
        :loading="loading"
        @click="loadData"
      >
        Actualiser
      </v-btn>
    </div>

    <!-- Statistiques globales -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card color="primary" variant="tonal">
          <v-card-text class="text-center">
            <v-icon size="32" class="mb-2">mdi-database</v-icon>
            <div class="text-h4 font-weight-bold">{{ status.total_ogs_tables }}</div>
            <div class="text-body-2">Tables OGS créées</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card color="success" variant="tonal">
          <v-card-text class="text-center">
            <v-icon size="32" class="mb-2">mdi-check-circle</v-icon>
            <div class="text-h4 font-weight-bold">{{ status.total_points_published }}</div>
            <div class="text-body-2">Points publiés</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card color="warning" variant="tonal">
          <v-card-text class="text-center">
            <v-icon size="32" class="mb-2">mdi-clock-outline</v-icon>
            <div class="text-h4 font-weight-bold">{{ totalValidatedPoints }}</div>
            <div class="text-body-2">Points validés à publier</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card color="info" variant="tonal">
          <v-card-text class="text-center">
            <v-icon size="32" class="mb-2">mdi-account-clock</v-icon>
            <div class="text-h4 font-weight-bold">{{ status.pending_validation }}</div>
            <div class="text-body-2">En attente de validation</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Liste des catégories -->
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-folder-multiple</v-icon>
        Catégories à publier
        <v-spacer />
        <v-btn
          v-if="totalValidatedPoints > 0"
          color="success"
          prepend-icon="mdi-publish"
          @click="publishAll"
          :loading="publishingAll"
        >
          Tout publier vers OGS
        </v-btn>
      </v-card-title>

      <v-card-text v-if="loading">
        <div class="text-center pa-8">
          <v-progress-circular indeterminate color="primary" size="48" />
          <p class="mt-4 text-grey">Chargement des catégories...</p>
        </div>
      </v-card-text>

      <v-card-text v-else-if="status.tables.length === 0">
        <v-alert type="info" variant="tonal" class="ma-4">
          <v-alert-title>Aucune catégorie configurée</v-alert-title>
          Créez des catégories dans le <router-link to="/lexique">Lexique</router-link> pour commencer.
        </v-alert>
      </v-card-text>

      <v-list v-else lines="two">
        <template v-for="(table, index) in status.tables" :key="table.lexique_code">
          <v-list-item>
            <template v-slot:prepend>
              <v-avatar :color="table.point_count > 0 ? 'success' : 'grey-lighten-1'" class="mr-2">
                <v-icon :color="table.point_count > 0 ? 'white' : 'grey'">
                  {{ table.exists ? 'mdi-database-check' : 'mdi-database-plus' }}
                </v-icon>
              </v-avatar>
            </template>

            <v-list-item-title class="font-weight-medium">
              {{ table.lexique_label }}
            </v-list-item-title>

            <v-list-item-subtitle>
              <span class="mr-4">
                <v-icon size="14" class="mr-1">mdi-tag</v-icon>
                Code: {{ table.lexique_code }}
              </span>
              <span class="mr-4">
                <v-icon size="14" class="mr-1">mdi-table</v-icon>
                Table: <code>{{ table.table_name }}</code>
              </span>
              <v-chip
                v-if="table.exists"
                size="x-small"
                color="success"
                variant="tonal"
                class="mr-2"
              >
                Créée
              </v-chip>
              <v-chip
                v-else
                size="x-small"
                color="grey"
                variant="tonal"
                class="mr-2"
              >
                Non créée
              </v-chip>
            </v-list-item-subtitle>

            <template v-slot:append>
              <div class="d-flex align-center gap-3">
                <!-- Nombre de points validés -->
                <v-chip
                  :color="table.point_count > 0 ? 'warning' : 'grey'"
                  variant="flat"
                  size="small"
                >
                  <v-icon start size="14">mdi-map-marker</v-icon>
                  {{ table.point_count }} validé{{ table.point_count > 1 ? 's' : '' }}
                </v-chip>

                <!-- Bouton publier -->
                <v-btn
                  :color="table.point_count > 0 ? 'success' : 'grey'"
                  :disabled="table.point_count === 0"
                  :loading="publishing[table.lexique_code]"
                  variant="flat"
                  size="small"
                  prepend-icon="mdi-upload"
                  @click="publishCategory(table)"
                >
                  Publier
                </v-btn>

                <!-- Menu actions -->
                <v-menu v-if="table.exists">
                  <template v-slot:activator="{ props }">
                    <v-btn icon variant="text" size="small" v-bind="props">
                      <v-icon>mdi-dots-vertical</v-icon>
                    </v-btn>
                  </template>
                  <v-list density="compact">
                    <v-list-item
                      prepend-icon="mdi-delete"
                      title="Supprimer la table OGS"
                      @click="confirmDeleteTable(table)"
                    />
                  </v-list>
                </v-menu>
              </div>
            </template>
          </v-list-item>
          <v-divider v-if="index < status.tables.length - 1" />
        </template>
      </v-list>
    </v-card>

    <!-- Dialogue de confirmation publication -->
    <v-dialog v-model="publishDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon class="mr-2" color="success">mdi-upload</v-icon>
          Publier vers OneGeo Suite
        </v-card-title>
        <v-card-text>
          <p class="mb-4">
            Vous allez publier <strong>{{ selectedTable?.point_count }} point(s)</strong>
            de la catégorie <strong>« {{ selectedTable?.lexique_label }} »</strong>
            vers la table <code>{{ selectedTable?.table_name }}</code>.
          </p>

          <v-checkbox
            v-model="includeChildren"
            label="Inclure les sous-catégories"
            hint="Publie également les points des sous-catégories"
            persistent-hint
          />

          <v-alert type="info" variant="tonal" class="mt-4" density="compact">
            La table sera créée automatiquement si elle n'existe pas.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="publishDialog = false">Annuler</v-btn>
          <v-btn
            color="success"
            variant="flat"
            prepend-icon="mdi-check"
            :loading="selectedTable ? publishing[selectedTable.lexique_code] : false"
            @click="doPublish"
          >
            Confirmer la publication
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialogue de confirmation suppression -->
    <v-dialog v-model="deleteDialog" max-width="450">
      <v-card>
        <v-card-title class="text-h6 text-error">
          <v-icon class="mr-2" color="error">mdi-alert</v-icon>
          Supprimer la table OGS
        </v-card-title>
        <v-card-text>
          <p>
            Êtes-vous sûr de vouloir supprimer la table
            <code>{{ tableToDelete?.table_name }}</code> ?
          </p>
          <v-alert type="warning" variant="tonal" class="mt-4" density="compact">
            Cette action supprimera toutes les données publiées dans cette table.
            Les données dans GéoClic ne seront pas affectées.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Annuler</v-btn>
          <v-btn
            color="error"
            variant="flat"
            prepend-icon="mdi-delete"
            :loading="deleting"
            @click="doDeleteTable"
          >
            Supprimer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar résultat -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="5000">
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Fermer</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { ogsAPI } from '@/services/api'
import HelpButton from '@/components/help/HelpButton.vue'

// Types
interface OGSTableInfo {
  table_name: string
  lexique_code: string
  lexique_label: string
  point_count: number
  last_publication: string | null
  exists: boolean
}

interface OGSStatus {
  total_ogs_tables: number
  total_points_published: number
  tables: OGSTableInfo[]
  pending_validation: number
}

// State
const loading = ref(false)
const status = ref<OGSStatus>({
  total_ogs_tables: 0,
  total_points_published: 0,
  tables: [],
  pending_validation: 0,
})
const publishing = ref<Record<string, boolean>>({})
const publishingAll = ref(false)
const deleting = ref(false)

// Dialogs
const publishDialog = ref(false)
const deleteDialog = ref(false)
const selectedTable = ref<OGSTableInfo | null>(null)
const tableToDelete = ref<OGSTableInfo | null>(null)
const includeChildren = ref(true)

// Snackbar
const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
})

// Computed
const totalValidatedPoints = computed(() =>
  status.value.tables.reduce((sum, t) => sum + t.point_count, 0)
)

// Methods
async function loadData() {
  loading.value = true
  try {
    status.value = await ogsAPI.getStatus()
  } catch (e) {
    console.error('Erreur chargement statut OGS:', e)
    showMessage('Erreur lors du chargement des données', 'error')
  } finally {
    loading.value = false
  }
}

function publishCategory(table: OGSTableInfo) {
  selectedTable.value = table
  publishDialog.value = true
}

async function doPublish() {
  if (!selectedTable.value) return

  const code = selectedTable.value.lexique_code
  publishing.value[code] = true

  try {
    const result = await ogsAPI.publish(code, includeChildren.value)
    showMessage(result.message, 'success')
    publishDialog.value = false
    await loadData() // Recharger les données
  } catch (e: any) {
    console.error('Erreur publication:', e)
    showMessage(e.response?.data?.detail || 'Erreur lors de la publication', 'error')
  } finally {
    publishing.value[code] = false
  }
}

async function publishAll() {
  publishingAll.value = true
  let successCount = 0
  let errorCount = 0

  for (const table of status.value.tables) {
    if (table.point_count > 0) {
      try {
        await ogsAPI.publish(table.lexique_code, true)
        successCount++
      } catch (e) {
        console.error(`Erreur publication ${table.lexique_code}:`, e)
        errorCount++
      }
    }
  }

  publishingAll.value = false
  await loadData()

  if (errorCount === 0) {
    showMessage(`Publication réussie: ${successCount} catégorie(s)`, 'success')
  } else {
    showMessage(`Publication partielle: ${successCount} OK, ${errorCount} erreur(s)`, 'warning')
  }
}

function confirmDeleteTable(table: OGSTableInfo) {
  tableToDelete.value = table
  deleteDialog.value = true
}

async function doDeleteTable() {
  if (!tableToDelete.value) return

  deleting.value = true
  try {
    await ogsAPI.deleteTable(tableToDelete.value.table_name)
    showMessage(`Table ${tableToDelete.value.table_name} supprimée`, 'success')
    deleteDialog.value = false
    await loadData()
  } catch (e: any) {
    console.error('Erreur suppression:', e)
    showMessage(e.response?.data?.detail || 'Erreur lors de la suppression', 'error')
  } finally {
    deleting.value = false
  }
}

function showMessage(message: string, color: string) {
  snackbar.value = { show: true, message, color }
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>

<style scoped>
code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85em;
}

.gap-3 {
  gap: 12px;
}
</style>

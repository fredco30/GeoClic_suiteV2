<template>
  <div>
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          Imports
          <HelpButton page-key="imports" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          Importez des données depuis des fichiers ou PostGIS
        </p>
      </div>
      <v-spacer />
      <v-btn-group variant="outlined" density="compact" v-if="importMode === 'file'">
        <v-btn prepend-icon="mdi-download" @click="downloadTemplate('csv')">
          Modele CSV
        </v-btn>
        <v-btn prepend-icon="mdi-download" @click="downloadTemplate('geojson')">
          Modele GeoJSON
        </v-btn>
      </v-btn-group>
    </div>

    <!-- Sélection du mode d'import -->
    <v-tabs v-model="importMode" class="mb-4" color="primary">
      <v-tab value="file" prepend-icon="mdi-file-upload">
        Fichier
      </v-tab>
      <v-tab value="postgis" prepend-icon="mdi-database" :disabled="!postgisConfigured">
        PostGIS
        <v-chip v-if="!postgisConfigured" size="x-small" color="grey" class="ml-2">
          Non configure
        </v-chip>
      </v-tab>
    </v-tabs>

    <!-- ================================================================== -->
    <!-- MODE FICHIER -->
    <!-- ================================================================== -->
    <v-window v-model="importMode">
      <v-window-item value="file">
        <v-stepper v-model="step" :items="['Fichier', 'Mapping', 'Import']">
          <template v-slot:item.1>
            <v-card flat>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-file-input
                      v-model="file"
                      label="Selectionner un fichier"
                      accept=".csv,.geojson,.json,.zip"
                      prepend-icon="mdi-file-upload"
                      show-size
                      :hint="file ? '' : 'Formats: CSV, GeoJSON, Shapefile (ZIP)'"
                      persistent-hint
                      @update:model-value="onFileChange"
                    />

                    <v-select
                      v-model="targetProjet"
                      label="Projet cible *"
                      :items="projets"
                      item-title="nom"
                      item-value="id"
                      :rules="[v => !!v || 'Projet requis']"
                      class="mt-4"
                    />

                    <v-select
                      v-model="targetCategorie"
                      label="Categorie cible *"
                      :items="categories"
                      item-title="libelle"
                      item-value="code"
                      :rules="[v => !!v || 'Categorie requise']"
                      class="mt-4"
                    />
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-card variant="tonal" color="info">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2">mdi-information</v-icon>
                        Formats supportes
                      </v-card-title>
                      <v-card-text>
                        <v-list density="compact" bg-color="transparent">
                          <v-list-item prepend-icon="mdi-file-delimited">
                            <v-list-item-title>CSV</v-list-item-title>
                            <v-list-item-subtitle>
                              Avec colonnes latitude/longitude
                            </v-list-item-subtitle>
                          </v-list-item>
                          <v-list-item prepend-icon="mdi-code-json">
                            <v-list-item-title>GeoJSON</v-list-item-title>
                            <v-list-item-subtitle>
                              FeatureCollection avec Points
                            </v-list-item-subtitle>
                          </v-list-item>
                          <v-list-item prepend-icon="mdi-folder-zip">
                            <v-list-item-title>Shapefile (ZIP)</v-list-item-title>
                            <v-list-item-subtitle>
                              Archive contenant .shp, .dbf, .shx
                            </v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>

              <v-card-actions>
                <v-spacer />
                <v-btn
                  color="primary"
                  :disabled="!file || !targetProjet || !targetCategorie"
                  :loading="analyzing"
                  @click="analyzeFile"
                >
                  Analyser le fichier
                  <v-icon end>mdi-arrow-right</v-icon>
                </v-btn>
              </v-card-actions>
            </v-card>
          </template>

          <!-- Etape 2: Mapping des colonnes -->
          <template v-slot:item.2>
            <v-card flat>
              <v-card-text>
                <v-alert type="info" variant="tonal" class="mb-4">
                  <strong>{{ preview?.total_rows }} lignes</strong> detectees dans le fichier
                  <strong>{{ preview?.format?.toUpperCase() }}</strong>.
                  Associez les colonnes source aux champs GeoClic.
                </v-alert>

                <v-row>
                  <v-col cols="12" md="8">
                    <v-card variant="outlined">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2">mdi-swap-horizontal</v-icon>
                        Mapping des colonnes
                      </v-card-title>
                      <v-card-text>
                        <v-table density="compact">
                          <thead>
                            <tr>
                              <th>Colonne source</th>
                              <th>-></th>
                              <th>Champ GeoClic</th>
                              <th>Apercu</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="col in preview?.columns" :key="col">
                              <td class="font-weight-medium">{{ col }}</td>
                              <td class="text-center">-></td>
                              <td style="width: 200px">
                                <v-select
                                  v-model="mapping[col]"
                                  :items="targetFields"
                                  item-title="label"
                                  item-value="value"
                                  density="compact"
                                  variant="outlined"
                                  hide-details
                                  clearable
                                  placeholder="Ignorer"
                                />
                              </td>
                              <td class="text-caption text-grey">
                                {{ getSampleValue(col) }}
                              </td>
                            </tr>
                          </tbody>
                        </v-table>
                      </v-card-text>
                    </v-card>

                    <!-- Validation du mapping -->
                    <v-alert
                      v-if="!mappingValid"
                      type="warning"
                      variant="tonal"
                      class="mt-4"
                    >
                      <v-icon class="mr-2">mdi-alert</v-icon>
                      Vous devez mapper soit <strong>latitude</strong> et <strong>longitude</strong>, soit une colonne <strong>Geometrie (WKT)</strong>.
                    </v-alert>
                  </v-col>

                  <v-col cols="12" md="4">
                    <!-- Options d'import -->
                    <v-card variant="outlined">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2">mdi-cog</v-icon>
                        Options
                      </v-card-title>
                      <v-card-text>
                        <v-checkbox
                          v-model="options.skipDuplicates"
                          label="Ignorer les doublons"
                          hint="Points dans un rayon de 5m"
                          persistent-hint
                          hide-details="auto"
                          density="compact"
                        />
                        <v-checkbox
                          v-model="options.updateExisting"
                          label="Mettre a jour les existants"
                          hint="Au lieu de les ignorer"
                          persistent-hint
                          hide-details="auto"
                          density="compact"
                          class="mt-2"
                        />
                      </v-card-text>
                    </v-card>

                    <!-- Apercu donnees -->
                    <v-card variant="outlined" class="mt-4">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2">mdi-eye</v-icon>
                        Apercu (5 premieres lignes)
                      </v-card-title>
                      <v-card-text class="pa-0">
                        <v-table density="compact" class="text-caption">
                          <thead>
                            <tr>
                              <th v-for="col in previewColumns" :key="col" class="text-truncate" style="max-width: 100px">
                                {{ col }}
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(row, i) in preview?.sample_data?.slice(0, 5)" :key="i">
                              <td v-for="col in previewColumns" :key="col" class="text-truncate" style="max-width: 100px">
                                {{ row[col] }}
                              </td>
                            </tr>
                          </tbody>
                        </v-table>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>

              <v-card-actions>
                <v-btn variant="text" @click="step = 1">
                  <v-icon start>mdi-arrow-left</v-icon>
                  Retour
                </v-btn>
                <v-spacer />
                <v-btn
                  color="primary"
                  :disabled="!mappingValid"
                  @click="step = 3; executeImport()"
                >
                  Lancer l'import
                  <v-icon end>mdi-upload</v-icon>
                </v-btn>
              </v-card-actions>
            </v-card>
          </template>

          <!-- Etape 3: Resultat -->
          <template v-slot:item.3>
            <ImportResultCard
              :importing="importing"
              :import-result="importResult"
              :import-error="importError"
              @reset="resetImport"
            />
          </template>
        </v-stepper>
      </v-window-item>

      <!-- ================================================================== -->
      <!-- MODE POSTGIS -->
      <!-- ================================================================== -->
      <v-window-item value="postgis">
        <v-stepper v-model="pgStep" :items="['Table', 'Mapping', 'Import']">
          <!-- Etape 1: Selection de la table -->
          <template v-slot:item.1>
            <v-card flat>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-alert type="success" variant="tonal" class="mb-4" v-if="postgisStatus">
                      <v-icon class="mr-2">mdi-database-check</v-icon>
                      Connecte a <strong>{{ postgisStatus.host }}</strong> /
                      <strong>{{ postgisStatus.database }}</strong>
                    </v-alert>

                    <v-select
                      v-model="pgSelectedTable"
                      label="Table PostGIS *"
                      :items="pgTables"
                      item-title="table_name"
                      item-value="table_name"
                      :loading="pgLoadingTables"
                      @update:model-value="onTableSelect"
                    >
                      <template v-slot:item="{ item, props }">
                        <v-list-item v-bind="props">
                          <template v-slot:append>
                            <v-chip size="x-small" color="info">
                              {{ item.raw.row_count }} lignes
                            </v-chip>
                          </template>
                        </v-list-item>
                      </template>
                    </v-select>

                    <v-select
                      v-model="targetProjet"
                      label="Projet cible *"
                      :items="projets"
                      item-title="nom"
                      item-value="id"
                      :rules="[v => !!v || 'Projet requis']"
                      class="mt-4"
                    />

                    <v-select
                      v-model="targetCategorie"
                      label="Categorie cible *"
                      :items="categories"
                      item-title="libelle"
                      item-value="code"
                      :rules="[v => !!v || 'Categorie requise']"
                      class="mt-4"
                    />

                    <!-- Filtres structurés (sécurisés) -->
                    <div class="mt-4" v-if="pgSelectedTable && pgPreview?.columns?.length">
                      <div class="text-subtitle-2 mb-2">Filtres (optionnel)</div>
                      <div v-for="(filter, idx) in pgFilters" :key="idx" class="d-flex align-center ga-2 mb-2">
                        <v-select
                          v-model="filter.column"
                          :items="pgPreview.columns"
                          label="Colonne"
                          density="compact"
                          variant="outlined"
                          hide-details
                          style="max-width: 200px"
                        />
                        <v-select
                          v-model="filter.operator"
                          :items="filterOperators"
                          label="Op."
                          density="compact"
                          variant="outlined"
                          hide-details
                          style="max-width: 140px"
                        />
                        <v-text-field
                          v-if="!['IS NULL', 'IS NOT NULL'].includes(filter.operator)"
                          v-model="filter.value"
                          label="Valeur"
                          density="compact"
                          variant="outlined"
                          hide-details
                          style="max-width: 200px"
                        />
                        <v-btn icon="mdi-close" size="small" variant="text" color="error" @click="pgFilters.splice(idx, 1)" />
                      </div>
                      <v-btn size="small" variant="tonal" prepend-icon="mdi-plus" @click="pgFilters.push({ column: '', operator: '=', value: '' })">
                        Ajouter un filtre
                      </v-btn>
                    </div>

                    <v-text-field
                      v-model.number="pgLimit"
                      label="Limite (optionnel)"
                      type="number"
                      hint="Nombre max de lignes a importer"
                      persistent-hint
                      class="mt-4"
                    />
                  </v-col>

                  <v-col cols="12" md="6">
                    <!-- Info table selectionnee -->
                    <v-card variant="outlined" v-if="pgSelectedTableInfo">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2">mdi-table</v-icon>
                        {{ pgSelectedTable }}
                      </v-card-title>
                      <v-card-text>
                        <v-list density="compact">
                          <v-list-item>
                            <v-list-item-title>Geometrie</v-list-item-title>
                            <v-list-item-subtitle>
                              {{ pgSelectedTableInfo.geometry_type }} (SRID: {{ pgSelectedTableInfo.srid }})
                            </v-list-item-subtitle>
                          </v-list-item>
                          <v-list-item>
                            <v-list-item-title>Nombre de lignes</v-list-item-title>
                            <v-list-item-subtitle>
                              {{ pgSelectedTableInfo.row_count }}
                            </v-list-item-subtitle>
                          </v-list-item>
                        </v-list>

                        <!-- Apercu des donnees -->
                        <div class="mt-4" v-if="pgPreview">
                          <div class="text-subtitle-2 mb-2">Apercu (10 lignes)</div>
                          <v-table density="compact" class="text-caption">
                            <thead>
                              <tr>
                                <th v-for="col in pgPreview.columns?.slice(0, 5)" :key="col" class="text-truncate" style="max-width: 80px">
                                  {{ col }}
                                </th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr v-for="(row, i) in pgPreview.data?.slice(0, 5)" :key="i">
                                <td v-for="col in pgPreview.columns?.slice(0, 5)" :key="col" class="text-truncate" style="max-width: 80px">
                                  {{ row[col] }}
                                </td>
                              </tr>
                            </tbody>
                          </v-table>
                        </div>
                      </v-card-text>
                    </v-card>

                    <!-- Placeholder si pas de table selectionnee -->
                    <v-card variant="tonal" color="grey-lighten-4" v-else>
                      <v-card-text class="text-center py-8">
                        <v-icon size="48" color="grey">mdi-table-search</v-icon>
                        <p class="text-grey mt-2">Selectionnez une table pour voir l'apercu</p>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>

              <v-card-actions>
                <v-spacer />
                <v-btn
                  color="primary"
                  :disabled="!pgSelectedTable || !targetProjet || !targetCategorie"
                  :loading="pgAnalyzing"
                  @click="analyzePostGISTable"
                >
                  Configurer le mapping
                  <v-icon end>mdi-arrow-right</v-icon>
                </v-btn>
              </v-card-actions>
            </v-card>
          </template>

          <!-- Etape 2: Mapping PostGIS -->
          <template v-slot:item.2>
            <v-card flat>
              <v-card-text>
                <v-alert type="info" variant="tonal" class="mb-4">
                  <strong>{{ pgSelectedTableInfo?.row_count }} lignes</strong> dans la table
                  <strong>{{ pgSelectedTable }}</strong>.
                  Associez les colonnes source aux champs GeoClic.
                </v-alert>

                <v-row>
                  <v-col cols="12" md="8">
                    <v-card variant="outlined">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2">mdi-swap-horizontal</v-icon>
                        Mapping des colonnes
                      </v-card-title>
                      <v-card-text>
                        <v-table density="compact">
                          <thead>
                            <tr>
                              <th>Colonne source</th>
                              <th>-></th>
                              <th>Champ GeoClic</th>
                              <th>Type</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="col in pgColumns" :key="col.column_name">
                              <td class="font-weight-medium">
                                {{ col.column_name }}
                                <v-chip v-if="col.is_geometry" size="x-small" color="success" class="ml-1">
                                  geom
                                </v-chip>
                              </td>
                              <td class="text-center">-></td>
                              <td style="width: 200px">
                                <v-select
                                  v-model="pgMapping[col.column_name]"
                                  :items="pgTargetFields"
                                  item-title="label"
                                  item-value="value"
                                  density="compact"
                                  variant="outlined"
                                  hide-details
                                  clearable
                                  placeholder="Ignorer"
                                />
                              </td>
                              <td class="text-caption text-grey">
                                {{ col.data_type }}
                              </td>
                            </tr>
                          </tbody>
                        </v-table>
                      </v-card-text>
                    </v-card>

                    <!-- Validation du mapping -->
                    <v-alert
                      v-if="!pgMappingValid"
                      type="warning"
                      variant="tonal"
                      class="mt-4"
                    >
                      <v-icon class="mr-2">mdi-alert</v-icon>
                      Vous devez mapper soit une <strong>colonne geometrie</strong>,
                      soit <strong>latitude</strong> et <strong>longitude</strong>.
                    </v-alert>
                  </v-col>

                  <v-col cols="12" md="4">
                    <!-- Resume -->
                    <v-card variant="outlined">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2">mdi-information</v-icon>
                        Resume
                      </v-card-title>
                      <v-card-text>
                        <v-list density="compact">
                          <v-list-item>
                            <v-list-item-title>Table</v-list-item-title>
                            <v-list-item-subtitle>{{ pgSelectedTable }}</v-list-item-subtitle>
                          </v-list-item>
                          <v-list-item>
                            <v-list-item-title>Projet</v-list-item-title>
                            <v-list-item-subtitle>{{ projets.find(p => p.id === targetProjet)?.nom }}</v-list-item-subtitle>
                          </v-list-item>
                          <v-list-item>
                            <v-list-item-title>Categorie</v-list-item-title>
                            <v-list-item-subtitle>{{ categories.find(c => c.code === targetCategorie)?.libelle }}</v-list-item-subtitle>
                          </v-list-item>
                          <v-list-item v-if="pgFilters.length > 0">
                            <v-list-item-title>Filtres</v-list-item-title>
                            <v-list-item-subtitle>{{ pgFilters.length }} filtre(s) actif(s)</v-list-item-subtitle>
                          </v-list-item>
                          <v-list-item v-if="pgLimit">
                            <v-list-item-title>Limite</v-list-item-title>
                            <v-list-item-subtitle>{{ pgLimit }} lignes</v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>

              <v-card-actions>
                <v-btn variant="text" @click="pgStep = 1">
                  <v-icon start>mdi-arrow-left</v-icon>
                  Retour
                </v-btn>
                <v-spacer />
                <v-btn
                  color="primary"
                  :disabled="!pgMappingValid"
                  @click="pgStep = 3; executePostGISImport()"
                >
                  Lancer l'import
                  <v-icon end>mdi-upload</v-icon>
                </v-btn>
              </v-card-actions>
            </v-card>
          </template>

          <!-- Etape 3: Resultat PostGIS -->
          <template v-slot:item.3>
            <ImportResultCard
              :importing="pgImporting"
              :import-result="pgImportResult"
              :import-error="pgImportError"
              @reset="resetPostGISImport"
            />
          </template>
        </v-stepper>
      </v-window-item>
    </v-window>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { projetsAPI, importsAPI, postgisAPI } from '@/services/api'
import { useLexiqueStore } from '@/stores/lexique'
import HelpButton from '@/components/help/HelpButton.vue'

const lexiqueStore = useLexiqueStore()

// ============================================================
// STATE COMMUN
// ============================================================
const importMode = ref<'file' | 'postgis'>('file')
const projets = ref<any[]>([])
const categories = ref<any[]>([])
const targetProjet = ref<string | null>(null)
const targetCategorie = ref<string | null>(null)

// ============================================================
// STATE IMPORT FICHIER
// ============================================================
const step = ref(1)
const file = ref<File | null>(null)
const analyzing = ref(false)
const importing = ref(false)
const importError = ref('')
const preview = ref<any>(null)
const mapping = ref<Record<string, string>>({})
const importResult = ref<any>(null)
const options = ref({
  skipDuplicates: true,
  updateExisting: false,
})

// ============================================================
// STATE POSTGIS
// ============================================================
const postgisConfigured = ref(false)
const postgisStatus = ref<any>(null)
const pgStep = ref(1)
const pgTables = ref<any[]>([])
const pgLoadingTables = ref(false)
const pgSelectedTable = ref<string | null>(null)
const pgSelectedTableInfo = ref<any>(null)
const pgColumns = ref<any[]>([])
const pgPreview = ref<any>(null)
const pgMapping = ref<Record<string, string>>({})
const pgAnalyzing = ref(false)
const pgImporting = ref(false)
const pgImportResult = ref<any>(null)
const pgImportError = ref('')
const pgFilters = ref<Array<{ column: string; operator: string; value: string }>>([])
const pgLimit = ref<number | null>(null)
const filterOperators = ['=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IS NULL', 'IS NOT NULL']

// ============================================================
// COMPUTED - FICHIER
// ============================================================
const targetFields = computed(() => {
  const baseFields = [
    // Champs principaux
    { label: 'ID (conserve original)', value: 'id' },
    { label: 'Nom du point', value: 'nom' },
    { label: 'Latitude', value: 'latitude' },
    { label: 'Longitude', value: 'longitude' },
    { label: 'Geometrie (WKT)', value: 'wkt' },
    // Classification
    { label: 'Type', value: 'type' },
    { label: 'Sous-type', value: 'subtype' },
    { label: 'Code Lexique', value: 'lexique_code' },
    // Etat et statut
    { label: 'Etat / Condition', value: 'condition_state' },
    { label: 'Statut du point', value: 'point_status' },
    // Proprietes physiques
    { label: 'Materiau', value: 'materiau' },
    { label: 'Hauteur', value: 'hauteur' },
    { label: 'Largeur', value: 'largeur' },
    // Dates et priorite
    { label: 'Date installation', value: 'date_installation' },
    { label: 'Priorite', value: 'priorite' },
    { label: 'Cout remplacement', value: 'cout_remplacement' },
    // Localisation
    { label: 'Zone / Secteur', value: 'zone_name' },
    { label: 'Altitude', value: 'altitude' },
    { label: 'Precision GPS', value: 'gps_precision' },
    { label: 'Source GPS', value: 'gps_source' },
    // Autres
    { label: 'Commentaire', value: 'comment' },
    { label: 'Chemin photo', value: 'photo_path' },
    { label: 'Couleur (hex)', value: 'color_value' },
    { label: 'Icone', value: 'icon_name' },
  ]

  if (targetCategorie.value) {
    const champs = lexiqueStore.getChampsForLexique(targetCategorie.value)
    for (const champ of champs) {
      baseFields.push({
        label: `[Champ] ${champ.nom}`,
        value: `custom_${champ.nom}`,
      })
    }
  }

  return baseFields
})

const previewColumns = computed(() => {
  return preview.value?.columns?.slice(0, 5) || []
})

const mappingValid = computed(() => {
  const values = Object.values(mapping.value)
  const hasLatLng = values.includes('latitude') && values.includes('longitude')
  const hasWkt = values.includes('wkt')
  return hasLatLng || hasWkt
})

// ============================================================
// COMPUTED - POSTGIS
// ============================================================
const pgTargetFields = computed(() => {
  const baseFields = [
    // Champs principaux
    { label: 'ID (conserve original)', value: 'id' },
    { label: 'Nom du point', value: 'nom' },
    { label: 'Geometrie (auto lat/lng)', value: 'geometry' },
    { label: 'Latitude', value: 'latitude' },
    { label: 'Longitude', value: 'longitude' },
    // Classification
    { label: 'Type', value: 'type' },
    { label: 'Sous-type', value: 'subtype' },
    { label: 'Code Lexique', value: 'lexique_code' },
    // Etat et statut
    { label: 'Etat / Condition', value: 'condition_state' },
    { label: 'Statut du point', value: 'point_status' },
    // Proprietes physiques
    { label: 'Materiau', value: 'materiau' },
    { label: 'Hauteur', value: 'hauteur' },
    { label: 'Largeur', value: 'largeur' },
    // Dates et priorite
    { label: 'Date installation', value: 'date_installation' },
    { label: 'Priorite', value: 'priorite' },
    { label: 'Cout remplacement', value: 'cout_remplacement' },
    // Localisation
    { label: 'Zone / Secteur', value: 'zone_name' },
    { label: 'Altitude', value: 'altitude' },
    { label: 'Precision GPS', value: 'gps_precision' },
    { label: 'Source GPS', value: 'gps_source' },
    // Autres
    { label: 'Commentaire', value: 'comment' },
    { label: 'Couleur (hex)', value: 'color_value' },
    { label: 'Icone', value: 'icon_name' },
  ]

  if (targetCategorie.value) {
    const champs = lexiqueStore.getChampsForLexique(targetCategorie.value)
    for (const champ of champs) {
      baseFields.push({
        label: `[Champ] ${champ.nom}`,
        value: `custom_${champ.nom}`,
      })
    }
  }

  return baseFields
})

const pgMappingValid = computed(() => {
  const values = Object.values(pgMapping.value)
  const hasGeometry = values.includes('geometry')
  const hasLatLng = values.includes('latitude') && values.includes('longitude')
  return hasGeometry || hasLatLng
})

// ============================================================
// METHODS - FICHIER
// ============================================================
function onFileChange() {
  preview.value = null
  mapping.value = {}
}

async function analyzeFile() {
  if (!file.value) return

  analyzing.value = true
  try {
    preview.value = await importsAPI.preview(file.value)
    mapping.value = { ...preview.value.suggested_mapping }

    if (targetCategorie.value) {
      await lexiqueStore.fetchChamps(targetCategorie.value)
    }

    step.value = 2
  } catch (e: any) {
    console.error('Erreur analyse:', e)
    alert(e.response?.data?.detail || "Erreur lors de l'analyse du fichier")
  } finally {
    analyzing.value = false
  }
}

function getSampleValue(column: string): string {
  if (!preview.value?.sample_data?.length) return ''
  const value = preview.value.sample_data[0][column]
  if (value === null || value === undefined) return '-'
  const str = String(value)
  return str.length > 30 ? str.substring(0, 30) + '...' : str
}

async function executeImport() {
  if (!file.value || !targetProjet.value || !targetCategorie.value) return

  importing.value = true
  importError.value = ''

  try {
    importResult.value = await importsAPI.execute(
      file.value,
      targetProjet.value,
      targetCategorie.value,
      mapping.value,
      options.value
    )
  } catch (e: any) {
    console.error('Erreur import:', e)
    importError.value = e.response?.data?.detail || "Erreur lors de l'import"
    importResult.value = { success: false }
  } finally {
    importing.value = false
  }
}

function resetImport() {
  step.value = 1
  file.value = null
  preview.value = null
  mapping.value = {}
  importResult.value = null
  importError.value = ''
}

async function downloadTemplate(format: 'csv' | 'geojson') {
  try {
    const blob = await importsAPI.downloadTemplate(format)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `modele_import.${format}`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Erreur telechargement modele:', e)
  }
}

// ============================================================
// METHODS - POSTGIS
// ============================================================
async function loadPostGISStatus() {
  try {
    postgisStatus.value = await postgisAPI.getStatus()
    postgisConfigured.value = postgisStatus.value?.configured || false

    if (postgisConfigured.value) {
      await loadPostGISTables()
    }
  } catch (e) {
    console.error('Erreur chargement statut PostGIS:', e)
    postgisConfigured.value = false
  }
}

async function loadPostGISTables() {
  pgLoadingTables.value = true
  try {
    pgTables.value = await postgisAPI.getTables()
  } catch (e) {
    console.error('Erreur chargement tables:', e)
  } finally {
    pgLoadingTables.value = false
  }
}

async function onTableSelect(tableName: string | null) {
  if (!tableName) {
    pgSelectedTableInfo.value = null
    pgPreview.value = null
    return
  }

  // Trouver les infos de la table
  pgSelectedTableInfo.value = pgTables.value.find(t => t.table_name === tableName)

  // Charger l'apercu
  try {
    pgPreview.value = await postgisAPI.previewTable(tableName)
  } catch (e) {
    console.error('Erreur apercu table:', e)
  }
}

async function analyzePostGISTable() {
  if (!pgSelectedTable.value) return

  pgAnalyzing.value = true
  try {
    // Charger les colonnes
    pgColumns.value = await postgisAPI.getTableColumns(pgSelectedTable.value)

    // Obtenir le mapping suggere
    const suggestion = await postgisAPI.suggestMapping(pgSelectedTable.value)
    pgMapping.value = { ...suggestion.suggested_mapping }

    // Charger les champs dynamiques de la categorie
    if (targetCategorie.value) {
      await lexiqueStore.fetchChamps(targetCategorie.value)
    }

    pgStep.value = 2
  } catch (e: any) {
    console.error('Erreur analyse table:', e)
    alert(e.response?.data?.detail || "Erreur lors de l'analyse de la table")
  } finally {
    pgAnalyzing.value = false
  }
}

async function executePostGISImport() {
  if (!pgSelectedTable.value || !targetProjet.value || !targetCategorie.value) return

  pgImporting.value = true
  pgImportError.value = ''

  try {
    const activeFilters = pgFilters.value.filter(f => f.column && f.operator)
    pgImportResult.value = await postgisAPI.importData({
      table_name: pgSelectedTable.value,
      schema_name: postgisStatus.value?.schema_name || 'public',
      project_id: targetProjet.value,
      lexique_code: targetCategorie.value,
      mapping: pgMapping.value,
      filters: activeFilters.length > 0 ? activeFilters : undefined,
      limit: pgLimit.value || undefined,
    })
  } catch (e: any) {
    console.error('Erreur import PostGIS:', e)
    pgImportError.value = e.response?.data?.detail || "Erreur lors de l'import"
    pgImportResult.value = { success: false }
  } finally {
    pgImporting.value = false
  }
}

function resetPostGISImport() {
  pgStep.value = 1
  pgSelectedTable.value = null
  pgSelectedTableInfo.value = null
  pgColumns.value = []
  pgPreview.value = null
  pgMapping.value = {}
  pgImportResult.value = null
  pgImportError.value = ''
  pgFilters.value = []
  pgLimit.value = null
}

// ============================================================
// LIFECYCLE
// ============================================================
onMounted(async () => {
  try {
    projets.value = await projetsAPI.getAll()
  } catch (e) {
    console.error('Erreur chargement projets:', e)
  }
  await lexiqueStore.fetchAll()
  categories.value = lexiqueStore.entries.filter(e => e.niveau === 0 || e.niveau === 1)

  // Charger le statut PostGIS
  await loadPostGISStatus()
})

// ============================================================
// COMPOSANT RESULTAT (inline)
// ============================================================
const ImportResultCard = defineComponent({
  props: {
    importing: Boolean,
    importResult: Object as () => any,
    importError: String,
  },
  emits: ['reset'],
  setup(props, { emit }) {
    return () => h('v-card', { flat: true }, [
      h('v-card-text', { class: 'text-center py-8' }, [
        // En cours
        props.importing ? h('div', [
          h('v-progress-circular', { indeterminate: true, color: 'primary', size: 64, class: 'mb-4' }),
          h('p', { class: 'text-h6' }, 'Import en cours...'),
          h('p', { class: 'text-grey' }, 'Veuillez patienter'),
        ]) :
        // Succes
        props.importResult?.success ? h('div', [
          h('v-icon', { size: 64, color: 'success', class: 'mb-4' }, 'mdi-check-circle'),
          h('p', { class: 'text-h6 text-success' }, 'Import termine avec succes !'),
          h('v-row', { justify: 'center', class: 'mt-6' }, [
            h('v-col', { cols: 'auto' }, [
              h('v-card', { variant: 'tonal', color: 'success', class: 'pa-4 text-center' }, [
                h('div', { class: 'text-h4' }, props.importResult.imported),
                h('div', { class: 'text-caption' }, 'Points importes'),
              ]),
            ]),
            props.importResult.skipped > 0 ? h('v-col', { cols: 'auto' }, [
              h('v-card', { variant: 'tonal', color: 'warning', class: 'pa-4 text-center' }, [
                h('div', { class: 'text-h4' }, props.importResult.skipped),
                h('div', { class: 'text-caption' }, 'Doublons ignores'),
              ]),
            ]) : null,
            props.importResult.errors > 0 ? h('v-col', { cols: 'auto' }, [
              h('v-card', { variant: 'tonal', color: 'error', class: 'pa-4 text-center' }, [
                h('div', { class: 'text-h4' }, props.importResult.errors),
                h('div', { class: 'text-caption' }, 'Erreurs'),
              ]),
            ]) : null,
          ]),
        ]) :
        // Erreur
        props.importResult ? h('div', [
          h('v-icon', { size: 64, color: 'error', class: 'mb-4' }, 'mdi-alert-circle'),
          h('p', { class: 'text-h6 text-error' }, "Erreur lors de l'import"),
          h('p', { class: 'text-grey' }, props.importError),
        ]) : null,
      ]),
      h('v-card-actions', [
        h('v-spacer'),
        h('v-btn', { variant: 'text', onClick: () => emit('reset') }, 'Nouvel import'),
        props.importResult?.success ? h('v-btn', { color: 'primary', to: '/points' }, [
          'Voir les points',
          h('v-icon', { end: true }, 'mdi-arrow-right'),
        ]) : null,
      ]),
    ])
  },
})
</script>

<style scoped>
.v-table {
  font-size: 0.85rem;
}
</style>

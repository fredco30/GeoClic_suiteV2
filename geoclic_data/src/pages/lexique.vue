<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          Lexique - Vue globale
          <HelpButton page-key="lexique" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          Vue d'ensemble de toutes les catégories. Pour modifier, ouvrez le projet concerné.
        </p>
      </div>
      <v-spacer />
      <v-chip color="info" variant="flat" prepend-icon="mdi-eye">
        Lecture seule
      </v-chip>
    </div>

    <!-- Info banner -->
    <v-alert type="info" variant="tonal" class="mb-4">
      <div class="d-flex align-center">
        <v-icon class="mr-2">mdi-information</v-icon>
        <div>
          <strong>Cette page est en lecture seule.</strong>
          Pour ajouter ou modifier des catégories et des champs, ouvrez le projet correspondant depuis la page
          <router-link to="/projets" class="text-primary">Projets</router-link>.
        </div>
      </div>
    </v-alert>

    <v-row>
      <!-- Arborescence -->
      <v-col cols="12" md="5">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-folder-tree</v-icon>
            Arborescence complète
            <v-spacer />
            <v-btn icon size="small" variant="text" @click="expandAll">
              <v-icon>mdi-unfold-more-horizontal</v-icon>
              <v-tooltip activator="parent" location="top">Tout déplier</v-tooltip>
            </v-btn>
            <v-btn icon size="small" variant="text" @click="collapseAll">
              <v-icon>mdi-unfold-less-horizontal</v-icon>
              <v-tooltip activator="parent" location="top">Tout replier</v-tooltip>
            </v-btn>
          </v-card-title>
          <v-card-text class="pa-0">
            <v-treeview
              v-model:opened="openedNodes"
              v-model:activated="activatedNodes"
              :items="treeItems"
              item-title="libelle"
              item-value="id"
              activatable
              open-on-click
              density="compact"
              @update:activated="onNodeActivated"
            >
              <template v-slot:prepend="{ item }">
                <v-icon :color="toHexColor(item.couleur)">
                  {{ item.icone || 'mdi-folder' }}
                </v-icon>
              </template>
              <template v-slot:append="{ item }">
                <v-chip size="x-small" class="ml-2" v-if="item.children?.length">
                  {{ item.children.length }}
                </v-chip>
                <v-chip
                  size="x-small"
                  color="grey"
                  class="ml-2"
                  v-if="!item.actif"
                >
                  Inactif
                </v-chip>
              </template>
            </v-treeview>

            <div v-if="!treeItems.length" class="text-center pa-8 text-grey">
              <v-icon size="48" class="mb-2">mdi-folder-plus</v-icon>
              <p>Aucune catégorie</p>
              <p class="text-caption">Créez des catégories depuis un projet</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Détail de la catégorie sélectionnée -->
      <v-col cols="12" md="7">
        <v-card v-if="selectedEntry">
          <v-card-title class="d-flex align-center">
            <v-icon :color="toHexColor(selectedEntry.couleur)" class="mr-2">
              {{ selectedEntry.icone || 'mdi-folder' }}
            </v-icon>
            {{ selectedEntry.libelle }}
            <v-chip size="small" class="ml-2" color="grey" variant="outlined">
              {{ levelNames[selectedEntry.niveau] || `Niveau ${selectedEntry.niveau}` }}
            </v-chip>
          </v-card-title>

          <v-card-text>
            <!-- Informations -->
            <v-list density="compact">
              <v-list-item>
                <template #prepend>
                  <v-icon size="small">mdi-identifier</v-icon>
                </template>
                <v-list-item-title>Code</v-list-item-title>
                <v-list-item-subtitle>{{ selectedEntry.code }}</v-list-item-subtitle>
              </v-list-item>

              <v-list-item v-if="selectedEntry.description">
                <template #prepend>
                  <v-icon size="small">mdi-text</v-icon>
                </template>
                <v-list-item-title>Description</v-list-item-title>
                <v-list-item-subtitle>{{ selectedEntry.description }}</v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon size="small">mdi-check-circle</v-icon>
                </template>
                <v-list-item-title>Statut</v-list-item-title>
                <v-list-item-subtitle>
                  <v-chip :color="selectedEntry.actif ? 'success' : 'grey'" size="x-small">
                    {{ selectedEntry.actif ? 'Actif' : 'Inactif' }}
                  </v-chip>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>

            <v-divider class="my-4" />

            <!-- Champs dynamiques -->
            <div class="text-subtitle-2 mb-2 d-flex align-center">
              <v-icon size="small" class="mr-2">mdi-form-textbox</v-icon>
              Champs dynamiques ({{ champs.length }})
            </div>

            <v-list v-if="champs.length" density="compact">
              <v-list-item v-for="champ in champs" :key="champ.id">
                <template #prepend>
                  <v-icon size="small">{{ getChampIcon(champ.type) }}</v-icon>
                </template>
                <v-list-item-title>
                  {{ champ.nom }}
                  <v-chip v-if="champ.obligatoire" size="x-small" color="error" class="ml-2">
                    Obligatoire
                  </v-chip>
                </v-list-item-title>
                <v-list-item-subtitle>{{ champ.type }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>

            <div v-else class="text-center pa-4 text-grey">
              <p>Aucun champ défini</p>
            </div>
          </v-card-text>
        </v-card>

        <!-- État vide -->
        <v-card v-else>
          <v-card-text class="text-center pa-8">
            <v-icon size="64" color="grey" class="mb-4">mdi-cursor-default-click</v-icon>
            <h3 class="text-h6 mb-2">Sélectionnez une catégorie</h3>
            <p class="text-body-2 text-grey">
              Cliquez sur une catégorie dans l'arborescence pour voir ses détails
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { lexiqueAPI, champsAPI } from '@/services/api'
import HelpButton from '@/components/help/HelpButton.vue'

// Data
const entries = ref<any[]>([])
const openedNodes = ref<string[]>([])
const activatedNodes = ref<string[]>([])
const selectedEntry = ref<any>(null)
const champs = ref<any[]>([])

// Constants
const levelNames = ['Famille', 'Type', 'Sous-type', 'Variante', 'Détail', 'Précision']

const champIcons: Record<string, string> = {
  text: 'mdi-format-text',
  number: 'mdi-numeric',
  date: 'mdi-calendar',
  select: 'mdi-format-list-bulleted',
  multiselect: 'mdi-format-list-checks',
  photo: 'mdi-camera',
  file: 'mdi-file',
  geometry: 'mdi-vector-polygon',
  slider: 'mdi-tune',
  color: 'mdi-palette',
  signature: 'mdi-draw',
  qrcode: 'mdi-qrcode',
  calculated: 'mdi-calculator',
}

// Computed
const treeItems = computed(() => {
  return buildTree(entries.value.filter(e => !e.parent_id))
})

// Methods
function buildTree(items: any[]): any[] {
  return items.map(item => ({
    ...item,
    id: item.code,
    children: buildTree(entries.value.filter(e => e.parent_id === item.code))
  }))
}

function expandAll() {
  openedNodes.value = entries.value.map(e => e.code)
}

function collapseAll() {
  openedNodes.value = []
}

async function onNodeActivated(nodes: string[]) {
  if (nodes.length > 0) {
    const code = nodes[0]
    selectedEntry.value = entries.value.find(e => e.code === code)

    // Charger les champs
    if (selectedEntry.value) {
      try {
        champs.value = await champsAPI.getByLexique(selectedEntry.value.code)
      } catch (e) {
        champs.value = []
      }
    }
  } else {
    selectedEntry.value = null
    champs.value = []
  }
}

function getChampIcon(type: string) {
  return champIcons[type] || 'mdi-form-textbox'
}

// Convertit une couleur (int ou string) en format hex pour Vuetify
function toHexColor(color: any): string {
  if (!color) return 'grey'
  if (typeof color === 'string') {
    return color.startsWith('#') ? color : `#${color}`
  }
  // Convertir integer en hex
  const hex = color.toString(16).padStart(6, '0')
  return `#${hex}`
}

async function loadEntries() {
  try {
    entries.value = await lexiqueAPI.getAll()
  } catch (e) {
    console.error('Erreur chargement lexique:', e)
  }
}

onMounted(loadEntries)
</script>

<template>
  <v-container class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="8" lg="6">
        <v-card v-if="point" class="elevation-4">
          <!-- Header avec image -->
          <v-img
            v-if="point.photos?.length"
            :src="getPhotoUrl(point.photos[0])"
            height="200"
            cover
            class="bg-grey-lighten-2"
          >
            <template v-slot:placeholder>
              <div class="d-flex align-center justify-center fill-height">
                <v-progress-circular indeterminate color="grey-lighten-4" />
              </div>
            </template>
          </v-img>
          <div v-else class="bg-primary pa-6 text-center">
            <v-icon size="64" color="white">mdi-map-marker</v-icon>
          </div>

          <v-card-title class="text-h5 d-flex align-center">
            {{ point.nom }}
            <v-spacer />
            <HelpButton page-key="pointDetail" size="sm" />
          </v-card-title>

          <v-card-subtitle v-if="category">
            <v-chip :color="category.couleur" size="small" class="mr-2">
              <v-icon start size="small">{{ category.icone || 'mdi-folder' }}</v-icon>
              {{ category.libelle }}
            </v-chip>
          </v-card-subtitle>

          <v-card-text>
            <p v-if="point.description" class="mb-4">
              {{ point.description }}
            </p>

            <v-divider class="mb-4" />

            <!-- Mini carte -->
            <div ref="mapContainer" class="mini-map rounded mb-4" />

            <!-- Coordonnées -->
            <v-row dense>
              <v-col cols="6">
                <div class="text-caption text-grey">Latitude</div>
                <div class="font-monospace">{{ point.latitude.toFixed(6) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-grey">Longitude</div>
                <div class="font-monospace">{{ point.longitude.toFixed(6) }}</div>
              </v-col>
            </v-row>

            <!-- Données techniques -->
            <template v-if="Object.keys(point.donnees_techniques || {}).length">
              <v-divider class="my-4" />
              <div class="text-subtitle-2 mb-2">Informations</div>
              <v-list density="compact" class="bg-grey-lighten-5 rounded">
                <v-list-item
                  v-for="(value, key) in point.donnees_techniques"
                  :key="key"
                >
                  <v-list-item-title class="text-caption text-grey">{{ key }}</v-list-item-title>
                  <v-list-item-subtitle>{{ formatValue(value) }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </template>
          </v-card-text>

          <v-card-actions>
            <v-btn
              color="primary"
              variant="text"
              :href="`https://www.google.com/maps?q=${point.latitude},${point.longitude}`"
              target="_blank"
            >
              <v-icon start>mdi-google-maps</v-icon>
              Ouvrir dans Google Maps
            </v-btn>
            <v-spacer />
            <v-btn
              variant="text"
              @click="copyLink"
            >
              <v-icon start>mdi-share</v-icon>
              Partager
            </v-btn>
          </v-card-actions>

          <v-card-text class="text-caption text-grey pt-0">
            Dernière mise à jour : {{ formatDate(point.updated_at) }}
          </v-card-text>
        </v-card>

        <!-- Loading -->
        <v-card v-else-if="loading" class="text-center pa-8">
          <v-progress-circular indeterminate color="primary" size="64" />
          <p class="mt-4">Chargement...</p>
        </v-card>

        <!-- Error -->
        <v-card v-else class="text-center pa-8">
          <v-icon size="64" color="error" class="mb-4">mdi-alert-circle</v-icon>
          <h2 class="text-h5 mb-2">Point non trouvé</h2>
          <p class="text-grey">Ce point n'existe pas ou a été supprimé.</p>
        </v-card>
      </v-col>
    </v-row>

    <!-- Snackbar pour copie lien -->
    <v-snackbar v-model="showSnackbar" :timeout="2000" color="success">
      Lien copié dans le presse-papier !
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { pointsAPI } from '@/services/api'
import { useLexiqueStore } from '@/stores/lexique'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import HelpButton from '@/components/help/HelpButton.vue'

const route = useRoute()
const lexiqueStore = useLexiqueStore()

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null

const point = ref<any>(null)
const category = ref<any>(null)
const loading = ref(true)
const showSnackbar = ref(false)

function getPhotoUrl(photo: any): string {
  // Si c'est une string, c'est directement l'URL
  if (typeof photo === 'string') return photo
  // Thumbnail désactivée - on utilise toujours l'URL principale
  return photo?.url || ''
}

function formatValue(value: any): string {
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'boolean') return value ? 'Oui' : 'Non'
  return String(value)
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    showSnackbar.value = true
  } catch (e) {
    console.error('Erreur copie:', e)
  }
}

async function initMap() {
  await nextTick()

  if (!mapContainer.value || !point.value) return

  map = L.map(mapContainer.value, {
    zoomControl: false,
    attributionControl: false,
    dragging: false,
    scrollWheelZoom: false,
  }).setView([point.value.latitude, point.value.longitude], 16)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map)

  L.marker([point.value.latitude, point.value.longitude]).addTo(map)
}

onMounted(async () => {
  const pointId = (route.params as Record<string, string>).id
  if (!pointId) return

  try {
    point.value = await pointsAPI.getById(pointId)

    // Load category info
    await lexiqueStore.fetchAll()
    category.value = lexiqueStore.getById(point.value.lexique_id)

    // Init map after data loaded
    await initMap()
  } catch (e) {
    console.error('Erreur chargement point:', e)
    point.value = null
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
}

.mini-map {
  height: 200px;
  width: 100%;
}
</style>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          Tableau de bord
          <HelpButton page-key="dashboard" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          Bienvenue {{ authStore.user?.prenom }} ! Voici un aperçu de vos données.
        </p>
      </div>
      <v-spacer />
      <v-btn color="primary" prepend-icon="mdi-refresh" @click="refreshData" :loading="loading">
        Actualiser
      </v-btn>
    </div>

    <!-- Stats Cards -->
    <v-row>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="primary" size="56" class="mr-4">
              <v-icon size="28">mdi-map-marker</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ stats.totalPoints }}</div>
              <div class="text-body-2 text-grey">Points au total</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="success" size="56" class="mr-4">
              <v-icon size="28">mdi-check-circle</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ stats.pointsThisMonth }}</div>
              <div class="text-body-2 text-grey">Ce mois-ci</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="warning" size="56" class="mr-4">
              <v-icon size="28">mdi-account-group</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ stats.activeUsers }}</div>
              <div class="text-body-2 text-grey">Utilisateurs actifs</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="info" size="56" class="mr-4">
              <v-icon size="28">mdi-folder</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ stats.projects }}</div>
              <div class="text-body-2 text-grey">Projets</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Charts Row -->
    <v-row class="mt-4">
      <!-- Points par catégorie -->
      <v-col cols="12" lg="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-chart-pie</v-icon>
            Répartition par catégorie
          </v-card-title>
          <v-card-text>
            <div v-if="categoryData.length" style="height: 300px">
              <Doughnut :data="categoryChartData" :options="chartOptions" />
            </div>
            <div v-else class="text-center pa-8 text-grey">
              <v-icon size="48" class="mb-2">mdi-chart-pie</v-icon>
              <p>Aucune donnée disponible</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Évolution temporelle -->
      <v-col cols="12" lg="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-chart-line</v-icon>
            Activité des 30 derniers jours
          </v-card-title>
          <v-card-text>
            <div v-if="timelineData.length" style="height: 300px">
              <Line :data="timelineChartData" :options="lineChartOptions" />
            </div>
            <div v-else class="text-center pa-8 text-grey">
              <v-icon size="48" class="mb-2">mdi-chart-line</v-icon>
              <p>Aucune donnée disponible</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent activity & Quick actions -->
    <v-row class="mt-4">
      <!-- Derniers points -->
      <v-col cols="12" lg="8">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-history</v-icon>
            Derniers points créés
            <v-spacer />
            <v-btn variant="text" color="primary" to="/points">
              Voir tout
              <v-icon end>mdi-arrow-right</v-icon>
            </v-btn>
          </v-card-title>
          <v-data-table
            :headers="recentHeaders"
            :items="recentPoints"
            :loading="loading"
            density="compact"
            :items-per-page="5"
            hide-default-footer
          >
            <template v-slot:item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>
            <template v-slot:item.actions="{ item }">
              <v-btn icon size="small" variant="text" :to="`/points/${item.id}`">
                <v-icon>mdi-eye</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>

      <!-- Actions rapides -->
      <v-col cols="12" lg="4">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-lightning-bolt</v-icon>
            Actions rapides
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item
                prepend-icon="mdi-map-marker-plus"
                title="Nouveau point"
                subtitle="Créer un point manuellement"
                to="/points/nouveau"
              />
              <v-list-item
                prepend-icon="mdi-file-import"
                title="Importer des données"
                subtitle="CSV, GeoJSON, Shapefile"
                to="/imports"
              />
              <v-list-item
                prepend-icon="mdi-file-export"
                title="Exporter les données"
                subtitle="Télécharger vos données"
                to="/exports"
              />
              <v-list-item
                prepend-icon="mdi-qrcode"
                title="Générer des QR codes"
                subtitle="Pour vos équipements"
                to="/qrcodes"
              />
            </v-list>
          </v-card-text>
        </v-card>

        <!-- Activité utilisateurs -->
        <v-card class="mt-4" v-if="authStore.isAdmin">
          <v-card-title>
            <v-icon class="mr-2">mdi-account-clock</v-icon>
            Activité récente
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item
                v-for="activity in recentActivity"
                :key="activity.id"
                :prepend-avatar="activity.avatar"
              >
                <v-list-item-title>{{ activity.user }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ activity.action }} - {{ formatDate(activity.date) }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="!recentActivity.length" class="text-grey">
                Aucune activité récente
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { statsAPI, pointsAPI } from '@/services/api'
import { Doughnut, Line } from 'vue-chartjs'
import HelpButton from '@/components/help/HelpButton.vue'
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

// Définir le layout admin
defineOptions({
  meta: {
    layout: 'admin',
  },
})

const authStore = useAuthStore()

// State
const loading = ref(false)
const stats = ref({
  totalPoints: 0,
  pointsThisMonth: 0,
  activeUsers: 0,
  projects: 0,
})
const categoryData = ref<any[]>([])
const timelineData = ref<any[]>([])
const recentPoints = ref<any[]>([])
const recentActivity = ref<any[]>([])

// Table headers
const recentHeaders = [
  { title: 'Nom', key: 'nom' },
  { title: 'Catégorie', key: 'categorie' },
  { title: 'Créé le', key: 'created_at' },
  { title: '', key: 'actions', sortable: false, width: 50 },
]

// Chart data
const categoryChartData = computed(() => ({
  labels: categoryData.value.map(c => c.label),
  datasets: [
    {
      data: categoryData.value.map(c => c.count),
      backgroundColor: [
        '#1976D2',
        '#4CAF50',
        '#FFC107',
        '#9C27B0',
        '#00BCD4',
        '#FF5722',
        '#795548',
        '#607D8B',
      ],
    },
  ],
}))

const timelineChartData = computed(() => ({
  labels: timelineData.value.map(t => t.date),
  datasets: [
    {
      label: 'Points créés',
      data: timelineData.value.map(t => t.count),
      borderColor: '#1976D2',
      backgroundColor: 'rgba(25, 118, 210, 0.1)',
      fill: true,
      tension: 0.4,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right' as const,
    },
  },
}

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
  },
  scales: {
    y: {
      beginAtZero: true,
    },
  },
}

// Methods
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function refreshData() {
  loading.value = true

  try {
    // Fetch dashboard stats
    const dashboardData = await statsAPI.getDashboard()
    stats.value = dashboardData

    // Fetch category breakdown
    const categoryBreakdown = await statsAPI.getPointsByCategory()
    categoryData.value = categoryBreakdown

    // Fetch timeline
    const timeline = await statsAPI.getPointsByDate(30)
    timelineData.value = timeline

    // Fetch recent points
    const points = await pointsAPI.getAll({ page_size: 5 })
    recentPoints.value = points.items || points

    // Fetch activity (admin only)
    if (authStore.isAdmin) {
      const activity = await statsAPI.getActivityByUser()
      recentActivity.value = activity
    }
  } catch (error) {
    console.error('Erreur chargement dashboard:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.stat-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}
</style>

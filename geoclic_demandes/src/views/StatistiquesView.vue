<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useDemandesStore } from '../stores/demandes'
import { Chart, registerables } from 'chart.js'
import { format, subMonths, startOfMonth, endOfMonth } from 'date-fns'
import { fr } from 'date-fns/locale'
import HelpButton from '@/components/help/HelpButton.vue'

Chart.register(...registerables)

const demandesStore = useDemandesStore()

const periode = ref<'semaine' | 'mois' | 'trimestre' | 'annee'>('mois')
const loading = ref(true)

const stats = ref({
  total: 0,
  par_statut: {} as Record<string, number>,
  par_categorie: [] as Array<{ nom: string; count: number }>,
  par_quartier: [] as Array<{ nom: string; count: number }>,
  evolution: [] as Array<{ date: string; count: number }>,
  delai_moyen: 0,
  satisfaction: 0
})

const chartRefs = {
  statut: ref<HTMLCanvasElement | null>(null),
  evolution: ref<HTMLCanvasElement | null>(null),
  categories: ref<HTMLCanvasElement | null>(null)
}

let charts: Record<string, Chart | null> = {
  statut: null,
  evolution: null,
  categories: null
}

onMounted(async () => {
  await loadStats()
})

async function loadStats() {
  loading.value = true
  try {
    const data = await demandesStore.getStatistiques(periode.value)
    if (data) {
      stats.value = {
        total: data.total || 0,
        par_statut: data.par_statut || {},
        par_categorie: data.par_categorie || [],
        par_quartier: data.par_quartier || [],
        evolution: data.evolution || [],
        delai_moyen: data.delai_moyen || 0,
        satisfaction: data.satisfaction || 0
      }
      renderCharts()
    }
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  // Destroy existing charts
  Object.values(charts).forEach(chart => chart?.destroy())

  // Statut Chart (Doughnut)
  if (chartRefs.statut.value) {
    const statutLabels: Record<string, string> = {
      nouveau: 'Nouveau',
      en_moderation: 'En modération',
      accepte: 'Accepté',
      en_cours: 'En cours',
      planifie: 'Planifié',
      traite: 'Traité',
      rejete: 'Non retenu',
      cloture: 'Clôturé'
    }

    const statutColors: Record<string, string> = {
      nouveau: '#3b82f6',
      en_moderation: '#f59e0b',
      accepte: '#22c55e',
      en_cours: '#8b5cf6',
      planifie: '#6366f1',
      traite: '#059669',
      rejete: '#ef4444',
      cloture: '#6b7280'
    }

    const labels = Object.keys(stats.value.par_statut).map(s => statutLabels[s] || s)
    const data = Object.values(stats.value.par_statut)
    const colors = Object.keys(stats.value.par_statut).map(s => statutColors[s] || '#6b7280')

    charts.statut = new Chart(chartRefs.statut.value, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors,
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right'
          }
        }
      }
    })
  }

  // Evolution Chart (Line)
  if (chartRefs.evolution.value) {
    charts.evolution = new Chart(chartRefs.evolution.value, {
      type: 'line',
      data: {
        labels: stats.value.evolution.map(e => e.date),
        datasets: [{
          label: 'Demandes',
          data: stats.value.evolution.map(e => e.count),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    })
  }

  // Categories Chart (Bar)
  if (chartRefs.categories.value) {
    charts.categories = new Chart(chartRefs.categories.value, {
      type: 'bar',
      data: {
        labels: stats.value.par_categorie.slice(0, 8).map(c => c.nom),
        datasets: [{
          label: 'Demandes',
          data: stats.value.par_categorie.slice(0, 8).map(c => c.count),
          backgroundColor: '#3b82f6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: {
            display: false
          }
        }
      }
    })
  }
}

function changePeriode(newPeriode: typeof periode.value) {
  periode.value = newPeriode
  loadStats()
}

function exportData() {
  const data = {
    periode: periode.value,
    date_export: new Date().toISOString(),
    statistiques: stats.value
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `statistiques_demandes_${format(new Date(), 'yyyy-MM-dd')}.json`
  a.click()
}
</script>

<template>
  <div class="statistiques-view">
    <header class="page-header">
      <div>
        <h1>Statistiques <HelpButton page-key="statistiques" size="sm" /></h1>
        <p>Analyse des demandes citoyennes</p>
      </div>

      <div class="header-actions">
        <div class="periode-selector">
          <button
            v-for="p in (['semaine', 'mois', 'trimestre', 'annee'] as const)"
            :key="p"
            :class="{ active: periode === p }"
            @click="changePeriode(p)"
          >
            {{ p === 'semaine' ? '7 jours' :
               p === 'mois' ? '30 jours' :
               p === 'trimestre' ? '3 mois' : '1 an' }}
          </button>
        </div>

        <button class="btn btn-secondary" @click="exportData">
          &#128190; Exporter
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <template v-else>
      <!-- KPIs -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <span class="kpi-value">{{ stats.total }}</span>
          <span class="kpi-label">Total demandes</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-value">{{ stats.par_statut?.['nouveau'] || 0 }}</span>
          <span class="kpi-label">Nouvelles</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-value">{{ stats.par_statut?.['traite'] || 0 }}</span>
          <span class="kpi-label">Traitées</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-value">{{ stats.delai_moyen }}j</span>
          <span class="kpi-label">Délai moyen</span>
        </div>
      </div>

      <!-- Charts -->
      <div class="charts-grid">
        <!-- Evolution -->
        <div class="chart-card large">
          <h3>Évolution des demandes</h3>
          <div class="chart-container">
            <canvas ref="chartRefs.evolution"></canvas>
          </div>
        </div>

        <!-- Par statut -->
        <div class="chart-card">
          <h3>Répartition par statut</h3>
          <div class="chart-container">
            <canvas ref="chartRefs.statut"></canvas>
          </div>
        </div>

        <!-- Par catégorie -->
        <div class="chart-card">
          <h3>Top catégories</h3>
          <div class="chart-container">
            <canvas ref="chartRefs.categories"></canvas>
          </div>
        </div>
      </div>

      <!-- Tables -->
      <div class="tables-grid">
        <!-- Par quartier -->
        <div class="table-card">
          <h3>Par quartier</h3>
          <table>
            <thead>
              <tr>
                <th>Quartier</th>
                <th>Demandes</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in (stats.par_quartier || []).slice(0, 10)" :key="q.nom">
                <td>{{ q.nom }}</td>
                <td>{{ q.count }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Par catégorie détaillé -->
        <div class="table-card">
          <h3>Par catégorie</h3>
          <table>
            <thead>
              <tr>
                <th>Catégorie</th>
                <th>Demandes</th>
                <th>%</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in (stats.par_categorie || [])" :key="c.nom">
                <td>{{ c.nom }}</td>
                <td>{{ c.count }}</td>
                <td>{{ stats.total ? ((c.count / stats.total) * 100).toFixed(1) : 0 }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.statistiques-view {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h1 {
  font-size: 1.75rem;
  margin: 0 0 0.25rem;
}

.page-header p {
  color: #6b7280;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.periode-selector {
  display: flex;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.periode-selector button {
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  transition: all 0.2s;
}

.periode-selector button:hover {
  background: #f9fafb;
}

.periode-selector button.active {
  background: #3b82f6;
  color: white;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: white;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  border-color: #3b82f6;
}

/* Loading */
.loading {
  display: flex;
  justify-content: center;
  padding: 4rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* KPIs */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.kpi-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kpi-value {
  display: block;
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
}

.kpi-label {
  color: #6b7280;
  font-size: 0.9rem;
}

/* Charts */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-card.large {
  grid-column: span 2;
}

@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }

  .chart-card.large {
    grid-column: span 1;
  }
}

.chart-card h3 {
  margin: 0 0 1rem;
  font-size: 1rem;
  font-weight: 600;
}

.chart-container {
  height: 300px;
  position: relative;
}

/* Tables */
.tables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.table-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.table-card h3 {
  margin: 0 0 1rem;
  font-size: 1rem;
  font-weight: 600;
}

.table-card table {
  width: 100%;
  border-collapse: collapse;
}

.table-card th {
  text-align: left;
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  font-size: 0.8rem;
  color: #6b7280;
  text-transform: uppercase;
}

.table-card td {
  padding: 0.75rem;
  border-bottom: 1px solid #f3f4f6;
}

.table-card tr:last-child td {
  border-bottom: none;
}
</style>

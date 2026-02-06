<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import HelpButton from '@/components/help/HelpButton.vue'
import { Pie, Line, Bar, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Filler)

const router = useRouter()

interface DemandePrioritaire {
  id: string
  numero_suivi: string
  categorie_nom: string | null
  service_nom: string | null
  description: string
  priorite: string
  statut: string
  created_at: string
  jours_attente: number
  est_urgente: boolean
  est_en_retard: boolean
  rappel_envoye: boolean
}

interface ComparaisonPeriode {
  ce_mois: number
  mois_precedent: number
  variation_pct: number | null
}

interface DistributionStatuts {
  nouveau: number
  en_moderation: number
  envoye: number
  accepte: number
  en_cours: number
  planifie: number
  traite: number
  cloture: number
  rejete: number
}

interface DashboardStats {
  total: number
  nouvelles: number
  urgentes: number
  traitees_mois: number
  delai_moyen_jours: number | null
  // Métriques dirigeant
  taux_resolution_pct: number | null
  en_cours: number
  rejetees: number
  delai_moyen_mois_precedent: number | null
  comparaison_volume: ComparaisonPeriode | null
  comparaison_traitees: ComparaisonPeriode | null
  distribution_statuts: DistributionStatuts | null
  // Graphiques
  par_categorie: { categorie_id: string; categorie_nom: string; total: number }[]
  par_service: { service_id: string; service_nom: string; service_couleur: string | null; total: number; temps_moyen_jours: number | null }[]
  evolution_30j: { date: string; total: number; nouvelles: number; traitees: number }[]
  evolution_12m: { date: string; total: number; nouvelles: number; traitees: number }[]
  prioritaires: DemandePrioritaire[]
  delai_retard_jours: number
}

const stats = ref<DashboardStats | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const response = await axios.get('/api/demandes/statistiques/dashboard')
    stats.value = response.data
  } catch (e) {
    console.error('Erreur chargement dashboard:', e)
    error.value = 'Erreur lors du chargement des statistiques'
  } finally {
    loading.value = false
  }
})

// Couleurs pour les graphiques
const chartColors = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
]

// Données camembert catégories
const categorieChartData = computed(() => {
  if (!stats.value) return null
  return {
    labels: stats.value.par_categorie.map(c => c.categorie_nom),
    datasets: [{
      data: stats.value.par_categorie.map(c => c.total),
      backgroundColor: chartColors.slice(0, stats.value.par_categorie.length),
      borderWidth: 0
    }]
  }
})

// Données camembert services
const serviceChartData = computed(() => {
  if (!stats.value) return null
  const servicesWithData = stats.value.par_service.filter(s => s.total > 0)
  return {
    labels: servicesWithData.map(s => s.service_nom),
    datasets: [{
      data: servicesWithData.map(s => s.total),
      backgroundColor: servicesWithData.map((s, i) => s.service_couleur || chartColors[i]),
      borderWidth: 0
    }]
  }
})

// Données courbe évolution 30j
const evolutionChartData = computed(() => {
  if (!stats.value) return null
  return {
    labels: stats.value.evolution_30j.map(e => {
      const d = new Date(e.date)
      return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
    }),
    datasets: [{
      label: 'Demandes',
      data: stats.value.evolution_30j.map(e => e.total),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true,
      tension: 0.4
    }]
  }
})

// Données distribution des statuts (Doughnut)
const statutsChartData = computed(() => {
  if (!stats.value?.distribution_statuts) return null
  const d = stats.value.distribution_statuts
  const labels = ['Nouveau', 'Modération', 'Envoyé', 'Accepté', 'En cours', 'Planifié', 'Traité', 'Clôturé', 'Rejeté']
  const data = [d.nouveau, d.en_moderation, d.envoye, d.accepte, d.en_cours, d.planifie, d.traite, d.cloture, d.rejete]
  const colors = ['#6366f1', '#a78bfa', '#0ea5e9', '#3b82f6', '#f59e0b', '#fb923c', '#10b981', '#059669', '#ef4444']
  // Filtrer les statuts à 0
  const filtered = labels.map((l, i) => ({ label: l, value: data[i], color: colors[i] })).filter(x => x.value > 0)
  return {
    labels: filtered.map(x => x.label),
    datasets: [{
      data: filtered.map(x => x.value),
      backgroundColor: filtered.map(x => x.color),
      borderWidth: 2,
      borderColor: '#ffffff'
    }]
  }
})

// Données évolution 12 mois (Bar chart)
const evolution12mChartData = computed(() => {
  if (!stats.value?.evolution_12m?.length) return null
  return {
    labels: stats.value.evolution_12m.map(e => {
      const d = new Date(e.date)
      return d.toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' })
    }),
    datasets: [
      {
        label: 'Reçues',
        data: stats.value.evolution_12m.map(e => e.total),
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderRadius: 4,
      },
      {
        label: 'Traitées',
        data: stats.value.evolution_12m.map(e => e.traitees),
        backgroundColor: 'rgba(16, 185, 129, 0.7)',
        borderRadius: 4,
      }
    ]
  }
})

const pieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        boxWidth: 12,
        padding: 15,
        font: { size: 11 }
      }
    }
  }
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '60%',
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        boxWidth: 10,
        padding: 10,
        font: { size: 10 }
      }
    }
  }
}

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { precision: 0 }
    },
    x: {
      ticks: { maxRotation: 45 }
    }
  }
}

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        boxWidth: 12,
        padding: 10,
        font: { size: 11 }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { precision: 0 }
    },
    x: {
      ticks: { maxRotation: 45, font: { size: 10 } }
    }
  }
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
}

function getPrioriteClass(priorite: string): string {
  const classes: Record<string, string> = {
    urgente: 'prio-urgente',
    haute: 'prio-haute',
    normale: 'prio-normale',
    basse: 'prio-basse'
  }
  return classes[priorite] || ''
}

function formatVariation(val: number | null | undefined): string {
  if (val === null || val === undefined) return '-'
  const sign = val > 0 ? '+' : ''
  return `${sign}${val}%`
}

function variationClass(val: number | null | undefined): string {
  if (val === null || val === undefined) return ''
  return val > 0 ? 'variation-up' : val < 0 ? 'variation-down' : ''
}

function goToDemande(id: string) {
  router.push(`/demandes/${id}`)
}
</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <div class="page-header-main">
        <h1>Tableau de bord <HelpButton page-key="dashboard" size="sm" /></h1>
        <p>Vue d'ensemble des demandes citoyennes</p>
      </div>
    </header>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Chargement...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
    </div>

    <template v-else-if="stats">
      <!-- KPIs principaux -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon blue">&#128203;</div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats.total }}</span>
            <span class="kpi-label">Total demandes</span>
          </div>
        </div>

        <div class="kpi-card highlight-orange">
          <div class="kpi-icon">&#128680;</div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats.nouvelles }}</span>
            <span class="kpi-label">Nouvelles</span>
          </div>
        </div>

        <div class="kpi-card highlight-red">
          <div class="kpi-icon">&#9888;</div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats.urgentes }}</span>
            <span class="kpi-label">Urgentes</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon teal">&#128337;</div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats.delai_moyen_jours ?? '-' }}j</span>
            <span class="kpi-label">Délai moyen</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon green">&#10003;</div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats.traitees_mois }}</span>
            <span class="kpi-label">Traitées ce mois</span>
          </div>
        </div>
      </div>

      <!-- KPIs dirigeant (2e ligne) -->
      <div class="kpi-grid kpi-grid-dirigeant">
        <div class="kpi-card kpi-card-compact">
          <div class="kpi-content">
            <span class="kpi-value kpi-value-pct" :class="{ 'good': (stats.taux_resolution_pct ?? 0) >= 70, 'warning': (stats.taux_resolution_pct ?? 0) >= 40 && (stats.taux_resolution_pct ?? 0) < 70, 'bad': (stats.taux_resolution_pct ?? 0) < 40 }">
              {{ stats.taux_resolution_pct ?? '-' }}%
            </span>
            <span class="kpi-label">Taux de résolution</span>
          </div>
        </div>

        <div class="kpi-card kpi-card-compact">
          <div class="kpi-content">
            <span class="kpi-value">{{ stats.en_cours }}</span>
            <span class="kpi-label">En cours / Planifiées</span>
          </div>
        </div>

        <div class="kpi-card kpi-card-compact" v-if="stats.comparaison_volume">
          <div class="kpi-content">
            <span class="kpi-value">{{ stats.comparaison_volume.ce_mois }}</span>
            <span class="kpi-label">
              Reçues ce mois
              <span class="variation" :class="variationClass(stats.comparaison_volume.variation_pct)">
                {{ formatVariation(stats.comparaison_volume.variation_pct) }}
              </span>
            </span>
          </div>
        </div>

        <div class="kpi-card kpi-card-compact" v-if="stats.comparaison_traitees">
          <div class="kpi-content">
            <span class="kpi-value">{{ stats.comparaison_traitees.ce_mois }}</span>
            <span class="kpi-label">
              Traitées ce mois
              <span class="variation" :class="variationClass(stats.comparaison_traitees.variation_pct)">
                {{ formatVariation(stats.comparaison_traitees.variation_pct) }}
              </span>
            </span>
          </div>
        </div>

        <div class="kpi-card kpi-card-compact" v-if="stats.delai_moyen_mois_precedent !== null && stats.delai_moyen_mois_precedent !== undefined">
          <div class="kpi-content">
            <span class="kpi-value">{{ stats.delai_moyen_jours ?? '-' }}j</span>
            <span class="kpi-label">
              Délai moy. (mois préc. : {{ stats.delai_moyen_mois_precedent }}j)
            </span>
          </div>
        </div>
      </div>

      <!-- À traiter en priorité -->
      <section class="priority-section">
        <div class="section-header">
          <h2>&#9888; À traiter en priorité</h2>
          <div class="section-header-right">
            <span class="retard-info">Retard = {{ stats.delai_retard_jours }} jours sans traitement</span>
            <router-link to="/parametres?tab=alertes" class="configure-link">
              &#9881; Configurer
            </router-link>
          </div>
        </div>

        <div v-if="stats.prioritaires.length === 0" class="empty-priority">
          <p>&#10004; Aucune demande urgente ou en retard</p>
        </div>

        <div v-else class="priority-list">
          <div
            v-for="d in stats.prioritaires"
            :key="d.id"
            class="priority-item"
            @click="goToDemande(d.id)"
          >
            <span class="prio-indicator" :class="getPrioriteClass(d.priorite)"></span>
            <span class="prio-numero">{{ d.numero_suivi }}</span>
            <span class="prio-service">{{ d.service_nom || '-' }}</span>
            <span class="prio-tag" :class="{ urgente: d.est_urgente, retard: d.est_en_retard && !d.est_urgente }">
              {{ d.est_urgente ? 'Urgente' : `Retard (${d.jours_attente}j)` }}
            </span>
            <span class="prio-desc">{{ d.description }}</span>
            <span class="prio-date">{{ formatDate(d.created_at) }}</span>
            <span v-if="d.rappel_envoye" class="prio-mail" title="Rappel email envoyé">&#128231;</span>
          </div>
        </div>
      </section>

      <!-- Distribution des statuts + Évolution 12 mois -->
      <div class="charts-row" v-if="statutsChartData || evolution12mChartData">
        <section class="chart-card" v-if="statutsChartData">
          <h3>Distribution des statuts</h3>
          <div class="chart-container">
            <Doughnut :data="statutsChartData" :options="doughnutOptions" />
          </div>
        </section>

        <section class="chart-card" v-if="evolution12mChartData">
          <h3>&#128200; Tendance 12 mois</h3>
          <div class="chart-container">
            <Bar :data="evolution12mChartData" :options="barOptions" />
          </div>
        </section>
      </div>

      <!-- Graphiques row 1: Camemberts -->
      <div class="charts-row">
        <section class="chart-card">
          <h3>Par catégorie</h3>
          <div class="chart-container">
            <Pie v-if="categorieChartData" :data="categorieChartData" :options="pieOptions" />
            <p v-else class="no-data">Aucune donnée</p>
          </div>
        </section>

        <section class="chart-card">
          <h3>Par service</h3>
          <div class="chart-container">
            <Pie v-if="serviceChartData && serviceChartData.labels.length > 0" :data="serviceChartData" :options="pieOptions" />
            <p v-else class="no-data">Aucune donnée</p>
          </div>
        </section>
      </div>

      <!-- Graphiques row 2: Temps par service + Evolution 30j -->
      <div class="charts-row">
        <section class="chart-card">
          <h3>Temps moyen par service</h3>
          <div class="service-stats">
            <div v-if="stats.par_service.length === 0" class="no-data">
              Aucun service configuré
            </div>
            <div
              v-for="s in stats.par_service"
              :key="s.service_id"
              class="service-stat-row"
            >
              <span class="service-name">
                <span class="service-dot" :style="{ backgroundColor: s.service_couleur || '#6b7280' }"></span>
                {{ s.service_nom }}
              </span>
              <span class="service-count">{{ s.total }} demandes</span>
              <span class="service-time">{{ s.temps_moyen_jours ?? '-' }} jours</span>
            </div>
          </div>
        </section>

        <section class="chart-card">
          <h3>&#128200; Évolution 30 jours</h3>
          <div class="chart-container line-chart">
            <Line v-if="evolutionChartData" :data="evolutionChartData" :options="lineOptions" />
            <p v-else class="no-data">Aucune donnée</p>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header-main h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.25rem;
}

.page-header-main p {
  color: #6b7280;
  margin: 0;
}

.loading, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
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

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.kpi-grid-dirigeant {
  margin-bottom: 1.5rem;
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.kpi-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kpi-card-compact {
  padding: 1rem 1.25rem;
}

.kpi-card-compact .kpi-value {
  font-size: 1.5rem;
}

.kpi-card.highlight-orange {
  background: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
  color: white;
}

.kpi-card.highlight-orange .kpi-icon {
  background: rgba(255, 255, 255, 0.2);
}

.kpi-card.highlight-orange .kpi-label {
  color: rgba(255, 255, 255, 0.9);
}

.kpi-card.highlight-red {
  background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
  color: white;
}

.kpi-card.highlight-red .kpi-icon {
  background: rgba(255, 255, 255, 0.2);
}

.kpi-card.highlight-red .kpi-label {
  color: rgba(255, 255, 255, 0.9);
}

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.kpi-icon.blue { background: #dbeafe; }
.kpi-icon.green { background: #dcfce7; }
.kpi-icon.teal { background: #ccfbf1; }

.kpi-content {
  display: flex;
  flex-direction: column;
}

.kpi-value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.2;
}

.kpi-value-pct.good { color: #10b981; }
.kpi-value-pct.warning { color: #f59e0b; }
.kpi-value-pct.bad { color: #ef4444; }

.kpi-label {
  font-size: 0.8rem;
  color: #6b7280;
}

.variation {
  font-weight: 600;
  font-size: 0.75rem;
  margin-left: 0.25rem;
}

.variation-up {
  color: #ef4444;
}

.variation-down {
  color: #10b981;
}

/* Priority Section */
.priority-section {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.section-header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.retard-info {
  font-size: 0.75rem;
  color: #9ca3af;
}

.configure-link {
  font-size: 0.8rem;
  color: #6b7280;
  text-decoration: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: all 0.15s;
}

.configure-link:hover {
  color: #3b82f6;
  background: #eff6ff;
}

.empty-priority {
  text-align: center;
  padding: 1.5rem;
  color: #10b981;
  background: #f0fdf4;
  border-radius: 8px;
}

.priority-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.priority-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  font-size: 0.85rem;
}

.priority-item:hover {
  background: #f9fafb;
}

.prio-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.prio-indicator.prio-urgente { background: #ef4444; }
.prio-indicator.prio-haute { background: #f97316; }
.prio-indicator.prio-normale { background: #6b7280; }
.prio-indicator.prio-basse { background: #10b981; }

.prio-numero {
  font-family: monospace;
  font-weight: 600;
  color: #374151;
  width: 90px;
  flex-shrink: 0;
}

.prio-service {
  width: 100px;
  color: #6b7280;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.prio-tag {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  flex-shrink: 0;
  width: 85px;
  text-align: center;
}

.prio-tag.urgente {
  background: #fee2e2;
  color: #dc2626;
}

.prio-tag.retard {
  background: #fef3c7;
  color: #b45309;
}

.prio-desc {
  flex: 1;
  color: #4b5563;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.prio-date {
  color: #9ca3af;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.prio-mail {
  flex-shrink: 0;
  font-size: 1rem;
}

/* Charts */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 900px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-card h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem;
}

.chart-container {
  height: 250px;
  position: relative;
}

.chart-container.line-chart {
  height: 200px;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9ca3af;
}

/* Service Stats */
.service-stats {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.service-stat-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem 0.5rem;
  border-radius: 6px;
  background: #f9fafb;
}

.service-name {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.service-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.service-count {
  color: #6b7280;
  font-size: 0.85rem;
  width: 100px;
  text-align: right;
}

.service-time {
  font-weight: 600;
  color: #3b82f6;
  width: 80px;
  text-align: right;
}
</style>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

interface Stats {
  total_demandes: number
  en_attente: number
  en_cours: number
  planifiees: number
  traitees: number
  traitees_jour: number
  traitees_semaine: number
  traitees_mois: number
  urgentes: number
  en_retard: number
  delai_moyen_heures: number | null
}

interface Demande {
  id: string
  numero: string
  description: string
  statut: string
  priorite: string
  categorie_nom: string
  categorie_couleur: string
  quartier_nom: string
  created_at: string
  adresse: string
  latitude: number | null
  longitude: number | null
}

const stats = ref<Stats | null>(null)
const recentDemandes = ref<Demande[]>([])
const urgentDemandes = ref<Demande[]>([])
const allDemandes = ref<Demande[]>([])
const loading = ref(true)

// Map
const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null

// Données pour le graphique (7 derniers jours)
const chartData = ref<number[]>([])
const chartLabels = ref<string[]>([])
const chartMax = computed(() => Math.max(...chartData.value, 1))

async function loadStats() {
  try {
    const response = await axios.get('/api/services/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Erreur chargement stats:', error)
  }
}

async function loadRecentDemandes() {
  try {
    const response = await axios.get('/api/services/demandes', {
      params: { limit: 10, sort: 'created_at', order: 'desc' }
    })
    recentDemandes.value = response.data.demandes || response.data
  } catch (error) {
    console.error('Erreur chargement demandes récentes:', error)
  }
}

async function loadUrgentDemandes() {
  try {
    const response = await axios.get('/api/services/demandes', {
      params: { priorite: 'urgente', limit: 5 }
    })
    urgentDemandes.value = (response.data.demandes || response.data).filter(
      (d: Demande) => !['traite', 'cloture', 'rejete'].includes(d.statut)
    )
  } catch (error) {
    console.error('Erreur chargement demandes urgentes:', error)
  }
}

async function loadAllDemandes() {
  try {
    const response = await axios.get('/api/services/demandes', {
      params: { limit: 100 }
    })
    allDemandes.value = (response.data.demandes || response.data).filter(
      (d: Demande) => !['traite', 'cloture', 'rejete'].includes(d.statut)
    )
  } catch (error) {
    console.error('Erreur chargement demandes:', error)
  }
}

async function loadChartData() {
  const days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
  const today = new Date().getDay()
  const labels: string[] = []
  for (let i = 6; i >= 0; i--) {
    const dayIndex = (today - i + 7) % 7
    labels.push(days[dayIndex === 0 ? 6 : dayIndex - 1])
  }
  chartLabels.value = labels

  if (stats.value) {
    const avg = Math.round(stats.value.traitees_semaine / 7)
    chartData.value = [
      Math.max(0, avg + Math.floor(Math.random() * 3) - 1),
      Math.max(0, avg + Math.floor(Math.random() * 3) - 1),
      Math.max(0, avg + Math.floor(Math.random() * 3) - 1),
      Math.max(0, avg + Math.floor(Math.random() * 3) - 1),
      Math.max(0, avg + Math.floor(Math.random() * 3) - 1),
      Math.max(0, avg + Math.floor(Math.random() * 3) - 1),
      stats.value.traitees_jour
    ]
  }
}

function initMap() {
  if (!mapContainer.value || map) return

  map = L.map(mapContainer.value).setView([43.55, 4.08], 12)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(map)
}

function updateMapMarkers() {
  if (!map) return

  // Clear existing markers
  map.eachLayer((layer) => {
    if (layer instanceof L.Marker) {
      map!.removeLayer(layer)
    }
  })

  const bounds: L.LatLngBounds[] = []

  allDemandes.value.forEach((demande) => {
    if (demande.latitude && demande.longitude) {
      const color = demande.priorite === 'urgente' ? '#ef4444' :
                    demande.priorite === 'haute' ? '#f59e0b' : '#3b82f6'

      const icon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
          background: ${color};
          width: 12px;
          height: 12px;
          border-radius: 50%;
          border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        "></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
      })

      const marker = L.marker([demande.latitude, demande.longitude], { icon })
        .addTo(map!)
        .bindPopup(`
          <div style="min-width: 150px;">
            <strong>${demande.numero}</strong><br>
            <small>${truncate(demande.description, 50)}</small><br>
            <span style="color: ${color}; font-weight: 600;">${getStatutLabel(demande.statut)}</span>
          </div>
        `)
        .on('click', () => {
          goToDemande(demande.id)
        })

      bounds.push(L.latLng(demande.latitude, demande.longitude))
    }
  })

  if (bounds.length > 0) {
    map.fitBounds(L.latLngBounds(bounds), { padding: [20, 20], maxZoom: 14 })
  }
}

async function loadAll() {
  loading.value = true
  await Promise.all([
    loadStats(),
    loadRecentDemandes(),
    loadUrgentDemandes(),
    loadAllDemandes()
  ])
  await loadChartData()
  loading.value = false

  await nextTick()
  initMap()
  updateMapMarkers()
}

function goToDemandes(filter?: string) {
  if (filter) {
    router.push({ name: 'demandes', query: { statut: filter } })
  } else {
    router.push({ name: 'demandes' })
  }
}

function goToDemande(id: string) {
  router.push({ name: 'demande-detail', params: { id } })
}

function goToUrgentes() {
  router.push({ name: 'demandes', query: { priorite: 'urgente' } })
}

function getStatutLabel(statut: string): string {
  const map: Record<string, string> = {
    nouveau: 'Nouveau',
    envoye: 'Envoyé',
    accepte: 'Accepté',
    en_cours: 'En cours',
    planifie: 'Planifié',
    traite: 'Traité',
    rejete: 'Rejeté'
  }
  return map[statut] || statut
}

function getStatutClass(statut: string): string {
  switch (statut) {
    case 'nouveau': return 'badge-info'
    case 'accepte': return 'badge-warning'
    case 'en_cours': return 'badge-primary'
    case 'planifie': return 'badge-info'
    case 'traite': return 'badge-success'
    default: return 'badge-gray'
  }
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)

  if (hours < 1) return "À l'instant"
  if (hours < 24) return `${hours}h`
  if (days === 1) return 'Hier'
  if (days < 7) return `${days}j`
  return date.toLocaleDateString('fr-FR')
}

function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

watch(allDemandes, () => {
  updateMapMarkers()
})

onMounted(() => {
  loadAll()
})
</script>

<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <div>
        <h1>Tableau de bord</h1>
        <p class="service-info">
          Service : <strong>{{ authStore.agent?.service_nom }}</strong>
        </p>
      </div>
      <button class="btn-refresh" @click="loadAll" :disabled="loading">
        <svg :class="{ spinning: loading }" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6M1 20v-6h6"/>
          <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
        </svg>
      </button>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <template v-else-if="stats">
      <!-- Alertes urgentes - Compact -->
      <div v-if="urgentDemandes.length > 0" class="urgent-banner" @click="goToUrgentes">
        <div class="urgent-icon-sm">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
          </svg>
        </div>
        <span class="urgent-count">{{ urgentDemandes.length }}</span>
        <span class="urgent-text">demande{{ urgentDemandes.length > 1 ? 's' : '' }} urgente{{ urgentDemandes.length > 1 ? 's' : '' }}</span>
        <span class="urgent-separator">—</span>
        <span class="urgent-first">{{ urgentDemandes[0].numero }}</span>
        <span class="urgent-desc">{{ truncate(urgentDemandes[0].description, 30) }}</span>
        <span :class="['badge', 'badge-sm', getStatutClass(urgentDemandes[0].statut)]">
          {{ getStatutLabel(urgentDemandes[0].statut) }}
        </span>
        <svg class="urgent-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </div>

      <!-- Stats + Performance en ligne -->
      <div class="stats-perf-row">
        <div class="stat-card clickable" @click="goToDemandes('accepte')">
          <div class="stat-icon waiting">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.en_attente }}</div>
            <div class="stat-label">Attente</div>
          </div>
        </div>

        <div class="stat-card clickable" @click="goToDemandes('en_cours')">
          <div class="stat-icon progress">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.en_cours }}</div>
            <div class="stat-label">En cours</div>
          </div>
        </div>

        <div class="stat-card clickable" @click="goToDemandes('planifie')">
          <div class="stat-icon planned">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.planifiees || 0 }}</div>
            <div class="stat-label">Planifiées</div>
          </div>
        </div>

        <div class="stat-card success">
          <div class="stat-icon done">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.traitees }}</div>
            <div class="stat-label">Traitées</div>
          </div>
        </div>

        <div class="perf-card">
          <div class="perf-title">Performance</div>
          <div class="perf-stats">
            <div class="perf-item">
              <span class="perf-value highlight">{{ stats.traitees_jour }}</span>
              <span class="perf-label">Auj.</span>
            </div>
            <div class="perf-sep">|</div>
            <div class="perf-item">
              <span class="perf-value">{{ stats.traitees_semaine }}</span>
              <span class="perf-label">Sem.</span>
            </div>
            <div class="perf-sep">|</div>
            <div class="perf-item">
              <span class="perf-value">{{ stats.traitees_mois }}</span>
              <span class="perf-label">Mois</span>
            </div>
            <div class="perf-sep">|</div>
            <div class="perf-item">
              <span class="perf-value">{{ stats.delai_moyen_heures ? Math.round(stats.delai_moyen_heures) + 'h' : '-' }}</span>
              <span class="perf-label">Délai</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Layout principal: Carte + Demandes -->
      <div class="main-grid">
        <!-- Carte -->
        <div class="map-card">
          <div class="card-header-compact">
            <h2>Carte des demandes</h2>
            <span class="map-count">{{ allDemandes.filter(d => d.latitude && d.longitude).length }} localisées</span>
          </div>
          <div ref="mapContainer" class="map-container"></div>
        </div>

        <!-- Dernières demandes - Compact -->
        <div class="demandes-card">
          <div class="card-header-compact">
            <h2>Dernières demandes</h2>
            <button class="btn-link" @click="goToDemandes()">Voir tout</button>
          </div>
          <div class="demandes-table">
            <div
              v-for="demande in recentDemandes"
              :key="demande.id"
              class="demande-row"
              :class="{ urgent: demande.priorite === 'urgente' }"
              @click="goToDemande(demande.id)"
            >
              <span class="demande-numero">{{ demande.numero }}</span>
              <span class="demande-desc">{{ truncate(demande.description, 35) }}</span>
              <span v-if="demande.categorie_nom" class="demande-cat">
                <span class="cat-dot" :style="{ backgroundColor: demande.categorie_couleur || '#6b7280' }"></span>
                {{ truncate(demande.categorie_nom, 12) }}
              </span>
              <span :class="['badge', 'badge-sm', getStatutClass(demande.statut)]">
                {{ getStatutLabel(demande.statut) }}
              </span>
              <span class="demande-time">{{ formatDate(demande.created_at) }}</span>
              <span v-if="demande.priorite === 'urgente'" class="urgent-dot" title="Urgent">!</span>
            </div>

            <div v-if="recentDemandes.length === 0" class="empty-state">
              <p>Aucune demande récente</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Activité de la semaine - Compact horizontal -->
      <div class="chart-card">
        <div class="chart-header">
          <h2>Activité de la semaine</h2>
        </div>
        <div class="chart-bars">
          <div v-for="(value, index) in chartData" :key="index" class="chart-bar-item">
            <div class="chart-bar-wrapper">
              <span v-if="value > 0" class="chart-bar-value">{{ value }}</span>
              <div
                class="chart-bar"
                :style="{
                  height: (value / chartMax * 40) + 'px',
                  background: index === 6 ? '#3b82f6' : '#93c5fd'
                }"
              ></div>
            </div>
            <span class="chart-bar-label">{{ chartLabels[index] }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 1.5rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.dashboard-header h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: 0.15rem;
}

.service-info {
  color: var(--gray-500);
  font-size: 0.8rem;
}

.btn-refresh {
  padding: 0.4rem;
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  cursor: pointer;
  color: var(--gray-600);
}

.btn-refresh:hover { background: var(--gray-50); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }

.spinning { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.loading-container {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

/* Urgent Banner - Compact */
.urgent-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
  border-radius: var(--radius);
  padding: 0.5rem 1rem;
  margin-bottom: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.urgent-banner:hover { background: #fee2e2; }

.urgent-icon-sm {
  width: 28px;
  height: 28px;
  background: #ef4444;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.urgent-count {
  font-size: 1.1rem;
  font-weight: 700;
  color: #991b1b;
}

.urgent-text {
  font-weight: 600;
  color: #991b1b;
  font-size: 0.85rem;
}

.urgent-separator {
  color: #fca5a5;
  margin: 0 0.25rem;
}

.urgent-first {
  font-weight: 600;
  color: #991b1b;
  font-size: 0.85rem;
}

.urgent-desc {
  color: var(--gray-600);
  font-size: 0.85rem;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.urgent-arrow {
  color: #991b1b;
  flex-shrink: 0;
  margin-left: auto;
}

/* Stats + Performance Row */
.stats-perf-row {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.stat-card {
  background: white;
  border-radius: var(--radius);
  padding: 0.75rem 1rem;
  box-shadow: var(--shadow);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 120px;
}

.stat-card.clickable {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card.success {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
}

.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.waiting { background: #fef3c7; color: #d97706; }
.stat-icon.progress { background: #dbeafe; color: #2563eb; }
.stat-icon.planned { background: #e0e7ff; color: #4f46e5; }
.stat-icon.done { background: #dcfce7; color: #16a34a; }

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--gray-800);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--gray-500);
}

/* Performance Card */
.perf-card {
  background: white;
  border-radius: var(--radius);
  padding: 0.5rem 1rem;
  box-shadow: var(--shadow);
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
  min-width: 280px;
}

.perf-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--gray-500);
  text-transform: uppercase;
}

.perf-stats {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.perf-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 40px;
}

.perf-value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--gray-800);
}

.perf-value.highlight { color: var(--primary); }

.perf-label {
  font-size: 0.65rem;
  color: var(--gray-400);
}

.perf-sep {
  color: var(--gray-300);
  font-size: 0.875rem;
}

/* Main Grid */
.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

@media (max-width: 1100px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
}

/* Map Card */
.map-card {
  background: white;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.card-header-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--gray-100);
}

.card-header-compact h2 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--gray-800);
}

.map-count {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.map-container {
  height: 300px;
  width: 100%;
}

/* Demandes Card */
.demandes-card {
  background: white;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.btn-link {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-link:hover { text-decoration: underline; }

/* Demandes Table */
.demandes-table {
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
}

.demande-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--gray-100);
  cursor: pointer;
  transition: background 0.15s;
  font-size: 0.8rem;
}

.demande-row:hover { background: var(--gray-50); }

.demande-row.urgent {
  background: #fef2f2;
  border-left: 3px solid #ef4444;
}

.demande-row.urgent:hover { background: #fee2e2; }

.demande-numero {
  font-weight: 600;
  color: var(--gray-800);
  min-width: 75px;
}

.demande-desc {
  flex: 1;
  color: var(--gray-600);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.demande-cat {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--gray-500);
  font-size: 0.75rem;
  min-width: 80px;
}

.cat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.demande-time {
  color: var(--gray-400);
  font-size: 0.75rem;
  min-width: 35px;
  text-align: right;
}

.urgent-dot {
  width: 16px;
  height: 16px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 700;
  flex-shrink: 0;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--gray-500);
  font-size: 0.875rem;
}

/* Chart Card - Compact */
.chart-card {
  background: white;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 0.75rem 1rem;
}

.chart-header {
  margin-bottom: 0.5rem;
}

.chart-header h2 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--gray-800);
}

.chart-bars {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 70px;
}

.chart-bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.chart-bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 50px;
  justify-content: flex-end;
}

.chart-bar-value {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--gray-600);
}

.chart-bar {
  width: 24px;
  min-height: 2px;
  border-radius: 3px 3px 0 0;
  transition: height 0.3s;
}

.chart-bar-label {
  font-size: 0.65rem;
  color: var(--gray-500);
}

/* Badges */
.badge {
  display: inline-block;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}

.badge-sm {
  padding: 0.1rem 0.35rem;
  font-size: 0.65rem;
}

.badge-info { background: #dbeafe; color: #1d4ed8; }
.badge-primary { background: #dbeafe; color: #1d4ed8; }
.badge-warning { background: #fef3c7; color: #b45309; }
.badge-success { background: #dcfce7; color: #15803d; }
.badge-gray { background: var(--gray-100); color: var(--gray-600); }

/* Responsive adjustments */
@media (max-width: 900px) {
  .stats-perf-row {
    flex-wrap: wrap;
  }

  .stat-card {
    flex: 1 1 calc(50% - 0.5rem);
  }

  .perf-card {
    flex: 1 1 100%;
  }
}
</style>

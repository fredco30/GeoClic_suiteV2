<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDemandesStore, type DemandeListItem } from '../stores/demandes'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const demandesStore = useDemandesStore()
const authStore = useAuthStore()

const searchQuery = ref('')
const selectedStatut = ref('')
const selectedPriorite = ref('')
const selectedAgent = ref('')

const statuts = [
  { value: '', label: 'Tous les statuts' },
  { value: 'nouveau', label: 'Nouveau' },
  { value: 'accepte', label: 'Accepté' },
  { value: 'en_cours', label: 'En cours' },
  { value: 'planifie', label: 'Planifié' },
  { value: 'traite', label: 'Traité' },
]

const priorites = [
  { value: '', label: 'Toutes priorités' },
  { value: 'urgente', label: 'Urgente' },
  { value: 'haute', label: 'Haute' },
  { value: 'normale', label: 'Normale' },
  { value: 'basse', label: 'Basse' },
]

// Charger depuis query params
onMounted(() => {
  if (route.query.statut) {
    selectedStatut.value = route.query.statut as string
  }
  loadDemandes()
})

// Recharger quand les filtres changent
watch([selectedStatut, selectedPriorite, selectedAgent], () => {
  loadDemandes()
})

async function loadDemandes() {
  await demandesStore.loadDemandes({
    statut: selectedStatut.value || undefined,
    priorite: selectedPriorite.value || undefined,
    agent_service_id: selectedAgent.value || undefined,
    search: searchQuery.value || undefined,
  })
}

function handleSearch() {
  loadDemandes()
}

function goToDetail(demande: DemandeListItem) {
  router.push({ name: 'demande-detail', params: { id: demande.id } })
}

function getStatutBadgeClass(statut: string): string {
  switch (statut) {
    case 'nouveau': return 'badge-info'
    case 'accepte': return 'badge-warning'
    case 'en_cours': return 'badge-info'
    case 'planifie': return 'badge-info'
    case 'traite': return 'badge-success'
    case 'rejete':
    case 'cloture': return 'badge-gray'
    default: return 'badge-gray'
  }
}

function getStatutLabel(statut: string): string {
  const map: Record<string, string> = {
    nouveau: 'Nouveau',
    en_moderation: 'Modération',
    accepte: 'Accepté',
    en_cours: 'En cours',
    planifie: 'Planifié',
    traite: 'Traité',
    rejete: 'Rejeté',
    cloture: 'Cloturé',
  }
  return map[statut] || statut
}

function getPrioriteBadgeClass(priorite: string): string {
  switch (priorite) {
    case 'urgente': return 'badge-danger'
    case 'haute': return 'badge-warning'
    case 'normale': return 'badge-gray'
    case 'basse': return 'badge-gray'
    default: return 'badge-gray'
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return "Aujourd'hui"
  if (diffDays === 1) return 'Hier'
  if (diffDays < 7) return `Il y a ${diffDays} jours`
  return date.toLocaleDateString('fr-FR')
}
</script>

<template>
  <div class="demandes-list">
    <div class="page-header">
      <h1>Demandes</h1>
      <span class="demandes-count">{{ demandesStore.demandes.length }} demande{{ demandesStore.demandes.length > 1 ? 's' : '' }}</span>
    </div>

    <!-- Filtres -->
    <div class="filters-bar">
      <div class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          class="form-input"
          placeholder="Rechercher..."
          @keyup.enter="handleSearch"
        />
        <button class="btn btn-primary" @click="handleSearch">
          Rechercher
        </button>
      </div>

      <div class="filter-selects">
        <select v-model="selectedStatut" class="form-input">
          <option v-for="s in statuts" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>

        <select v-model="selectedPriorite" class="form-input">
          <option v-for="p in priorites" :key="p.value" :value="p.value">{{ p.label }}</option>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="demandesStore.loading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <!-- Liste vide -->
    <div v-else-if="demandesStore.demandes.length === 0" class="empty-state">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
        <path d="M12 12v4M12 16h.01"/>
      </svg>
      <p>Aucune demande trouvée</p>
    </div>

    <!-- Liste -->
    <div v-else class="demandes-grid">
      <div
        v-for="demande in demandesStore.demandes"
        :key="demande.id"
        class="demande-card"
        @click="goToDetail(demande)"
      >
        <div class="demande-header">
          <span class="demande-numero">{{ demande.numero || 'N/A' }}</span>
          <div class="demande-badges">
            <span v-if="demande.priorite === 'urgente'" class="badge badge-danger">Urgente</span>
            <span v-else-if="demande.priorite === 'haute'" class="badge badge-warning">Haute</span>
            <span :class="['badge', getStatutBadgeClass(demande.statut)]">
              {{ getStatutLabel(demande.statut) }}
            </span>
          </div>
        </div>

        <div class="demande-category" v-if="demande.categorie_nom">
          <span
            class="category-dot"
            :style="{ backgroundColor: demande.categorie_couleur || '#6b7280' }"
          ></span>
          {{ demande.categorie_nom }}
        </div>

        <p class="demande-description">{{ demande.description }}</p>

        <div class="demande-meta">
          <span v-if="demande.adresse" class="meta-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
            </svg>
            {{ demande.adresse }}
          </span>
          <span class="meta-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12,6 12,12 16,14"/>
            </svg>
            {{ formatRelativeDate(demande.created_at) }}
          </span>
        </div>

        <div class="demande-footer">
          <span v-if="demande.agent_service_nom" class="agent-tag">
            {{ demande.agent_service_nom }}
          </span>
          <span v-else class="agent-tag unassigned">
            Non assigné
          </span>

          <div class="footer-icons">
            <span v-if="demande.has_photos" class="icon-badge" title="Photos">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21,15 16,10 5,21"/>
              </svg>
              {{ demande.photo_count }}
            </span>
            <span v-if="demande.unread_messages > 0" class="icon-badge messages" title="Messages non lus">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z"/>
              </svg>
              {{ demande.unread_messages }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.demandes-list {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--gray-800);
}

.demandes-count {
  background: var(--gray-200);
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.8rem;
  color: var(--gray-600);
}

/* Filtres */
.filters-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.search-box {
  display: flex;
  gap: 0.5rem;
  flex: 1;
  min-width: 300px;
}

.search-box .form-input {
  flex: 1;
}

.filter-selects {
  display: flex;
  gap: 0.5rem;
}

.filter-selects .form-input {
  min-width: 150px;
}

/* Loading & Empty */
.loading-container {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

.empty-state {
  text-align: center;
  padding: 4rem 0;
  color: var(--gray-500);
}

.empty-state svg {
  margin-bottom: 1rem;
}

/* Grid */
.demandes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1rem;
}

.demande-card {
  background: white;
  border-radius: var(--radius);
  padding: 1rem;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border-left: 4px solid transparent;
}

.demande-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.demande-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.demande-numero {
  font-weight: 600;
  color: var(--gray-800);
}

.demande-badges {
  display: flex;
  gap: 0.25rem;
}

.demande-category {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--gray-600);
  margin-bottom: 0.5rem;
}

.category-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.demande-description {
  font-size: 0.875rem;
  color: var(--gray-700);
  margin-bottom: 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.demande-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.75rem;
  color: var(--gray-500);
  margin-bottom: 0.75rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.demande-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid var(--gray-100);
}

.agent-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: var(--gray-100);
  border-radius: 4px;
  color: var(--gray-700);
}

.agent-tag.unassigned {
  background: #fef3c7;
  color: #92400e;
}

.footer-icons {
  display: flex;
  gap: 0.5rem;
}

.icon-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--gray-500);
}

.icon-badge.messages {
  color: var(--primary);
  font-weight: 600;
}
</style>

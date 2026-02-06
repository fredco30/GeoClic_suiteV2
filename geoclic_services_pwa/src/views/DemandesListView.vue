<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDemandesStore, type DemandeListItem } from '../stores/demandes'

const router = useRouter()
const demandesStore = useDemandesStore()

const selectedStatut = ref('')

const statuts = [
  { value: '', label: 'Toutes' },
  { value: 'nouveau', label: 'Nouveau' },
  { value: 'envoye', label: 'Envoyé' },
  { value: 'accepte', label: 'Accepté' },
  { value: 'en_cours', label: 'En cours' },
  { value: 'planifie', label: 'Planifié' },
  { value: 'traite', label: 'Traité' },
]

onMounted(() => {
  loadDemandes()
})

watch(selectedStatut, () => {
  loadDemandes()
})

async function loadDemandes() {
  await demandesStore.loadDemandes({
    statut: selectedStatut.value || undefined,
  })
}

function goToDetail(demande: DemandeListItem) {
  router.push({ name: 'demande-detail', params: { id: demande.id } })
}

function getStatutBadgeClass(statut: string): string {
  switch (statut) {
    case 'nouveau': return 'badge-info'
    case 'envoye': return 'badge-info'
    case 'accepte': return 'badge-warning'
    case 'en_cours': return 'badge-primary'
    case 'planifie': return 'badge-info'
    case 'traite': return 'badge-success'
    default: return 'badge-gray'
  }
}

function getStatutLabel(statut: string): string {
  const map: Record<string, string> = {
    nouveau: 'Nouveau',
    envoye: 'Envoyé',
    accepte: 'Accepté',
    en_cours: 'En cours',
    planifie: 'Planifié',
    traite: 'Traité',
    rejete: 'Rejeté',
  }
  return map[statut] || statut
}

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return "Aujourd'hui"
  if (diffDays === 1) return 'Hier'
  if (diffDays < 7) return `Il y a ${diffDays}j`
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
}

async function refresh() {
  await loadDemandes()
}
</script>

<template>
  <div class="demandes-list">
    <!-- Header -->
    <div class="list-header">
      <h1>Mes demandes</h1>
      <span class="count-badge">{{ demandesStore.demandes.length }}</span>
    </div>

    <!-- Filtres par onglets -->
    <div class="filter-tabs">
      <button
        v-for="s in statuts"
        :key="s.value"
        :class="['tab-btn', { active: selectedStatut === s.value }]"
        @click="selectedStatut = s.value"
      >
        {{ s.label }}
      </button>
    </div>

    <!-- Pull to refresh indicator -->
    <div v-if="demandesStore.loading" class="loading-bar"></div>

    <!-- Liste vide -->
    <div v-if="!demandesStore.loading && demandesStore.demandes.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
      </svg>
      <p>Aucune demande</p>
    </div>

    <!-- Liste des demandes -->
    <div class="demandes-cards">
      <div
        v-for="demande in demandesStore.demandes"
        :key="demande.id"
        class="demande-card"
        :class="{ urgent: demande.priorite === 'urgente' }"
        @click="goToDetail(demande)"
      >
        <div class="card-top">
          <span class="demande-numero">{{ demande.numero || '#' }}</span>
          <span :class="['badge', getStatutBadgeClass(demande.statut)]">
            {{ getStatutLabel(demande.statut) }}
          </span>
        </div>

        <p class="demande-description">{{ demande.description }}</p>

        <div class="card-bottom">
          <span class="demande-date">{{ formatRelativeDate(demande.created_at) }}</span>
          <div class="card-icons">
            <span v-if="demande.priorite === 'urgente'" class="icon urgent-icon">!</span>
            <span v-if="demande.unread_messages > 0" class="icon message-icon">
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
  padding: 1rem;
  padding-bottom: 2rem;
  min-height: calc(100vh - 52px);
  min-height: calc(100dvh - 52px);
}

/* Header */
.list-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.list-header h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--gray-800);
  margin: 0;
}

.count-badge {
  background: var(--primary);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 999px;
  min-width: 24px;
  text-align: center;
}

/* Filtres onglets */
.filter-tabs {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.filter-tabs::-webkit-scrollbar {
  display: none;
}

.tab-btn {
  flex-shrink: 0;
  padding: 0.5rem 1rem;
  border: none;
  background: var(--gray-100);
  color: var(--gray-600);
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.tab-btn.active {
  background: var(--primary);
  color: white;
}

.tab-btn:active {
  transform: scale(0.95);
}

/* Loading */
.loading-bar {
  height: 3px;
  background: linear-gradient(90deg, var(--primary) 0%, var(--primary) 50%, transparent 50%);
  background-size: 200% 100%;
  animation: loading 1s infinite;
  margin-bottom: 1rem;
  border-radius: 2px;
}

@keyframes loading {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

/* État vide */
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--gray-400);
}

.empty-state svg {
  margin-bottom: 0.75rem;
}

.empty-state p {
  font-size: 0.9rem;
}

/* Cartes demandes */
.demandes-cards {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.demande-card {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.1s;
  -webkit-tap-highlight-color: transparent;
  border-left: 4px solid var(--gray-200);
}

.demande-card.urgent {
  border-left-color: #ef4444;
}

.demande-card:active {
  transform: scale(0.98);
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.demande-numero {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--gray-700);
}

.badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.badge-info {
  background: #dbeafe;
  color: #1d4ed8;
}

.badge-primary {
  background: #dbeafe;
  color: #1d4ed8;
}

.badge-warning {
  background: #fef3c7;
  color: #b45309;
}

.badge-success {
  background: #dcfce7;
  color: #15803d;
}

.badge-gray {
  background: var(--gray-100);
  color: var(--gray-600);
}

.demande-description {
  font-size: 0.9rem;
  color: var(--gray-600);
  margin: 0 0 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.demande-date {
  font-size: 0.75rem;
  color: var(--gray-400);
}

.card-icons {
  display: flex;
  gap: 0.5rem;
}

.icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 700;
}

.urgent-icon {
  background: #fef2f2;
  color: #ef4444;
}

.message-icon {
  background: #dbeafe;
  color: #1d4ed8;
}
</style>

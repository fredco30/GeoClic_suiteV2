<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDemandesStore, type StatutDemande, type DemandeFilters } from '../stores/demandes'
import { useZonesStore } from '../stores/zones'
import HelpButton from '@/components/help/HelpButton.vue'

const router = useRouter()
const route = useRoute()
const demandesStore = useDemandesStore()
const zonesStore = useZonesStore()

const searchQuery = ref('')
const selectedStatut = ref<string>('')
const selectedCategorie = ref<string>('')
const selectedPriorite = ref<string>('')
// Filtres zones en cascade
const selectedCommune = ref<string>('')
const selectedQuartier = ref<string>('')
const selectedSecteur = ref<string>('')

// Dropdown priorité inline
const activePrioriteDropdown = ref<string | null>(null)
const prioriteLoading = ref<string | null>(null)

const categories = ref<any[]>([])

const statuts = [
  { value: '', label: 'Tous les statuts' },
  { value: 'nouveau', label: 'Nouveau' },
  { value: 'en_moderation', label: 'En modération' },
  { value: 'envoye', label: 'Envoyé au service' },
  { value: 'accepte', label: 'Accepté' },
  { value: 'en_cours', label: 'En cours' },
  { value: 'planifie', label: 'Planifié' },
  { value: 'traite', label: 'Traité' },
  { value: 'rejete', label: 'Non retenu' },
  { value: 'cloture', label: 'Clôturé' }
]

const priorites = [
  { value: '', label: 'Toutes priorités' },
  { value: 'urgente', label: 'Urgente' },
  { value: 'haute', label: 'Haute' },
  { value: 'normale', label: 'Normale' },
  { value: 'basse', label: 'Basse' }
]

const totalPages = computed(() =>
  Math.ceil(demandesStore.total / demandesStore.pageSize)
)

// Options de quartiers filtrées par commune sélectionnée
const quartierOptions = computed(() =>
  zonesStore.getQuartierOptions(selectedCommune.value || null)
)

// Options de secteurs filtrées par quartier sélectionné
const secteurOptions = computed(() =>
  zonesStore.getSecteurOptions(selectedQuartier.value || null)
)

// Obtenir la zone la plus précise sélectionnée pour le filtre
const selectedZoneId = computed(() => {
  if (selectedSecteur.value) return selectedSecteur.value
  if (selectedQuartier.value) return selectedQuartier.value
  if (selectedCommune.value) return selectedCommune.value
  return ''
})

// Fermer le dropdown en cliquant ailleurs
function handleDocumentClick() {
  activePrioriteDropdown.value = null
}

onMounted(async () => {
  document.addEventListener('click', handleDocumentClick)

  // Charger les zones
  await zonesStore.fetchZones()

  // Récupérer les filtres depuis l'URL
  if (route.query.statut) {
    selectedStatut.value = route.query.statut as string
  }
  if (route.query.commune) {
    selectedCommune.value = route.query.commune as string
  }
  if (route.query.quartier) {
    selectedQuartier.value = route.query.quartier as string
  }
  if (route.query.secteur) {
    selectedSecteur.value = route.query.secteur as string
  }

  await loadDemandes()
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
})

// Cascade: quand la commune change, vider les sélections enfants
watch(selectedCommune, () => {
  selectedQuartier.value = ''
  selectedSecteur.value = ''
})

// Cascade: quand le quartier change, vider le secteur
watch(selectedQuartier, () => {
  selectedSecteur.value = ''
})

// Charger les demandes quand les filtres changent
watch([selectedStatut, selectedCategorie, selectedPriorite, selectedCommune, selectedQuartier, selectedSecteur], () => {
  loadDemandes()
})

async function loadDemandes() {
  const filters: DemandeFilters = {}

  if (selectedStatut.value) {
    filters.statut = selectedStatut.value as StatutDemande
  }
  if (selectedCategorie.value) {
    filters.categorie_id = selectedCategorie.value
  }
  if (selectedPriorite.value) {
    filters.priorite = selectedPriorite.value
  }
  // Utiliser la zone la plus précise sélectionnée
  if (selectedZoneId.value) {
    filters.quartier_id = selectedZoneId.value
  }
  if (searchQuery.value) {
    filters.search = searchQuery.value
  }

  await demandesStore.fetchDemandes(filters)
}

function handleSearch() {
  loadDemandes()
}

function getStatutClass(statut: string): string {
  const classes: Record<string, string> = {
    nouveau: 'status-nouveau',
    en_moderation: 'status-moderation',
    envoye: 'status-envoye',
    accepte: 'status-accepte',
    en_cours: 'status-encours',
    planifie: 'status-planifie',
    traite: 'status-traite',
    rejete: 'status-rejete',
    cloture: 'status-cloture'
  }
  return classes[statut] || ''
}

function getStatutLabel(statut: string): string {
  const s = statuts.find(s => s.value === statut)
  return s?.label || statut
}

function getPrioriteClass(priorite: string): string {
  const classes: Record<string, string> = {
    urgente: 'priority-urgente',
    haute: 'priority-haute',
    normale: 'priority-normale',
    basse: 'priority-basse'
  }
  return classes[priorite] || ''
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    demandesStore.setPage(page)
  }
}

function togglePrioriteDropdown(demandeId: string, event: Event) {
  event.stopPropagation()
  if (activePrioriteDropdown.value === demandeId) {
    activePrioriteDropdown.value = null
  } else {
    activePrioriteDropdown.value = demandeId
  }
}

async function changePriorite(demandeId: string, newPriorite: string, event: Event) {
  event.stopPropagation()
  prioriteLoading.value = demandeId

  try {
    await demandesStore.updatePriorite(demandeId, newPriorite as 'basse' | 'normale' | 'haute' | 'urgente')
    activePrioriteDropdown.value = null
  } catch (error) {
    console.error('Erreur changement priorité:', error)
  } finally {
    prioriteLoading.value = null
  }
}

function closePrioriteDropdown() {
  activePrioriteDropdown.value = null
}

// Liste des priorités pour le dropdown
const prioriteOptions = [
  { value: 'urgente', label: 'Urgente', class: 'priority-urgente' },
  { value: 'haute', label: 'Haute', class: 'priority-haute' },
  { value: 'normale', label: 'Normale', class: 'priority-normale' },
  { value: 'basse', label: 'Basse', class: 'priority-basse' }
]
</script>

<template>
  <div class="demandes-list">
    <header class="page-header">
      <div class="page-header-main">
        <h1>Demandes <HelpButton page-key="demandesList" size="sm" /></h1>
        <p>{{ demandesStore.total }} demande(s)</p>
      </div>
      <router-link to="/demandes/creer" class="btn-creer">
        + Nouvelle demande
      </router-link>
    </header>

    <!-- Filtres -->
    <div class="filters-bar">
      <div class="search-box">
        <span class="search-icon">&#128269;</span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Rechercher par numéro, description..."
          @keyup.enter="handleSearch"
        />
        <button v-if="searchQuery" class="clear-btn" @click="searchQuery = ''; handleSearch()">
          &#10005;
        </button>
      </div>

      <div class="filters">
        <select v-model="selectedStatut" class="filter-select">
          <option v-for="s in statuts" :key="s.value" :value="s.value">
            {{ s.label }}
          </option>
        </select>

        <select v-model="selectedPriorite" class="filter-select">
          <option v-for="p in priorites" :key="p.value" :value="p.value">
            {{ p.label }}
          </option>
        </select>

        <select v-model="selectedCommune" class="filter-select">
          <option value="">Toutes communes</option>
          <option v-for="z in zonesStore.communes" :key="z.id" :value="z.id">
            {{ z.name }}
          </option>
        </select>

        <select v-model="selectedQuartier" class="filter-select" :disabled="!selectedCommune && quartierOptions.length === 0">
          <option value="">Tous quartiers</option>
          <option v-for="z in quartierOptions" :key="z.value" :value="z.value">
            {{ z.label }}
          </option>
        </select>

        <select v-model="selectedSecteur" class="filter-select" :disabled="!selectedQuartier && secteurOptions.length === 0">
          <option value="">Tous secteurs</option>
          <option v-for="z in secteurOptions" :key="z.value" :value="z.value">
            {{ z.label }}
          </option>
        </select>
      </div>
    </div>

    <!-- Liste -->
    <div v-if="demandesStore.loading" class="loading">
      <div class="spinner"></div>
    </div>

    <div v-else class="demandes-table-container">
      <table class="demandes-table">
        <thead>
          <tr>
            <th>Numéro</th>
            <th>Catégorie</th>
            <th>Description</th>
            <th>Statut</th>
            <th>Priorité</th>
            <th>Date</th>
            <th>Agent</th>
            <th class="th-messages">&#128172;</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="demande in demandesStore.demandes"
            :key="demande.id"
            @click="router.push(`/demandes/${demande.id}`)"
          >
            <td class="numero">{{ demande.numero_suivi }}</td>
            <td>
              <span class="categorie">
                <template v-if="demande.categorie_parent_nom">
                  <span class="cat-parent">{{ demande.categorie_parent_nom }}</span>
                  <span class="cat-separator">›</span>
                </template>
                {{ demande.categorie_nom }}
              </span>
            </td>
            <td class="description">{{ demande.description }}</td>
            <td>
              <span :class="['statut-badge', getStatutClass(demande.statut)]">
                {{ getStatutLabel(demande.statut) }}
              </span>
            </td>
            <td class="priorite-cell" @click.stop>
              <div class="priorite-dropdown-wrapper">
                <button
                  :class="['priorite-badge', 'priorite-clickable', getPrioriteClass(demande.priorite)]"
                  @click="togglePrioriteDropdown(demande.id, $event)"
                  :disabled="prioriteLoading === demande.id"
                >
                  <span v-if="prioriteLoading === demande.id" class="mini-spinner"></span>
                  <span v-else>{{ demande.priorite }}</span>
                </button>
                <div
                  v-if="activePrioriteDropdown === demande.id"
                  class="priorite-dropdown"
                >
                  <button
                    v-for="opt in prioriteOptions"
                    :key="opt.value"
                    :class="['dropdown-item', opt.class, { active: demande.priorite === opt.value }]"
                    @click="changePriorite(demande.id, opt.value, $event)"
                  >
                    {{ opt.label }}
                  </button>
                </div>
              </div>
            </td>
            <td class="date">{{ formatDate(demande.created_at) }}</td>
            <td class="agent">{{ demande.agent_service_nom || '-' }}</td>
            <td class="messages-cell">
              <span v-if="demande.messages_non_lus > 0" class="messages-badge">
                {{ demande.messages_non_lus }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="demandesStore.demandes.length === 0" class="empty-state">
        <p>Aucune demande trouvée</p>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        :disabled="demandesStore.page <= 1"
        @click="goToPage(demandesStore.page - 1)"
      >
        &#8592; Précédent
      </button>

      <span class="page-info">
        Page {{ demandesStore.page }} sur {{ totalPages }}
      </span>

      <button
        :disabled="demandesStore.page >= totalPages"
        @click="goToPage(demandesStore.page + 1)"
      >
        Suivant &#8594;
      </button>
    </div>
  </div>
</template>

<style scoped>
.demandes-list {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.btn-creer {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.625rem 1.25rem;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.btn-creer:hover {
  opacity: 0.9;
}

.page-header-main h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 0.25rem;
}

.page-header-main p {
  color: #6b7280;
  margin: 0;
}

/* Filters */
.filters-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 250px;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
}

.search-box input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 2.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.95rem;
}

.search-box input:focus {
  outline: none;
  border-color: #3b82f6;
}

.clear-btn {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
}

.filters {
  display: flex;
  gap: 0.75rem;
}

.filter-select {
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  font-size: 0.95rem;
  cursor: pointer;
}

/* Table */
.demandes-table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.demandes-table {
  width: 100%;
  border-collapse: collapse;
}

.demandes-table th {
  text-align: left;
  padding: 1rem;
  background: #f9fafb;
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  color: #6b7280;
  border-bottom: 1px solid #e5e7eb;
}

.demandes-table td {
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.demandes-table tbody tr {
  cursor: pointer;
  transition: background 0.2s;
}

.demandes-table tbody tr:hover {
  background: #f9fafb;
}

.numero {
  font-family: monospace;
  font-weight: 600;
}

.categorie {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.cat-parent {
  color: #6b7280;
  font-weight: 500;
}

.cat-separator {
  color: #9ca3af;
  margin: 0 0.1rem;
}

.description {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #4b5563;
}

.date {
  color: #6b7280;
  font-size: 0.9rem;
}

.agent {
  color: #6b7280;
}

/* Status badges */
.statut-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-nouveau { background: #dbeafe; color: #1d4ed8; }
.status-moderation { background: #fef3c7; color: #b45309; }
.status-envoye { background: #e0f2fe; color: #0369a1; }
.status-accepte { background: #dcfce7; color: #15803d; }
.status-encours { background: #ede9fe; color: #7c3aed; }
.status-planifie { background: #e0e7ff; color: #4338ca; }
.status-traite { background: #d1fae5; color: #047857; }
.status-rejete { background: #fee2e2; color: #dc2626; }
.status-cloture { background: #f3f4f6; color: #6b7280; }

/* Priority badges */
.priorite-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.priority-urgente { background: #fee2e2; color: #dc2626; }
.priority-haute { background: #ffedd5; color: #c2410c; }
.priority-normale { background: #f3f4f6; color: #6b7280; }
.priority-basse { background: #f0fdf4; color: #166534; }

/* Loading & Empty */
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

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #9ca3af;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.pagination button {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination button:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #3b82f6;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #6b7280;
  font-size: 0.9rem;
}

/* Messages badge */
.th-messages {
  width: 50px;
  text-align: center;
}

.messages-cell {
  text-align: center;
}

.messages-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  background: #3b82f6;
  color: white;
  border-radius: 11px;
  font-size: 0.75rem;
  font-weight: 600;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

/* Priorité dropdown */
.priorite-cell {
  position: relative;
}

.priorite-dropdown-wrapper {
  position: relative;
  display: inline-block;
}

.priorite-clickable {
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.priorite-clickable:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.priorite-clickable:disabled {
  cursor: wait;
  opacity: 0.7;
}

.priorite-dropdown {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 4px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  min-width: 120px;
  overflow: hidden;
}

.priorite-dropdown .dropdown-item {
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  transition: background 0.2s;
}

.priorite-dropdown .dropdown-item:hover {
  filter: brightness(0.95);
}

.priorite-dropdown .dropdown-item.active {
  font-weight: 700;
}

.priorite-dropdown .dropdown-item.active::before {
  content: '✓ ';
}

.mini-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

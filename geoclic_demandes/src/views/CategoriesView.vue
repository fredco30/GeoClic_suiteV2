<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import HelpButton from '@/components/help/HelpButton.vue'

// Types
interface ChampConfig {
  nom: string
  label: string
  type: 'text' | 'textarea' | 'number' | 'select' | 'checkbox' | 'date'
  requis: boolean
  options?: string[]
  placeholder?: string
  ordre: number
}

interface Category {
  id: string
  project_id: string
  parent_id: string | null
  nom: string
  description?: string
  icone: string
  couleur: number
  actif: boolean
  ordre_affichage: number
  moderation_requise: boolean
  service_defaut_id?: string
  delai_traitement_jours: number
  photo_obligatoire: boolean
  photo_max_count: number
  champs_config: ChampConfig[]
  created_at: string
  updated_at: string
  children?: Category[]
}

interface Project {
  id: string
  name: string
  description?: string
  collectivite_name?: string
}

interface Service {
  id: string
  project_id: string
  nom: string
  code?: string
  couleur: string
  actif: boolean
}

// State
const categories = ref<Category[]>([])
const projects = ref<Project[]>([])
const services = ref<Service[]>([])
const loading = ref(true)
const showModal = ref(false)
const editingCategory = ref<Category | null>(null)
const expandedCategories = ref<Set<string>>(new Set())
const currentProjectId = ref<string | null>(null)

// Form
const form = ref({
  nom: '',
  description: '',
  icone: 'report_problem',
  couleur: '#3b82f6',
  actif: true,
  parent_id: null as string | null,
  ordre_affichage: 0,
  moderation_requise: true,
  delai_traitement_jours: 7,
  photo_obligatoire: false,
  photo_max_count: 3,
  champs_config: [] as ChampConfig[],
  service_defaut_id: null as string | null
})

// Icones disponibles (Material Icons names) - organisées par thème
const icones = [
  // Signalement / Alertes
  { name: 'report_problem', emoji: '⚠️', label: 'Signalement' },
  { name: 'warning', emoji: '🚧', label: 'Danger' },
  { name: 'error', emoji: '❌', label: 'Erreur' },
  { name: 'info', emoji: 'ℹ️', label: 'Information' },
  { name: 'help', emoji: '❓', label: 'Aide' },

  // Voirie / Routes
  { name: 'directions_car', emoji: '🚗', label: 'Voiture' },
  { name: 'route', emoji: '🛣️', label: 'Route' },
  { name: 'traffic', emoji: '🚦', label: 'Feu tricolore' },
  { name: 'local_parking', emoji: '🅿️', label: 'Parking' },
  { name: 'directions_bike', emoji: '🚲', label: 'Vélo' },
  { name: 'directions_walk', emoji: '🚶', label: 'Piéton' },
  { name: 'directions_bus', emoji: '🚌', label: 'Bus' },

  // Travaux / Construction
  { name: 'construction', emoji: '🔧', label: 'Travaux' },
  { name: 'engineering', emoji: '👷', label: 'Chantier' },
  { name: 'handyman', emoji: '🛠️', label: 'Réparation' },
  { name: 'build', emoji: '🔨', label: 'Construction' },

  // Éclairage
  { name: 'lightbulb', emoji: '💡', label: 'Ampoule' },
  { name: 'wb_incandescent', emoji: '🔆', label: 'Éclairage' },
  { name: 'highlight', emoji: '✨', label: 'Lumière' },

  // Propreté / Déchets
  { name: 'delete', emoji: '🗑️', label: 'Poubelle' },
  { name: 'recycling', emoji: '♻️', label: 'Recyclage' },
  { name: 'local_shipping', emoji: '🚛', label: 'Camion' },
  { name: 'cleaning_services', emoji: '🧹', label: 'Nettoyage' },

  // Espaces verts / Nature
  { name: 'park', emoji: '🌳', label: 'Arbre' },
  { name: 'nature', emoji: '🌿', label: 'Nature' },
  { name: 'eco', emoji: '🌱', label: 'Écologie' },
  { name: 'grass', emoji: '🌾', label: 'Herbe' },
  { name: 'yard', emoji: '🏡', label: 'Jardin' },
  { name: 'forest', emoji: '🌲', label: 'Forêt' },

  // Eau
  { name: 'water_drop', emoji: '💧', label: 'Eau' },
  { name: 'waves', emoji: '🌊', label: 'Vagues' },
  { name: 'pool', emoji: '🏊', label: 'Piscine' },
  { name: 'opacity', emoji: '💦', label: 'Goutte' },

  // Bâtiments
  { name: 'home', emoji: '🏠', label: 'Maison' },
  { name: 'apartment', emoji: '🏢', label: 'Immeuble' },
  { name: 'business', emoji: '🏛️', label: 'Bâtiment' },
  { name: 'school', emoji: '🏫', label: 'École' },
  { name: 'local_hospital', emoji: '🏥', label: 'Hôpital' },
  { name: 'church', emoji: '⛪', label: 'Église' },
  { name: 'store', emoji: '🏪', label: 'Commerce' },

  // Sport / Loisirs
  { name: 'sports_soccer', emoji: '⚽', label: 'Football' },
  { name: 'sports_basketball', emoji: '🏀', label: 'Basketball' },
  { name: 'sports_tennis', emoji: '🎾', label: 'Tennis' },
  { name: 'fitness_center', emoji: '🏋️', label: 'Sport' },
  { name: 'theater_comedy', emoji: '🎭', label: 'Culture' },
  { name: 'attractions', emoji: '🎢', label: 'Attraction' },
  { name: 'beach_access', emoji: '🏖️', label: 'Plage' },

  // Mobilier urbain
  { name: 'chair', emoji: '🪑', label: 'Banc' },
  { name: 'deck', emoji: '🛝', label: 'Jeux' },
  { name: 'fence', emoji: '🚧', label: 'Clôture' },

  // Animaux
  { name: 'pets', emoji: '🐕', label: 'Chien' },
  { name: 'bug_report', emoji: '🐛', label: 'Insecte' },

  // Sécurité
  { name: 'security', emoji: '🛡️', label: 'Sécurité' },
  { name: 'local_police', emoji: '👮', label: 'Police' },
  { name: 'fire_extinguisher', emoji: '🧯', label: 'Incendie' },
  { name: 'videocam', emoji: '📹', label: 'Caméra' },

  // Communication / Bruit
  { name: 'volume_up', emoji: '🔊', label: 'Bruit' },
  { name: 'campaign', emoji: '📢', label: 'Annonce' },
  { name: 'phone', emoji: '📞', label: 'Téléphone' },
  { name: 'email', emoji: '📧', label: 'Email' },

  // Divers
  { name: 'accessibility', emoji: '♿', label: 'Accessibilité' },
  { name: 'elderly', emoji: '👴', label: 'Seniors' },
  { name: 'child_care', emoji: '👶', label: 'Enfants' },
  { name: 'local_cafe', emoji: '☕', label: 'Café' },
  { name: 'restaurant', emoji: '🍽️', label: 'Restaurant' },
  { name: 'shopping_cart', emoji: '🛒', label: 'Courses' },
  { name: 'wifi', emoji: '📶', label: 'WiFi' },
  { name: 'ev_station', emoji: '🔌', label: 'Borne électrique' },
  { name: 'local_gas_station', emoji: '⛽', label: 'Station' },
]

// Couleurs prédéfinies
const couleurs = [
  '#3b82f6', // Bleu
  '#10b981', // Vert
  '#f59e0b', // Orange
  '#ef4444', // Rouge
  '#8b5cf6', // Violet
  '#ec4899', // Rose
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#f97316', // Orange foncé
  '#6366f1', // Indigo
]

// Computed
const categoriesTree = computed(() => {
  const rootCats = categories.value.filter(c => !c.parent_id)
  return rootCats.map(cat => ({
    ...cat,
    children: categories.value.filter(c => c.parent_id === cat.id)
  }))
})

const parentCategories = computed(() => {
  return categories.value.filter(c => !c.parent_id)
})

const statsTotal = computed(() => categories.value.length)
const statsActives = computed(() => categories.value.filter(c => c.actif).length)
const statsParents = computed(() => categories.value.filter(c => !c.parent_id).length)

const currentProject = computed(() => {
  return projects.value.find(p => p.id === currentProjectId.value)
})

// Helpers
function intToHex(color: number): string {
  return '#' + (color & 0xFFFFFF).toString(16).padStart(6, '0')
}

function hexToInt(hex: string): number {
  return parseInt(hex.replace('#', ''), 16) | 0xFF000000
}

function getIconEmoji(iconName: string): string {
  const icon = icones.find(i => i.name === iconName)
  return icon?.emoji || '📌'
}

function getServiceName(serviceId: string | undefined): string | null {
  if (!serviceId) return null
  const service = services.value.find(s => s.id === serviceId)
  return service ? (service.code ? `[${service.code}] ${service.nom}` : service.nom) : null
}

// API calls
async function loadProjects() {
  try {
    // Charger les projets incluant le projet système pour Demandes
    const response = await axios.get('/api/sig/projects', {
      params: { include_system: true }
    })
    projects.value = response.data?.projects || []

    // Auto-sélectionner le projet système
    const systemProject = projects.value.find((p: Project & { is_system?: boolean }) => p.is_system)
    if (systemProject) {
      currentProjectId.value = systemProject.id
    }
  } catch (error) {
    console.error('Erreur chargement projets:', error)
    projects.value = []
  }
}

async function loadServices(projectId: string) {
  if (!projectId) return
  try {
    const response = await axios.get('/api/demandes/services', {
      params: { project_id: projectId, actif_only: false }
    })
    services.value = response.data || []
  } catch (error) {
    console.error('Erreur chargement services:', error)
    services.value = []
  }
}

// Computed - services du projet courant
const projectServices = computed(() => {
  if (!currentProjectId.value) return []
  return services.value.filter(s => s.project_id === currentProjectId.value && s.actif)
})

async function loadCategories() {
  loading.value = true
  try {
    // Charger les projets disponibles (sélectionne automatiquement le projet système)
    await loadProjects()

    // Charger les catégories pour le projet sélectionné
    if (currentProjectId.value) {
      const response = await axios.get('/api/demandes/categories', {
        params: { actif_only: false, project_id: currentProjectId.value }
      })
      categories.value = response.data

      // Charger les services
      await loadServices(currentProjectId.value)
    } else {
      categories.value = []
    }
  } catch (error) {
    console.error('Erreur chargement catégories:', error)
  } finally {
    loading.value = false
  }
}

// Modal handlers
function openCreateParent() {
  editingCategory.value = null
  form.value = {
    nom: '',
    description: '',
    icone: 'report_problem',
    couleur: '#3b82f6',
    actif: true,
    parent_id: null,
    ordre_affichage: categories.value.filter(c => !c.parent_id).length,
    moderation_requise: true,
    delai_traitement_jours: 7,
    photo_obligatoire: false,
    photo_max_count: 3,
    champs_config: [],
    service_defaut_id: null
  }
  showModal.value = true
}

function openCreateChild(parentId: string) {
  editingCategory.value = null
  const parent = categories.value.find(c => c.id === parentId)
  const childCount = categories.value.filter(c => c.parent_id === parentId).length

  form.value = {
    nom: '',
    description: '',
    icone: parent?.icone || 'report_problem',
    couleur: intToHex(parent?.couleur || hexToInt('#3b82f6')),
    actif: true,
    parent_id: parentId,
    ordre_affichage: childCount,
    moderation_requise: true,
    delai_traitement_jours: 7,
    photo_obligatoire: false,
    photo_max_count: 3,
    champs_config: [],
    service_defaut_id: null
  }
  showModal.value = true
}

function openEdit(cat: Category) {
  editingCategory.value = cat
  form.value = {
    nom: cat.nom,
    description: cat.description || '',
    icone: cat.icone || 'report_problem',
    couleur: intToHex(cat.couleur),
    actif: cat.actif,
    parent_id: cat.parent_id,
    ordre_affichage: cat.ordre_affichage,
    moderation_requise: cat.moderation_requise,
    delai_traitement_jours: cat.delai_traitement_jours,
    photo_obligatoire: cat.photo_obligatoire,
    photo_max_count: cat.photo_max_count,
    champs_config: cat.champs_config || [],
    service_defaut_id: cat.service_defaut_id || null
  }
  showModal.value = true
}

async function saveCategory() {
  try {
    // Préparer TOUTES les données attendues par l'API
    const data = {
      nom: form.value.nom,
      description: form.value.description || null,
      icone: form.value.icone || 'report_problem',
      couleur: hexToInt(form.value.couleur),
      actif: form.value.actif ?? true,
      parent_id: form.value.parent_id || null,
      ordre_affichage: form.value.ordre_affichage ?? 0,
      moderation_requise: form.value.moderation_requise ?? false,
      delai_traitement_jours: form.value.delai_traitement_jours ?? 7,
      photo_obligatoire: form.value.photo_obligatoire ?? false,
      photo_max_count: form.value.photo_max_count ?? 3,
      champs_config: form.value.champs_config || [],
      service_defaut_id: form.value.service_defaut_id || null
    }

    if (editingCategory.value) {
      await axios.put(`/api/demandes/categories/${editingCategory.value.id}`, data)
    } else {
      // Vérifier qu'on a un project_id
      if (!currentProjectId.value) {
        alert('Erreur: Aucun projet configuré. Contactez l\'administrateur.')
        return
      }
      await axios.post('/api/demandes/categories', data, {
        params: { project_id: currentProjectId.value }
      })
    }
    showModal.value = false
    await loadCategories()
  } catch (error: any) {
    console.error('Erreur sauvegarde:', error)
    const detail = error.response?.data?.detail || 'Erreur lors de la sauvegarde'
    alert(detail)
  }
}

async function toggleActif(cat: Category) {
  try {
    await axios.put(`/api/demandes/categories/${cat.id}`, {
      actif: !cat.actif
    })
    await loadCategories()
  } catch (error) {
    console.error('Erreur toggle:', error)
  }
}

async function deleteCategory(cat: Category) {
  const childCount = categories.value.filter(c => c.parent_id === cat.id).length

  if (childCount > 0) {
    alert(`Cette catégorie a ${childCount} sous-catégorie(s). Supprimez-les d'abord.`)
    return
  }

  if (!confirm(`Supprimer la catégorie "${cat.nom}" ?`)) return

  try {
    await axios.delete(`/api/demandes/categories/${cat.id}`)
    await loadCategories()
  } catch (error: any) {
    if (error.response?.status === 400) {
      alert(error.response.data.detail || 'Impossible de supprimer cette catégorie.')
    } else {
      console.error('Erreur suppression:', error)
    }
  }
}

function toggleExpand(catId: string) {
  if (expandedCategories.value.has(catId)) {
    expandedCategories.value.delete(catId)
  } else {
    expandedCategories.value.add(catId)
  }
}

// Init
onMounted(async () => {
  await loadCategories()
  // Expand all by default
  categories.value.filter(c => !c.parent_id).forEach(c => {
    expandedCategories.value.add(c.id)
  })
})
</script>

<template>
  <div class="categories-view">
    <!-- Header -->
    <header class="page-header">
      <div class="page-header-main">
        <h1>Catégories de signalements <HelpButton page-key="categories" size="sm" /></h1>
        <p>Organisez les types de signalements en catégories et sous-catégories</p>
      </div>
      <div class="page-header-actions">
        <button class="btn btn-primary" @click="openCreateParent" :disabled="!currentProjectId">
          + Nouvelle catégorie
        </button>
      </div>
    </header>

    <!-- Message si aucun projet système configuré -->
    <div v-if="projects.length === 0" class="project-selector">
      <div class="no-project-warning">
        <span class="warning-icon">⚠️</span>
        <div>
          <strong>Aucun projet configuré</strong>
          <p>Le projet système pour les signalements n'existe pas encore. Contactez l'administrateur.</p>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-value">{{ statsTotal }}</span>
        <span class="stat-label">Total</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ statsParents }}</span>
        <span class="stat-label">Catégories</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ statsTotal - statsParents }}</span>
        <span class="stat-label">Sous-catégories</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ statsActives }}</span>
        <span class="stat-label">Actives</span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <!-- Categories Tree -->
    <div v-else class="categories-container">
      <div v-if="categoriesTree.length === 0" class="empty-state">
        <div class="empty-icon">📂</div>
        <h3>Aucune catégorie</h3>
        <p>Créez votre première catégorie de signalement</p>
        <button class="btn btn-primary" @click="openCreateParent">
          + Créer une catégorie
        </button>
      </div>

      <div v-else class="categories-tree">
        <!-- Parent Categories -->
        <div
          v-for="parent in categoriesTree"
          :key="parent.id"
          class="category-group"
        >
          <!-- Parent Card -->
          <div
            class="category-card parent-card"
            :class="{ inactive: !parent.actif }"
          >
            <div class="card-left" @click="toggleExpand(parent.id)">
              <span
                class="category-icon"
                :style="{ backgroundColor: intToHex(parent.couleur) }"
              >
                {{ getIconEmoji(parent.icone) }}
              </span>
              <div class="category-info">
                <h3>{{ parent.nom }}</h3>
                <p v-if="parent.description">{{ parent.description }}</p>
                <div class="category-meta">
                  <span class="badge" :class="{ active: parent.actif }">
                    {{ parent.actif ? 'Actif' : 'Inactif' }}
                  </span>
                  <span class="meta-item" v-if="parent.children?.length">
                    {{ parent.children.length }} sous-catégorie(s)
                  </span>
                </div>
              </div>
            </div>

            <div class="card-actions">
              <button
                class="action-btn expand-btn"
                @click="toggleExpand(parent.id)"
                v-if="parent.children?.length"
              >
                {{ expandedCategories.has(parent.id) ? '▼' : '▶' }}
              </button>
              <button class="action-btn" @click="openCreateChild(parent.id)" title="Ajouter sous-catégorie">
                +
              </button>
              <button class="action-btn" @click="openEdit(parent)" title="Modifier">
                ✏️
              </button>
              <button
                class="action-btn"
                @click="toggleActif(parent)"
                :title="parent.actif ? 'Désactiver' : 'Activer'"
              >
                {{ parent.actif ? '🚫' : '✓' }}
              </button>
              <button
                class="action-btn delete"
                @click="deleteCategory(parent)"
                title="Supprimer"
              >
                🗑️
              </button>
            </div>
          </div>

          <!-- Children Cards -->
          <div
            v-if="expandedCategories.has(parent.id) && parent.children?.length"
            class="children-container"
          >
            <div
              v-for="child in parent.children"
              :key="child.id"
              class="category-card child-card"
              :class="{ inactive: !child.actif }"
            >
              <div class="card-left">
                <span
                  class="category-icon small"
                  :style="{ backgroundColor: intToHex(child.couleur) }"
                >
                  {{ getIconEmoji(child.icone) }}
                </span>
                <div class="category-info">
                  <h4>{{ child.nom }}</h4>
                  <p v-if="child.description">{{ child.description }}</p>
                  <div class="category-meta">
                    <span class="badge" :class="{ active: child.actif }">
                      {{ child.actif ? 'Actif' : 'Inactif' }}
                    </span>
                    <span class="meta-item">
                      Délai: {{ child.delai_traitement_jours }}j
                    </span>
                    <span class="meta-item" v-if="child.moderation_requise">
                      Modération
                    </span>
                    <span class="meta-item service-tag" v-if="getServiceName(child.service_defaut_id)">
                      🏢 {{ getServiceName(child.service_defaut_id) }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="card-actions">
                <button class="action-btn" @click="openEdit(child)" title="Modifier">
                  ✏️
                </button>
                <button
                  class="action-btn"
                  @click="toggleActif(child)"
                  :title="child.actif ? 'Désactiver' : 'Activer'"
                >
                  {{ child.actif ? '🚫' : '✓' }}
                </button>
                <button
                  class="action-btn delete"
                  @click="deleteCategory(child)"
                  title="Supprimer"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingCategory ? 'Modifier' : 'Nouvelle' }} {{ form.parent_id ? 'sous-catégorie' : 'catégorie' }}</h3>
          <button class="close-btn" @click="showModal = false">&times;</button>
        </div>

        <div class="modal-body">
          <!-- Parent selector (for subcategories) -->
          <div v-if="form.parent_id || (!editingCategory && parentCategories.length)" class="form-group">
            <label>Catégorie parente</label>
            <select v-model="form.parent_id" class="form-select">
              <option :value="null">-- Catégorie principale --</option>
              <option v-for="cat in parentCategories" :key="cat.id" :value="cat.id">
                {{ getIconEmoji(cat.icone) }} {{ cat.nom }}
              </option>
            </select>
          </div>

          <!-- Nom -->
          <div class="form-group">
            <label>Nom *</label>
            <input v-model="form.nom" type="text" required placeholder="Ex: Voirie, Éclairage public..." />
          </div>

          <!-- Description -->
          <div class="form-group">
            <label>Description <small class="char-count">({{ form.description?.length || 0 }}/100)</small></label>
            <textarea v-model="form.description" rows="2" maxlength="100" placeholder="Description courte pour les citoyens (max 100 caractères)"></textarea>
          </div>

          <!-- Icône et Couleur -->
          <div class="form-row">
            <div class="form-group flex-2">
              <label>Icône</label>
              <div class="icon-picker">
                <button
                  v-for="icon in icones"
                  :key="icon.name"
                  type="button"
                  class="icon-option"
                  :class="{ selected: form.icone === icon.name }"
                  @click="form.icone = icon.name"
                  :title="icon.label"
                >
                  {{ icon.emoji }}
                </button>
              </div>
            </div>

            <div class="form-group">
              <label>Couleur</label>
              <div class="color-picker">
                <button
                  v-for="color in couleurs"
                  :key="color"
                  type="button"
                  class="color-option"
                  :class="{ selected: form.couleur === color }"
                  :style="{ backgroundColor: color }"
                  @click="form.couleur = color"
                ></button>
              </div>
            </div>
          </div>

          <!-- Options SLA (pour sous-catégories) -->
          <div v-if="form.parent_id" class="form-section">
            <h4>Options de traitement</h4>

            <div class="form-row">
              <div class="form-group">
                <label>Délai de traitement (jours)</label>
                <input v-model.number="form.delai_traitement_jours" type="number" min="1" max="365" />
              </div>

              <div class="form-group">
                <label>Photos maximum</label>
                <input v-model.number="form.photo_max_count" type="number" min="0" max="10" />
              </div>
            </div>

            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input v-model="form.moderation_requise" type="checkbox" />
                Modération requise
              </label>
              <label class="checkbox-label">
                <input v-model="form.photo_obligatoire" type="checkbox" />
                Photo obligatoire
              </label>
            </div>

            <!-- Service par défaut -->
            <div class="form-group" style="margin-top: 1rem;">
              <label>Service par défaut</label>
              <select v-model="form.service_defaut_id" class="form-select">
                <option :value="null">-- Aucun service --</option>
                <option v-for="service in projectServices" :key="service.id" :value="service.id">
                  <span v-if="service.code">[{{ service.code }}]</span> {{ service.nom }}
                </option>
              </select>
              <small class="form-hint">Les nouvelles demandes de cette catégorie seront automatiquement affectées à ce service.</small>
            </div>
          </div>

          <!-- Actif -->
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="form.actif" type="checkbox" />
              Catégorie active (visible par les citoyens)
            </label>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showModal = false">
            Annuler
          </button>
          <button
            class="btn btn-primary"
            @click="saveCategory"
            :disabled="!form.nom"
          >
            {{ editingCategory ? 'Enregistrer' : 'Créer' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.categories-view {
  padding: 1.5rem;
  max-width: 1000px;
  margin: 0 auto;
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  font-size: 1.75rem;
  margin: 0 0 0.25rem;
  color: #1f2937;
}

.page-header-main p {
  color: #6b7280;
  margin: 0;
}

.page-header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* Project selector */
.project-selector {
  margin-bottom: 1.5rem;
}

.no-project-warning {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 10px;
  color: #92400e;
}

.no-project-warning .warning-icon {
  font-size: 1.5rem;
}

.no-project-warning strong {
  display: block;
  margin-bottom: 0.25rem;
}

.no-project-warning p {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
}

.no-project-warning a {
  color: #d97706;
  font-weight: 500;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

.project-select-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.project-select-row label {
  font-weight: 500;
  color: #374151;
}

.project-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.95rem;
  min-width: 200px;
}

.project-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.project-info {
  font-size: 0.85rem;
  color: #6b7280;
}

/* Stats */
.stats-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-value {
  display: block;
  font-size: 1.75rem;
  font-weight: 700;
  color: #3b82f6;
}

.stat-label {
  font-size: 0.85rem;
  color: #6b7280;
}

/* Buttons */
.btn {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  border: 1px solid #d1d5db;
  color: #374151;
}

.btn-secondary:hover {
  background: #f9fafb;
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

/* Empty state */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 0.5rem;
  color: #374151;
}

.empty-state p {
  color: #6b7280;
  margin: 0 0 1.5rem;
}

/* Categories Tree */
.categories-container {
  background: #f9fafb;
  border-radius: 12px;
  padding: 1.5rem;
}

.categories-tree {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.category-group {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.category-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  transition: background 0.2s;
}

.category-card:hover {
  background: #f9fafb;
}

.category-card.inactive {
  opacity: 0.6;
}

.parent-card {
  border-bottom: 1px solid #f3f4f6;
}

.children-container {
  background: #f9fafb;
  padding: 0.5rem 0.5rem 0.5rem 2rem;
}

.child-card {
  background: white;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.child-card:last-child {
  margin-bottom: 0;
}

.card-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  flex: 1;
}

.category-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.category-icon.small {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  font-size: 1.25rem;
}

.category-info h3, .category-info h4 {
  margin: 0 0 0.25rem;
  color: #1f2937;
}

.category-info h3 {
  font-size: 1.1rem;
}

.category-info h4 {
  font-size: 1rem;
  font-weight: 500;
}

.category-info p {
  margin: 0 0 0.5rem;
  color: #6b7280;
  font-size: 0.9rem;
}

.category-meta {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.badge {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  background: #f3f4f6;
  color: #6b7280;
}

.badge.active {
  background: #dcfce7;
  color: #15803d;
}

.meta-item {
  font-size: 0.8rem;
  color: #9ca3af;
}

.meta-item.service-tag {
  background: #dbeafe;
  color: #1d4ed8;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

.action-btn:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.action-btn.delete:hover {
  border-color: #ef4444;
  background: #fef2f2;
}

.expand-btn {
  font-size: 0.75rem;
  color: #9ca3af;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  margin: 1rem;
}

.modal.modal-sm {
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #f3f4f6;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  border-radius: 8px;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  line-height: 1;
}

.close-btn:hover {
  background: #e5e7eb;
}

.modal-body {
  padding: 1.5rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #f3f4f6;
  background: #f9fafb;
}

/* Form */
.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
}

.form-group label .char-count {
  font-weight: 400;
  color: #9ca3af;
  font-size: 0.85rem;
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group textarea,
.form-group .form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group .form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-row .form-group {
  flex: 1;
}

.form-row .form-group.flex-2 {
  flex: 2;
}

.form-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #f3f4f6;
}

.form-section h4 {
  margin: 0 0 1rem;
  font-size: 1rem;
  color: #374151;
}

.checkboxes {
  flex-wrap: wrap;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: normal !important;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.form-hint {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: #6b7280;
}

/* Icon picker */
.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.icon-option {
  width: 44px;
  height: 44px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: white;
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-option:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.icon-option.selected {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

/* Color picker */
.color-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.color-option {
  width: 36px;
  height: 36px;
  border: 3px solid white;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 0 0 1px #e5e7eb;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.selected {
  box-shadow: 0 0 0 3px #3b82f6;
}

/* Responsive */
@media (max-width: 640px) {
  .page-header {
    flex-direction: column;
    gap: 1rem;
  }

  .stats-row {
    flex-wrap: wrap;
  }

  .stat-card {
    min-width: calc(50% - 0.5rem);
  }

  .form-row {
    flex-direction: column;
  }

  .category-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>

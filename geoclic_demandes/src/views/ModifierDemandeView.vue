<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import FileDropZone from '@/components/FileDropZone.vue'
import MapPickerBackoffice from '@/components/MapPickerBackoffice.vue'
import type { UploadedFile } from '@/components/FileDropZone.vue'

const route = useRoute()
const router = useRouter()
const demandeId = route.params.id as string

const form = ref({
  categorie_id: '',
  description: '',
  declarant_nom: '',
  declarant_email: '',
  declarant_telephone: '',
  source: 'backoffice' as string,
  priorite: 'normale' as string,
  adresse_approximative: '',
})

const coords = ref<{ lat: number; lng: number } | null>(null)
const uploadedFiles = ref<UploadedFile[]>([])
const initialFiles = ref<UploadedFile[]>([])
const initialLat = ref<number | undefined>(undefined)
const initialLng = ref<number | undefined>(undefined)
const initialAddress = ref<string | undefined>(undefined)
const loading = ref(false)
const loadingData = ref(true)
const error = ref('')
const success = ref(false)
const numeroSuivi = ref('')
const showConfirmDialog = ref(false)

interface Category {
  id: string
  nom: string
  parent_id: string | null
  icone: string
  couleur: number
  actif: boolean
}

const categories = ref<Category[]>([])
const projectId = ref<string>('')

const categoriesTree = computed(() => {
  const rootCats = categories.value.filter(c => !c.parent_id && c.actif)
  return rootCats.map(cat => ({
    ...cat,
    children: categories.value.filter(c => c.parent_id === cat.id && c.actif)
  }))
})

const sources = [
  { value: 'backoffice', label: 'Saisie backoffice' },
  { value: 'telephone', label: 'Appel téléphonique' },
  { value: 'email', label: 'Email reçu' },
  { value: 'app_citoyen', label: 'App citoyen' },
  { value: 'web', label: 'Portail web' },
]

const priorites = [
  { value: 'basse', label: 'Basse' },
  { value: 'normale', label: 'Normale' },
  { value: 'haute', label: 'Haute' },
  { value: 'urgente', label: 'Urgente' },
]

const isValid = computed(() => {
  return form.value.categorie_id && form.value.description.length >= 3
})

onMounted(async () => {
  await loadProjectAndCategories()
  await loadDemande()
})

async function loadProjectAndCategories() {
  try {
    const projectsRes = await axios.get('/api/sig/projects', {
      params: { include_system: true }
    })
    const projects = projectsRes.data?.projects || []
    const systemProject = projects.find((p: any) => p.is_system)
    if (systemProject) {
      projectId.value = systemProject.id
    } else if (projects.length > 0) {
      projectId.value = projects[0].id
    }

    if (projectId.value) {
      const catRes = await axios.get('/api/demandes/categories', {
        params: { project_id: projectId.value, actif_only: true }
      })
      categories.value = catRes.data || []
    }
  } catch {
    error.value = 'Erreur lors du chargement des catégories'
  }
}

async function loadDemande() {
  loadingData.value = true
  try {
    const res = await axios.get(`/api/demandes/${demandeId}`)
    const d = res.data

    form.value.categorie_id = d.categorie_id || ''
    form.value.description = d.description || ''
    form.value.declarant_nom = d.declarant_nom || ''
    form.value.declarant_email = d.declarant_email || ''
    form.value.declarant_telephone = d.declarant_telephone || ''
    form.value.source = d.source || 'backoffice'
    form.value.priorite = d.priorite || 'normale'
    form.value.adresse_approximative = d.adresse_approximative || ''
    numeroSuivi.value = d.numero_suivi || ''

    // Coordonnées
    if (d.latitude && d.longitude) {
      coords.value = { lat: d.latitude, lng: d.longitude }
      initialLat.value = d.latitude
      initialLng.value = d.longitude
      initialAddress.value = d.adresse_approximative || ''
    }

    // Fichiers existants
    const existingFiles: UploadedFile[] = []
    const IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    if (d.photos && Array.isArray(d.photos)) {
      for (const url of d.photos) {
        const u = typeof url === 'string' ? url : url.url
        if (u) {
          existingFiles.push({
            url: u,
            type: 'image',
            originalName: u.split('/').pop() || 'photo',
            sizeBytes: 0,
          })
        }
      }
    }
    if (d.documents && Array.isArray(d.documents)) {
      for (const url of d.documents) {
        existingFiles.push({
          url,
          type: 'document',
          originalName: url.split('/').pop() || 'document',
          sizeBytes: 0,
        })
      }
    }
    initialFiles.value = existingFiles
    uploadedFiles.value = existingFiles
  } catch {
    error.value = 'Erreur lors du chargement de la demande'
  }
  loadingData.value = false
}

function onLocationSelect(location: { lat: number; lng: number; address: string }) {
  coords.value = { lat: location.lat, lng: location.lng }
  form.value.adresse_approximative = location.address
}

function onFilesUpdate(files: UploadedFile[]) {
  uploadedFiles.value = files
}

function confirmSubmit() {
  if (!isValid.value) return
  showConfirmDialog.value = true
}

async function submitUpdate() {
  showConfirmDialog.value = false
  if (!isValid.value) return

  loading.value = true
  error.value = ''

  try {
    const photos = uploadedFiles.value.filter(f => f.type === 'image').map(f => f.url)
    const documents = uploadedFiles.value.filter(f => f.type === 'document').map(f => f.url)

    const payload: any = {
      categorie_id: form.value.categorie_id,
      description: form.value.description,
      source: form.value.source,
      priorite: form.value.priorite,
      photos,
      documents,
      declarant_nom: form.value.declarant_nom || null,
      declarant_email: form.value.declarant_email || null,
      declarant_telephone: form.value.declarant_telephone || null,
      adresse_approximative: form.value.adresse_approximative || null,
    }

    if (coords.value) {
      payload.coordonnees = {
        latitude: coords.value.lat,
        longitude: coords.value.lng,
      }
    }

    await axios.put(`/api/demandes/backoffice/${demandeId}`, payload)
    success.value = true
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Erreur lors de la modification'
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push(`/demandes/${demandeId}`)
}
</script>

<template>
  <div class="modifier-demande">
    <header class="page-header">
      <div class="page-header-main">
        <button @click="goBack" class="back-link">&larr; Retour au détail</button>
        <h1>Modifier la demande <span v-if="numeroSuivi" class="numero">{{ numeroSuivi }}</span></h1>
      </div>
    </header>

    <!-- Chargement -->
    <div v-if="loadingData" class="loading-card">
      Chargement de la demande...
    </div>

    <!-- Succès -->
    <div v-else-if="success" class="success-card">
      <div class="success-icon">&#10003;</div>
      <h2>Demande modifiée avec succès</h2>
      <div class="success-actions">
        <button @click="goBack" class="btn btn-primary">Retour au détail</button>
      </div>
    </div>

    <!-- Formulaire -->
    <div v-else class="form-container">
      <div class="form-grid">
        <!-- Colonne gauche -->
        <div class="form-column">
          <div class="form-section">
            <h3 class="section-title">Catégorie <span class="required">*</span></h3>
            <select v-model="form.categorie_id" class="form-select" required>
              <option value="">-- Sélectionner une catégorie --</option>
              <template v-for="parent in categoriesTree" :key="parent.id">
                <option v-if="!parent.children?.length" :value="parent.id">
                  {{ parent.nom }}
                </option>
                <optgroup v-else :label="parent.nom">
                  <option :value="parent.id">{{ parent.nom }} (général)</option>
                  <option v-for="child in parent.children" :key="child.id" :value="child.id">
                    {{ child.nom }}
                  </option>
                </optgroup>
              </template>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Source</label>
              <select v-model="form.source" class="form-select">
                <option v-for="s in sources" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Priorité</label>
              <select v-model="form.priorite" class="form-select">
                <option v-for="p in priorites" :key="p.value" :value="p.value">{{ p.label }}</option>
              </select>
            </div>
          </div>

          <div class="form-section">
            <h3 class="section-title">Description <span class="required">*</span></h3>
            <textarea
              v-model="form.description"
              class="form-textarea"
              rows="5"
              placeholder="Décrivez le signalement..."
              required
              minlength="3"
            ></textarea>
            <span class="char-count">{{ form.description.length }} / 5000</span>
          </div>

          <div class="form-section">
            <h3 class="section-title">Déclarant <span class="optional">(optionnel)</span></h3>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Nom</label>
                <input v-model="form.declarant_nom" type="text" class="form-input" placeholder="Nom du déclarant" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Email</label>
                <input v-model="form.declarant_email" type="email" class="form-input" placeholder="email@example.com" />
              </div>
              <div class="form-group">
                <label class="form-label">Téléphone</label>
                <input v-model="form.declarant_telephone" type="tel" class="form-input" placeholder="06 12 34 56 78" />
              </div>
            </div>
          </div>
        </div>

        <!-- Colonne droite -->
        <div class="form-column">
          <div class="form-section">
            <FileDropZone :initial-files="initialFiles" @update="onFilesUpdate" />
          </div>

          <div class="form-section">
            <MapPickerBackoffice
              :initial-lat="initialLat"
              :initial-lng="initialLng"
              :initial-address="initialAddress"
              @select="onLocationSelect"
            />
          </div>

          <div class="form-section" v-if="!coords">
            <label class="form-label">Adresse (saisie manuelle)</label>
            <input
              v-model="form.adresse_approximative"
              type="text"
              class="form-input"
              placeholder="Ex: 12 rue de la Mairie, 34000 Montpellier"
            />
          </div>
        </div>
      </div>

      <div v-if="error" class="form-error">{{ error }}</div>

      <div class="form-actions">
        <button type="button" @click="goBack" class="btn btn-secondary">Annuler</button>
        <button type="button" @click="confirmSubmit" :disabled="!isValid || loading" class="btn btn-primary">
          <span v-if="loading">Modification en cours...</span>
          <span v-else>Enregistrer les modifications</span>
        </button>
      </div>
    </div>

    <!-- Modal de confirmation -->
    <Teleport to="body">
      <div v-if="showConfirmDialog" class="modal-overlay" @click.self="showConfirmDialog = false">
        <div class="modal-confirm">
          <h3>Confirmer la modification</h3>
          <p>Vous êtes sur le point de modifier cette demande. Voulez-vous continuer ?</p>
          <div class="modal-actions">
            <button @click="showConfirmDialog = false" class="btn btn-secondary">Annuler</button>
            <button @click="submitUpdate" class="btn btn-primary">Confirmer</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.modifier-demande {
  padding: 1.5rem;
  max-width: 1200px;
}

.page-header { margin-bottom: 1.5rem; }

.back-link {
  background: none;
  border: none;
  color: #3b82f6;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0;
  margin-bottom: 0.5rem;
  display: inline-block;
}
.back-link:hover { text-decoration: underline; }

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0.25rem 0;
}

.numero {
  color: #6b7280;
  font-weight: 400;
  font-size: 1rem;
}

.loading-card, .success-card {
  background: white;
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.success-icon {
  width: 64px;
  height: 64px;
  background: #059669;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  margin: 0 auto 1rem;
}
.success-card h2 { color: #059669; margin: 0 0 1.5rem 0; }
.success-actions { display: flex; gap: 1rem; justify-content: center; }

.form-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

@media (max-width: 1024px) {
  .form-grid { grid-template-columns: 1fr; }
}

.form-column { display: flex; flex-direction: column; gap: 0.25rem; }
.form-section { margin-bottom: 1rem; }

.section-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.5rem 0;
}

.required { color: #dc2626; }
.optional { font-weight: 400; color: #9ca3af; font-size: 0.85rem; }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.form-group { display: flex; flex-direction: column; }

.form-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: #4b5563;
  margin-bottom: 0.25rem;
}

.form-input, .form-select, .form-textarea {
  padding: 0.625rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
  width: 100%;
  box-sizing: border-box;
  font-family: inherit;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-textarea { resize: vertical; min-height: 80px; }

.char-count {
  font-size: 0.75rem;
  color: #9ca3af;
  text-align: right;
  display: block;
  margin-top: 0.25rem;
}

.form-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary { background: var(--primary-color, #3b82f6); color: white; }
.btn-primary:hover:not(:disabled) { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; }
.btn-secondary:hover { background: #e5e7eb; }

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-confirm {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-confirm h3 { margin: 0 0 0.75rem 0; font-size: 1.15rem; color: #1f2937; }
.modal-confirm p { color: #6b7280; font-size: 0.9rem; margin: 0 0 1.5rem 0; }
.modal-actions { display: flex; gap: 0.75rem; justify-content: flex-end; }
</style>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import HelpButton from '@/components/help/HelpButton.vue'

interface Template {
  id: string
  nom: string
  sujet: string
  contenu: string
  type: 'email' | 'sms'
  declencheur: string
  actif: boolean
}

const templates = ref<Template[]>([])
const loading = ref(true)
const showModal = ref(false)
const editingTemplate = ref<Template | null>(null)

const form = ref({
  nom: '',
  sujet: '',
  contenu: '',
  type: 'email' as 'email' | 'sms',
  declencheur: 'creation',
  actif: true
})

const declencheurs = [
  { value: 'creation', label: 'Création de demande' },
  { value: 'acceptation', label: 'Demande acceptée' },
  { value: 'rejet', label: 'Demande rejetée' },
  { value: 'planification', label: 'Intervention planifiée' },
  { value: 'traitement', label: 'Demande traitée' },
  { value: 'cloture', label: 'Demande clôturée' }
]

const variables = [
  { code: '{{numero_suivi}}', desc: 'Numéro de suivi' },
  { code: '{{categorie}}', desc: 'Catégorie' },
  { code: '{{statut}}', desc: 'Statut actuel' },
  { code: '{{date_creation}}', desc: 'Date de création' },
  { code: '{{date_planification}}', desc: 'Date d\'intervention' },
  { code: '{{declarant_nom}}', desc: 'Nom du déclarant' },
  { code: '{{lien_suivi}}', desc: 'Lien de suivi' }
]

onMounted(async () => {
  await loadTemplates()
})

async function loadTemplates() {
  loading.value = true
  try {
    const response = await axios.get('/api/demandes/templates')
    templates.value = response.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingTemplate.value = null
  form.value = {
    nom: '',
    sujet: '',
    contenu: '',
    type: 'email',
    declencheur: 'creation',
    actif: true
  }
  showModal.value = true
}

function openEdit(template: Template) {
  editingTemplate.value = template
  form.value = {
    nom: template.nom,
    sujet: template.sujet,
    contenu: template.contenu,
    type: template.type,
    declencheur: template.declencheur,
    actif: template.actif
  }
  showModal.value = true
}

async function saveTemplate() {
  try {
    if (editingTemplate.value) {
      await axios.put(`/api/demandes/templates/${editingTemplate.value.id}`, form.value)
    } else {
      await axios.post('/api/demandes/templates', form.value)
    }
    showModal.value = false
    await loadTemplates()
  } catch (error) {
    console.error('Erreur sauvegarde:', error)
  }
}

async function toggleActif(template: Template) {
  try {
    await axios.patch(`/api/demandes/templates/${template.id}`, {
      actif: !template.actif
    })
    template.actif = !template.actif
  } catch (error) {
    console.error('Erreur toggle:', error)
  }
}

async function deleteTemplate(template: Template) {
  if (!confirm(`Supprimer le template "${template.nom}" ?`)) return

  try {
    await axios.delete(`/api/demandes/templates/${template.id}`)
    await loadTemplates()
  } catch (error) {
    console.error('Erreur suppression:', error)
  }
}

function insertVariable(code: string) {
  form.value.contenu += code
}

function getDeclencheurLabel(value: string): string {
  return declencheurs.find(d => d.value === value)?.label || value
}
</script>

<template>
  <div class="templates-view">
    <header class="page-header">
      <div class="page-header-main">
        <h1>Templates de notification <HelpButton page-key="templates" size="sm" /></h1>
        <p>Personnalisez les emails et SMS envoyés aux citoyens</p>
      </div>
      <div class="page-header-actions">
        <button class="btn btn-primary" @click="openCreate">
          + Nouveau template
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <div v-else class="templates-list">
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-card"
        :class="{ inactive: !template.actif }"
      >
        <div class="template-header">
          <div class="template-type" :class="template.type">
            {{ template.type === 'email' ? '&#9993;' : '&#128241;' }}
          </div>
          <div class="template-info">
            <h3>{{ template.nom }}</h3>
            <span class="template-trigger">
              {{ getDeclencheurLabel(template.declencheur) }}
            </span>
          </div>
          <span class="status" :class="{ active: template.actif }">
            {{ template.actif ? 'Actif' : 'Inactif' }}
          </span>
        </div>

        <div class="template-preview">
          <div v-if="template.type === 'email'" class="subject">
            <strong>Sujet:</strong> {{ template.sujet }}
          </div>
          <p>{{ template.contenu.substring(0, 150) }}{{ template.contenu.length > 150 ? '...' : '' }}</p>
        </div>

        <div class="template-actions">
          <button class="action-btn" @click="openEdit(template)" title="Modifier">
            &#9998; Modifier
          </button>
          <button
            class="action-btn"
            @click="toggleActif(template)"
          >
            {{ template.actif ? '&#128683; Désactiver' : '&#10003; Activer' }}
          </button>
          <button
            class="action-btn delete"
            @click="deleteTemplate(template)"
          >
            &#128465; Supprimer
          </button>
        </div>
      </div>

      <div v-if="templates.length === 0" class="empty-state">
        <p>Aucun template configuré</p>
        <button class="btn btn-primary" @click="openCreate">
          Créer un template
        </button>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal modal-large">
        <h3>{{ editingTemplate ? 'Modifier' : 'Nouveau' }} template</h3>

        <div class="modal-content">
          <div class="form-column">
            <div class="form-group">
              <label>Nom du template *</label>
              <input v-model="form.nom" type="text" required />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Type</label>
                <select v-model="form.type">
                  <option value="email">Email</option>
                  <option value="sms">SMS</option>
                </select>
              </div>

              <div class="form-group">
                <label>Déclencheur</label>
                <select v-model="form.declencheur">
                  <option v-for="d in declencheurs" :key="d.value" :value="d.value">
                    {{ d.label }}
                  </option>
                </select>
              </div>
            </div>

            <div v-if="form.type === 'email'" class="form-group">
              <label>Sujet de l'email</label>
              <input v-model="form.sujet" type="text" />
            </div>

            <div class="form-group">
              <label>Contenu *</label>
              <textarea v-model="form.contenu" rows="8" required></textarea>
            </div>

            <div class="form-group checkbox-group">
              <label>
                <input v-model="form.actif" type="checkbox" />
                Template actif
              </label>
            </div>
          </div>

          <div class="variables-panel">
            <h4>Variables disponibles</h4>
            <p class="hint">Cliquez pour insérer</p>
            <div class="variables-list">
              <button
                v-for="v in variables"
                :key="v.code"
                type="button"
                class="variable-btn"
                @click="insertVariable(v.code)"
              >
                <code>{{ v.code }}</code>
                <span>{{ v.desc }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showModal = false">
            Annuler
          </button>
          <button
            class="btn btn-primary"
            @click="saveTemplate"
            :disabled="!form.nom || !form.contenu"
          >
            {{ editingTemplate ? 'Enregistrer' : 'Créer' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.templates-view {
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 1.75rem;
  margin: 0 0 0.25rem;
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

.btn-secondary {
  background: white;
  border: 1px solid #d1d5db;
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

/* Templates List */
.templates-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.template-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.template-card.inactive {
  opacity: 0.6;
}

.template-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.template-type {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.template-type.email {
  background: #dbeafe;
}

.template-type.sms {
  background: #dcfce7;
}

.template-info {
  flex: 1;
}

.template-info h3 {
  margin: 0 0 0.25rem;
}

.template-trigger {
  font-size: 0.85rem;
  color: #6b7280;
}

.status {
  font-size: 0.8rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: #f3f4f6;
  color: #6b7280;
}

.status.active {
  background: #dcfce7;
  color: #15803d;
}

.template-preview {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.template-preview .subject {
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.template-preview p {
  margin: 0;
  color: #6b7280;
  font-size: 0.9rem;
}

.template-actions {
  display: flex;
  gap: 0.75rem;
}

.action-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f9fafb;
}

.action-btn.delete:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.empty-state {
  text-align: center;
  padding: 4rem;
  color: #6b7280;
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
  border-radius: 12px;
  padding: 1.5rem;
  margin: 1rem;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-large {
  width: 100%;
  max-width: 800px;
}

.modal h3 {
  margin: 0 0 1.5rem;
}

.modal-content {
  display: grid;
  grid-template-columns: 1fr 250px;
  gap: 1.5rem;
}

@media (max-width: 768px) {
  .modal-content {
    grid-template-columns: 1fr;
  }
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-row .form-group {
  flex: 1;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.variables-panel {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
}

.variables-panel h4 {
  margin: 0 0 0.25rem;
  font-size: 0.9rem;
}

.variables-panel .hint {
  color: #6b7280;
  font-size: 0.8rem;
  margin: 0 0 1rem;
}

.variables-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.variable-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.variable-btn:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.variable-btn code {
  font-size: 0.75rem;
  color: #3b82f6;
}

.variable-btn span {
  font-size: 0.75rem;
  color: #6b7280;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}
</style>

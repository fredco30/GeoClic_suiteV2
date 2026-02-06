<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'

const emit = defineEmits<{
  (e: 'complete'): void
  (e: 'skip'): void
}>()

const currentStep = ref(1)
const totalSteps = 5
const saving = ref(false)
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null)
const logoFile = ref<File | null>(null)
const logoPreview = ref<string | null>(null)
const uploadingLogo = ref(false)

function onLogoSelected(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!['png', 'jpg', 'jpeg', 'svg', 'webp', 'gif'].includes(ext || '')) {
      message.value = { type: 'error', text: 'Format non supporté. Utilisez PNG, JPG, SVG ou WebP.' }
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      message.value = { type: 'error', text: 'Fichier trop volumineux (max 5 MB).' }
      return
    }
    logoFile.value = file
    logoPreview.value = URL.createObjectURL(file)
    message.value = null
  }
}

async function uploadLogo(): Promise<string | null> {
  if (!logoFile.value) return null
  uploadingLogo.value = true
  try {
    const formData = new FormData()
    formData.append('file', logoFile.value)
    const res = await axios.post('/api/settings/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data.logo_url
  } catch (e) {
    console.warn('Upload logo échoué:', e)
    return null
  } finally {
    uploadingLogo.value = false
  }
}

// Step 1: Identité
const identity = ref({
  nom_collectivite: '',
  logo_url: '',
  primary_color: '#2563eb',
  sidebar_color: '#1f2937',
  accent_color: '#10b981',
  secondary_color: '#1f2937',
  email_contact: '',
  telephone: '',
  adresse: '',
  site_web: ''
})

// Step 2: Email
const email = ref({
  enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
  smtp_tls: true,
  sender_name: '',
  sender_email: '',
  notify_citizen_creation: true,
  notify_citizen_status_change: true,
  notify_service_new_demande: true,
  notify_agent_new_message: true,
  notify_agent_reminder: true,
  reminder_hours_before: 24
})

// Step 3: Catégories prédéfinies
const selectedTemplate = ref<string>('standard')
const categoriesTemplates = [
  {
    id: 'standard',
    name: 'Standard (recommandé)',
    description: 'Voirie, Propreté, Espaces verts, Éclairage, Mobilier urbain, Eau/Assainissement',
    categories: [
      { nom: 'Voirie', icone: 'road', couleur: '#795548', children: ['Nid de poule', 'Chaussée dégradée', 'Trottoir abîmé', 'Signalisation'] },
      { nom: 'Propreté', icone: 'delete', couleur: '#FF9800', children: ['Dépôt sauvage', 'Poubelle débordante', 'Graffiti', 'Déjections animales'] },
      { nom: 'Espaces verts', icone: 'park', couleur: '#4CAF50', children: ['Arbre dangereux', 'Végétation envahissante', 'Aire de jeux abîmée'] },
      { nom: 'Éclairage', icone: 'lightbulb', couleur: '#FFC107', children: ['Lampadaire éteint', 'Lampadaire cassé', 'Éclairage insuffisant'] },
      { nom: 'Mobilier urbain', icone: 'chair', couleur: '#9C27B0', children: ['Banc cassé', 'Poteau abîmé', 'Abribus dégradé'] },
      { nom: 'Eau / Assainissement', icone: 'water_drop', couleur: '#2196F3', children: ['Fuite d\'eau', 'Bouche d\'égout bouchée', 'Inondation'] },
    ]
  },
  {
    id: 'minimal',
    name: 'Minimal',
    description: 'Voirie, Propreté, Espaces verts seulement',
    categories: [
      { nom: 'Voirie', icone: 'road', couleur: '#795548', children: ['Nid de poule', 'Chaussée dégradée', 'Trottoir abîmé'] },
      { nom: 'Propreté', icone: 'delete', couleur: '#FF9800', children: ['Dépôt sauvage', 'Poubelle débordante'] },
      { nom: 'Espaces verts', icone: 'park', couleur: '#4CAF50', children: ['Arbre dangereux', 'Végétation envahissante'] },
    ]
  },
  {
    id: 'custom',
    name: 'Personnalisé',
    description: 'Ne créer aucune catégorie - vous les configurerez manuellement',
    categories: []
  }
]

// Step 4: Services
const defaultServices = ref([
  { nom: 'Service Technique', code: 'ST', couleur: '#2196F3', actif: true },
  { nom: 'Espaces Verts', code: 'EV', couleur: '#4CAF50', actif: true },
  { nom: 'Propreté Urbaine', code: 'PU', couleur: '#FF9800', actif: true },
])
const createDefaultServices = ref(true)

// Step 5: Récapitulatif
const setupComplete = ref(false)

const progress = computed(() => Math.round((currentStep.value / totalSteps) * 100))

const stepTitle = computed(() => {
  const titles: Record<number, string> = {
    1: 'Identité de votre collectivité',
    2: 'Configuration email',
    3: 'Catégories de signalements',
    4: 'Services municipaux',
    5: 'Récapitulatif'
  }
  return titles[currentStep.value] || ''
})

function nextStep() {
  if (currentStep.value < totalSteps) {
    currentStep.value++
    message.value = null
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
    message.value = null
  }
}

// Convertir couleur hex (#RRGGBB) en entier ARGB (format attendu par l'API catégories)
function hexToArgb(hex: string): number {
  const clean = hex.replace('#', '')
  const r = parseInt(clean.substring(0, 2), 16)
  const g = parseInt(clean.substring(2, 4), 16)
  const b = parseInt(clean.substring(4, 6), 16)
  // Alpha = 255 (opaque) + RGB
  return ((255 << 24) | (r << 16) | (g << 8) | b) >>> 0
}

// Récupérer le project_id du projet système "Signalements Citoyens"
async function getSystemProjectId(): Promise<string | null> {
  try {
    const res = await axios.get('/api/projects', { params: { include_system: true } })
    const systemProject = res.data.find((p: any) => p.is_system)
    return systemProject?.id || null
  } catch (e) {
    console.warn('Impossible de récupérer le projet système:', e)
    return null
  }
}

async function finishSetup() {
  saving.value = true
  message.value = null

  try {
    // 0. Uploader le logo s'il y en a un
    if (logoFile.value) {
      const logoUrl = await uploadLogo()
      if (logoUrl) {
        identity.value.logo_url = logoUrl
      }
    }

    // 1. Sauvegarder l'identité / branding
    await axios.put('/api/settings/general', identity.value)

    // 2. Sauvegarder la config email (si activée)
    if (email.value.enabled) {
      await axios.put('/api/settings/email', email.value)
    }

    // 3. Récupérer le project_id système (requis pour catégories et services)
    const projectId = await getSystemProjectId()
    if (!projectId) {
      console.warn('Projet système non trouvé - catégories et services non créés')
    }

    // 4. Créer les catégories
    if (projectId) {
      const template = categoriesTemplates.find(t => t.id === selectedTemplate.value)
      if (template && template.categories.length > 0) {
        for (const cat of template.categories) {
          try {
            const parentRes = await axios.post('/api/demandes/categories', {
              nom: cat.nom,
              icone: cat.icone,
              couleur: hexToArgb(cat.couleur),
              actif: true
            }, { params: { project_id: projectId } })
            const parentId = parentRes.data.id
            // Créer les sous-catégories
            for (const childName of cat.children) {
              try {
                await axios.post('/api/demandes/categories', {
                  nom: childName,
                  icone: cat.icone,
                  couleur: hexToArgb(cat.couleur),
                  parent_id: parentId,
                  actif: true
                }, { params: { project_id: projectId } })
              } catch (e) {
                console.warn(`Sous-catégorie "${childName}" non créée:`, e)
              }
            }
          } catch (e) {
            console.warn(`Catégorie "${cat.nom}" non créée:`, e)
          }
        }
      }
    }

    // 5. Créer les services
    if (projectId && createDefaultServices.value) {
      for (const svc of defaultServices.value) {
        if (svc.actif) {
          try {
            await axios.post('/api/demandes/services', {
              nom: svc.nom,
              code: svc.code,
              couleur: svc.couleur,
              actif: true
            }, { params: { project_id: projectId } })
          } catch (e) {
            console.warn(`Service "${svc.nom}" non créé:`, e)
          }
        }
      }
    }

    // 6. Marquer l'onboarding comme terminé
    localStorage.setItem('geoclic_onboarding_complete', 'true')
    setupComplete.value = true

  } catch (error: any) {
    message.value = {
      type: 'error',
      text: error.response?.data?.detail || 'Erreur lors de la configuration. Certains éléments peuvent avoir été créés partiellement.'
    }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="wizard-overlay">
    <div class="wizard-container">
      <!-- Header -->
      <div class="wizard-header">
        <h2>Configuration initiale de GéoClic</h2>
        <p>{{ stepTitle }}</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="step-indicators">
          <span
            v-for="s in totalSteps"
            :key="s"
            class="step-dot"
            :class="{ active: s === currentStep, done: s < currentStep }"
          >{{ s }}</span>
        </div>
      </div>

      <!-- Message -->
      <div v-if="message" :class="['wizard-message', message.type]">
        {{ message.text }}
      </div>

      <!-- Step 1: Identité -->
      <div v-if="currentStep === 1" class="wizard-body">
        <div class="form-group">
          <label>Nom de la collectivité *</label>
          <input v-model="identity.nom_collectivite" type="text" placeholder="Mairie de..." />
          <small>Ce nom sera affiché sur le portail citoyen et dans les emails</small>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Email de contact</label>
            <input v-model="identity.email_contact" type="email" placeholder="contact@mairie.fr" />
          </div>
          <div class="form-group">
            <label>Téléphone</label>
            <input v-model="identity.telephone" type="tel" placeholder="01 23 45 67 89" />
          </div>
        </div>

        <div class="form-group">
          <label>Adresse</label>
          <input v-model="identity.adresse" type="text" placeholder="1 Place de la Mairie, 75000 Paris" />
        </div>

        <div class="form-group">
          <label>Logo de la collectivité (optionnel)</label>
          <div class="logo-upload-area">
            <div v-if="logoPreview" class="logo-preview">
              <img :src="logoPreview" alt="Aperçu logo" />
              <button type="button" class="btn-remove-logo" @click="logoFile = null; logoPreview = null">&times;</button>
            </div>
            <label v-else class="logo-upload-btn">
              <input type="file" accept=".png,.jpg,.jpeg,.svg,.webp,.gif" @change="onLogoSelected" hidden />
              <span class="upload-icon">&#128247;</span>
              <span>Choisir un fichier</span>
            </label>
          </div>
          <small>Format PNG ou SVG recommandé, hauteur 40px, max 5 MB</small>
        </div>

        <div class="color-section">
          <label>Couleur principale</label>
          <div class="color-row">
            <input v-model="identity.primary_color" type="color" class="color-input" />
            <span class="color-hex">{{ identity.primary_color }}</span>
          </div>
        </div>
      </div>

      <!-- Step 2: Email -->
      <div v-if="currentStep === 2" class="wizard-body">
        <div class="info-box">
          <p>La configuration email permet d'envoyer des notifications aux citoyens et aux agents. Vous pourrez la configurer plus tard dans les paramètres si vous préférez.</p>
        </div>

        <div class="form-group checkbox-group">
          <label>
            <input v-model="email.enabled" type="checkbox" />
            <strong>Activer les notifications email</strong>
          </label>
        </div>

        <template v-if="email.enabled">
          <div class="form-row">
            <div class="form-group" style="flex: 2">
              <label>Serveur SMTP</label>
              <input v-model="email.smtp_host" type="text" placeholder="smtp.office365.com" />
            </div>
            <div class="form-group">
              <label>Port</label>
              <input v-model="email.smtp_port" type="number" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Utilisateur SMTP</label>
              <input v-model="email.smtp_user" type="text" placeholder="user@domain.com" />
            </div>
            <div class="form-group">
              <label>Mot de passe</label>
              <input v-model="email.smtp_password" type="password" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Nom expéditeur</label>
              <input v-model="email.sender_name" type="text" :placeholder="identity.nom_collectivite || 'Mairie de...'" />
            </div>
            <div class="form-group">
              <label>Email expéditeur</label>
              <input v-model="email.sender_email" type="email" placeholder="noreply@mairie.fr" />
            </div>
          </div>
        </template>
      </div>

      <!-- Step 3: Catégories -->
      <div v-if="currentStep === 3" class="wizard-body">
        <div class="info-box">
          <p>Les catégories permettent aux citoyens de classer leurs signalements. Choisissez un modèle pour démarrer rapidement.</p>
        </div>

        <div class="template-cards">
          <div
            v-for="tmpl in categoriesTemplates"
            :key="tmpl.id"
            class="template-card"
            :class="{ selected: selectedTemplate === tmpl.id }"
            @click="selectedTemplate = tmpl.id"
          >
            <div class="template-radio">
              <span class="radio-dot" :class="{ active: selectedTemplate === tmpl.id }"></span>
            </div>
            <div class="template-info">
              <strong>{{ tmpl.name }}</strong>
              <p>{{ tmpl.description }}</p>
              <div v-if="tmpl.categories.length > 0" class="template-preview">
                <span
                  v-for="cat in tmpl.categories"
                  :key="cat.nom"
                  class="cat-tag"
                  :style="{ background: cat.couleur, color: 'white' }"
                >{{ cat.nom }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 4: Services -->
      <div v-if="currentStep === 4" class="wizard-body">
        <div class="info-box">
          <p>Les services municipaux reçoivent et traitent les signalements. Vous pourrez les modifier et en ajouter d'autres dans les paramètres.</p>
        </div>

        <div class="form-group checkbox-group">
          <label>
            <input v-model="createDefaultServices" type="checkbox" />
            <strong>Créer les services par défaut</strong>
          </label>
        </div>

        <div v-if="createDefaultServices" class="services-list">
          <div v-for="(svc, i) in defaultServices" :key="i" class="service-item">
            <input v-model="svc.actif" type="checkbox" />
            <span class="service-color" :style="{ background: svc.couleur }"></span>
            <input v-model="svc.nom" type="text" class="service-name-input" />
            <input v-model="svc.code" type="text" class="service-code-input" placeholder="Code" />
          </div>
        </div>
      </div>

      <!-- Step 5: Récapitulatif -->
      <div v-if="currentStep === 5" class="wizard-body">
        <div v-if="setupComplete" class="success-state">
          <div class="success-icon">&#10004;</div>
          <h3>Configuration terminée !</h3>
          <p>GéoClic est prêt à être utilisé pour <strong>{{ identity.nom_collectivite }}</strong>.</p>
          <button class="btn btn-primary btn-lg" @click="emit('complete')">
            Accéder au tableau de bord
          </button>
        </div>

        <template v-else>
          <h4>Récapitulatif de votre configuration</h4>

          <div class="recap-section">
            <h5>Collectivité</h5>
            <p><strong>{{ identity.nom_collectivite || '(non renseigné)' }}</strong></p>
            <p v-if="identity.email_contact">Contact : {{ identity.email_contact }}</p>
            <p v-if="identity.telephone">Tél : {{ identity.telephone }}</p>
          </div>

          <div class="recap-section">
            <h5>Email</h5>
            <p v-if="email.enabled">Activé - {{ email.smtp_host }}:{{ email.smtp_port }}</p>
            <p v-else>Non configuré (vous pourrez le faire plus tard)</p>
          </div>

          <div class="recap-section">
            <h5>Catégories</h5>
            <p>{{ categoriesTemplates.find(t => t.id === selectedTemplate)?.name }}</p>
          </div>

          <div class="recap-section">
            <h5>Services</h5>
            <p v-if="createDefaultServices">
              {{ defaultServices.filter(s => s.actif).map(s => s.nom).join(', ') }}
            </p>
            <p v-else>Aucun service créé</p>
          </div>
        </template>
      </div>

      <!-- Footer -->
      <div v-if="!setupComplete" class="wizard-footer">
        <button v-if="currentStep === 1" class="btn btn-link" @click="emit('skip')">
          Passer la configuration
        </button>
        <button v-else class="btn btn-secondary" @click="prevStep">
          Précédent
        </button>

        <div class="footer-right">
          <button
            v-if="currentStep < totalSteps"
            class="btn btn-primary"
            @click="nextStep"
            :disabled="currentStep === 1 && !identity.nom_collectivite"
          >
            Suivant
          </button>
          <button
            v-else
            class="btn btn-primary btn-lg"
            @click="finishSetup"
            :disabled="saving"
          >
            {{ saving ? 'Configuration en cours...' : 'Lancer la configuration' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wizard-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.wizard-container {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  margin: 1rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.wizard-header {
  padding: 2rem 2rem 1rem;
  text-align: center;
}

.wizard-header h2 {
  font-size: 1.5rem;
  margin: 0 0 0.25rem;
  color: #1f2937;
}

.wizard-header p {
  color: #6b7280;
  margin: 0 0 1rem;
}

.progress-bar {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.progress-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.step-indicators {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  background: #f3f4f6;
  color: #9ca3af;
  transition: all 0.2s;
}

.step-dot.active {
  background: #3b82f6;
  color: white;
}

.step-dot.done {
  background: #10b981;
  color: white;
}

.wizard-message {
  margin: 0 2rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.wizard-message.success { background: #dcfce7; color: #15803d; }
.wizard-message.error { background: #fee2e2; color: #dc2626; }

.wizard-body {
  padding: 1.5rem 2rem;
}

.wizard-footer {
  padding: 1rem 2rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f3f4f6;
}

.footer-right {
  display: flex;
  gap: 0.75rem;
}

/* Forms */
.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.4rem;
  font-size: 0.9rem;
}

.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="tel"],
.form-group input[type="url"],
.form-group input[type="password"],
.form-group input[type="number"] {
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.9rem;
}

.form-group small {
  display: block;
  color: #9ca3af;
  font-size: 0.8rem;
  margin-top: 0.25rem;
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

.color-section {
  margin-bottom: 1rem;
}

.color-section label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.4rem;
  font-size: 0.9rem;
}

.color-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.color-input {
  width: 44px;
  height: 36px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
}

.color-hex {
  font-family: monospace;
  color: #6b7280;
}

/* Logo upload */
.logo-upload-area {
  margin-top: 0.25rem;
}

.logo-upload-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.15s;
}

.logo-upload-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #f0f9ff;
}

.upload-icon {
  font-size: 1.2rem;
}

.logo-preview {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.logo-preview img {
  max-height: 48px;
  max-width: 200px;
  object-fit: contain;
}

.btn-remove-logo {
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}

.btn-remove-logo:hover {
  background: #fca5a5;
}

/* Info box */
.info-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.25rem;
}

.info-box p {
  margin: 0;
  color: #0369a1;
  font-size: 0.9rem;
}

/* Templates */
.template-cards {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.template-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.template-card:hover {
  border-color: #93c5fd;
}

.template-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.template-radio {
  padding-top: 0.2rem;
}

.radio-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
  display: block;
  position: relative;
}

.radio-dot.active {
  border-color: #3b82f6;
}

.radio-dot.active::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #3b82f6;
}

.template-info {
  flex: 1;
}

.template-info strong {
  display: block;
  margin-bottom: 0.25rem;
}

.template-info p {
  color: #6b7280;
  font-size: 0.85rem;
  margin: 0 0 0.5rem;
}

.template-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.cat-tag {
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Services */
.services-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.service-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
}

.service-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  flex-shrink: 0;
}

.service-name-input {
  flex: 1;
  padding: 0.4rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
}

.service-code-input {
  width: 60px;
  padding: 0.4rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.85rem;
  font-family: monospace;
  text-transform: uppercase;
  text-align: center;
}

/* Recap */
.recap-section {
  padding: 0.75rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.recap-section h5 {
  font-size: 0.8rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 0.25rem;
}

.recap-section p {
  margin: 0;
  font-size: 0.9rem;
}

/* Success */
.success-state {
  text-align: center;
  padding: 2rem 0;
}

.success-icon {
  width: 64px;
  height: 64px;
  background: #dcfce7;
  color: #15803d;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  margin: 0 auto 1rem;
}

.success-state h3 {
  margin: 0 0 0.5rem;
}

.success-state p {
  color: #6b7280;
  margin: 0 0 1.5rem;
}

/* Buttons */
.btn {
  padding: 0.6rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  transition: all 0.15s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-secondary {
  background: white;
  border: 1px solid #d1d5db;
  color: #374151;
}

.btn-secondary:hover { background: #f9fafb; }

.btn-link {
  background: none;
  color: #6b7280;
  text-decoration: underline;
  padding: 0.6rem 0.5rem;
}

.btn-lg {
  padding: 0.75rem 2rem;
  font-size: 1rem;
}
</style>

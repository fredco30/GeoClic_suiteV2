<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useConfigStore } from '@/stores/config'
import { api, type DemandeCreate, type Category, type DoublonPotentiel } from '@/services/api'
import MapPicker from '@/components/MapPicker.vue'
import PhotoUploader from '@/components/PhotoUploader.vue'
import CategorySelector from '@/components/CategorySelector.vue'

const router = useRouter()
const configStore = useConfigStore()

const currentStep = ref(1)
const totalSteps = 4

// Form data
const selectedCategory = ref<Category | null>(null)
const description = ref('')
const email = ref('')
const telephone = ref('')
const nom = ref('')
const photos = ref<string[]>([])
const coordonnees = ref<{ latitude: number; longitude: number } | null>(null)
const adresse = ref('')
const champsSupplementaires = ref<Record<string, unknown>>({})

// UI state
const loading = ref(false)
const error = ref('')
const success = ref(false)
const numeroSuivi = ref('')
const showMap = ref(false)

// Doublons detection
const doublons = ref<DoublonPotentiel[]>([])
const doublonsLoading = ref(false)
const doublonsChecked = ref(false)
const doublonsIgnored = ref(false)

const categories = computed(() => configStore.categories)

const canGoNext = computed(() => {
  switch (currentStep.value) {
    case 1:
      return selectedCategory.value !== null
    case 2:
      return description.value.trim().length >= 10
    case 3:
      return coordonnees.value !== null || adresse.value.trim().length > 0
    case 4:
      return email.value.includes('@') && email.value.includes('.')
    default:
      return false
  }
})

function nextStep() {
  if (canGoNext.value && currentStep.value < totalSteps) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

function onLocationSelected(location: { lat: number; lng: number; address?: string }) {
  coordonnees.value = { latitude: location.lat, longitude: location.lng }
  if (location.address) {
    adresse.value = location.address
  }
  showMap.value = false
  // Check for duplicates when location is selected
  checkDoublons()
}

function openMap() {
  showMap.value = true
}

function closeMap() {
  showMap.value = false
}

async function checkDoublons() {
  if (!selectedCategory.value || !coordonnees.value || !configStore.projectId) {
    return
  }

  doublonsLoading.value = true
  doublonsChecked.value = false
  doublons.value = []

  try {
    const response = await api.checkDoublons(
      configStore.projectId,
      selectedCategory.value.id,
      coordonnees.value.latitude,
      coordonnees.value.longitude,
      50,  // 50 mètres
      30   // 30 jours
    )
    doublons.value = response.doublons
    doublonsChecked.value = true
  } catch (err) {
    console.error('Erreur vérification doublons:', err)
  } finally {
    doublonsLoading.value = false
  }
}

function ignoreDoublons() {
  doublonsIgnored.value = true
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

function onPhotosChanged(urls: string[]) {
  photos.value = urls
}

async function submitDemande() {
  if (!selectedCategory.value || !configStore.projectId) return

  loading.value = true
  error.value = ''

  try {
    const demande: DemandeCreate = {
      categorie_id: selectedCategory.value.id,
      description: description.value,
      declarant_email: email.value,
      declarant_telephone: telephone.value || undefined,
      declarant_nom: nom.value || undefined,
      declarant_langue: 'fr',
      coordonnees: coordonnees.value || undefined,
      adresse_approximative: adresse.value || undefined,
      photos: photos.value.length > 0 ? photos.value : undefined,
      champs_supplementaires: Object.keys(champsSupplementaires.value).length > 0
        ? champsSupplementaires.value
        : undefined,
      source: 'web',
    }

    const response = await api.createDemande(configStore.projectId, demande)
    numeroSuivi.value = response.numero_suivi
    success.value = true
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'Une erreur est survenue'
    error.value = errorMessage
  } finally {
    loading.value = false
  }
}

function goToSuivi() {
  router.push(`/suivi/${numeroSuivi.value}`)
}

onMounted(() => {
  if (!configStore.projectId) {
    // Redirect to config or show project selector
  }
})
</script>

<template>
  <div class="signaler">
    <div class="container">
      <!-- Success State -->
      <div v-if="success" class="success-card">
        <div class="success-icon">&#9989;</div>
        <h2>Signalement envoyé !</h2>
        <p>Votre demande a bien été enregistrée.</p>
        <div class="numero-suivi-box">
          <span class="label">Votre numéro de suivi</span>
          <span class="numero">{{ numeroSuivi }}</span>
        </div>
        <p class="info">Un email de confirmation a été envoyé à <strong>{{ email }}</strong></p>
        <div class="success-actions">
          <button @click="goToSuivi" class="btn btn-primary">Suivre ma demande</button>
          <router-link to="/" class="btn btn-outline">Retour à l'accueil</router-link>
        </div>
      </div>

      <!-- Form -->
      <div v-else class="form-container">
        <h1>Signaler un problème</h1>

        <!-- Progress Bar -->
        <div class="progress-bar">
          <div class="progress-steps">
            <div
              v-for="step in totalSteps"
              :key="step"
              :class="['progress-step', { active: step === currentStep, completed: step < currentStep }]"
            >
              <span class="step-number">{{ step }}</span>
              <span class="step-label">
                {{ step === 1 ? 'Catégorie' : step === 2 ? 'Description' : step === 3 ? 'Localisation' : 'Contact' }}
              </span>
            </div>
          </div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: ((currentStep - 1) / (totalSteps - 1)) * 100 + '%' }"></div>
          </div>
        </div>

        <!-- Step 1: Category -->
        <div v-show="currentStep === 1" class="step-content">
          <h2>Choisissez une catégorie</h2>
          <p class="step-description">Sélectionnez le type de problème que vous souhaitez signaler.</p>

          <CategorySelector
            :categories="categories"
            v-model="selectedCategory"
          />
        </div>

        <!-- Step 2: Description -->
        <div v-show="currentStep === 2" class="step-content">
          <h2>Décrivez le problème</h2>
          <p class="step-description">Donnez le plus de détails possible pour faciliter l'intervention.</p>

          <div class="form-group">
            <label for="description">Description *</label>
            <textarea
              id="description"
              v-model="description"
              rows="5"
              placeholder="Décrivez le problème que vous avez constaté..."
              required
            ></textarea>
            <span class="char-count">{{ description.length }} caractères (minimum 10)</span>
          </div>

          <div class="form-group">
            <label>Photos (optionnel)</label>
            <PhotoUploader @change="onPhotosChanged" :max="3" />
          </div>
        </div>

        <!-- Step 3: Location -->
        <div v-show="currentStep === 3" class="step-content">
          <h2>Localisez le problème</h2>
          <p class="step-description">Indiquez l'emplacement exact du problème.</p>

          <!-- Location selector -->
          <div v-if="coordonnees" class="location-selected">
            <div class="location-icon">&#128205;</div>
            <div class="location-info">
              <div class="location-address">{{ adresse || 'Position sélectionnée' }}</div>
              <div class="location-coords">
                {{ coordonnees.latitude.toFixed(6) }}, {{ coordonnees.longitude.toFixed(6) }}
              </div>
            </div>
            <button @click="openMap" class="btn btn-outline btn-sm">Modifier</button>
          </div>

          <button v-else @click="openMap" class="open-map-btn">
            <span class="map-icon">&#128506;</span>
            <span class="map-text">
              <strong>Ouvrir la carte</strong>
              <small>Sélectionnez la position du problème</small>
            </span>
            <span class="arrow">&rarr;</span>
          </button>

          <div class="form-group" v-if="coordonnees">
            <label for="adresse">Précisions sur l'emplacement (optionnel)</label>
            <input
              id="adresse"
              v-model="adresse"
              type="text"
              placeholder="Ex: Devant le n°15, près du banc..."
            />
          </div>

          <!-- Doublons détectés -->
          <div v-if="doublonsLoading" class="doublons-loading">
            &#8987; Vérification des signalements similaires...
          </div>

          <div v-else-if="doublons.length > 0 && !doublonsIgnored" class="doublons-warning">
            <div class="doublons-header">
              <span class="doublons-icon">&#9888;</span>
              <div>
                <h3>Signalements similaires détectés</h3>
                <p>{{ doublons.length }} signalement(s) similaire(s) à proximité. Vérifiez si votre problème n'a pas déjà été signalé.</p>
              </div>
            </div>

            <div class="doublons-list">
              <div v-for="doublon in doublons" :key="doublon.id" class="doublon-item">
                <div class="doublon-content">
                  <div class="doublon-meta">
                    <span class="doublon-numero">{{ doublon.numero_suivi }}</span>
                    <span class="doublon-distance">{{ Math.round(doublon.distance_metres) }}m</span>
                    <span class="doublon-date">{{ formatDate(doublon.created_at) }}</span>
                    <span :class="['doublon-statut', doublon.statut]">{{ doublon.statut }}</span>
                  </div>
                  <p class="doublon-description">{{ doublon.description }}</p>
                  <div v-if="doublon.photos && doublon.photos.length > 0" class="doublon-photos">
                    <img v-for="(photo, idx) in doublon.photos.slice(0, 2)" :key="idx" :src="photo" alt="Photo" />
                  </div>
                </div>
                <div class="doublon-score" :title="'Score de similarité: ' + doublon.score_similarite + '%'">
                  {{ doublon.score_similarite }}%
                </div>
              </div>
            </div>

            <div class="doublons-actions">
              <button @click="ignoreDoublons" class="btn btn-outline btn-sm">
                Ce n'est pas un doublon, continuer
              </button>
            </div>
          </div>
        </div>

        <!-- Step 4: Contact -->
        <div v-show="currentStep === 4" class="step-content">
          <h2>Vos coordonnées</h2>
          <p class="step-description">Pour vous tenir informé de l'avancement de votre demande.</p>

          <div class="form-group">
            <label for="email">Email *</label>
            <input
              id="email"
              v-model="email"
              type="email"
              placeholder="votre@email.fr"
              required
            />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="nom">Nom (optionnel)</label>
              <input
                id="nom"
                v-model="nom"
                type="text"
                placeholder="Votre nom"
              />
            </div>
            <div class="form-group">
              <label for="telephone">Téléphone (optionnel)</label>
              <input
                id="telephone"
                v-model="telephone"
                type="tel"
                placeholder="06 12 34 56 78"
              />
            </div>
          </div>

          <div class="privacy-notice">
            <span class="icon">&#128274;</span>
            <p>Vos données personnelles sont traitées conformément au RGPD et ne seront utilisées que pour le traitement de votre demande.</p>
          </div>
        </div>

        <!-- Error message -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <!-- Navigation -->
        <div class="form-navigation">
          <button v-if="currentStep > 1" @click="prevStep" class="btn btn-outline">
            &#8592; Précédent
          </button>
          <div v-else></div>

          <button
            v-if="currentStep < totalSteps"
            @click="nextStep"
            :disabled="!canGoNext"
            class="btn btn-primary"
          >
            Suivant &#8594;
          </button>
          <button
            v-else
            @click="submitDemande"
            :disabled="!canGoNext || loading"
            class="btn btn-primary btn-submit"
          >
            <span v-if="loading">Envoi en cours...</span>
            <span v-else>Envoyer le signalement</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Fullscreen Map Overlay -->
    <MapPicker
      v-if="showMap"
      :initial-coords="coordonnees"
      :fullscreen="true"
      @select="onLocationSelected"
      @close="closeMap"
    />
  </div>
</template>

<style scoped>
.signaler {
  padding: 2rem;
  min-height: 100%;
}

.container {
  max-width: 800px;
  margin: 0 auto;
}

/* Success Card */
.success-card {
  background: white;
  border-radius: 16px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.success-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.success-card h2 {
  color: #059669;
  margin-bottom: 0.5rem;
}

.numero-suivi-box {
  background: #f0fdf4;
  border: 2px solid #059669;
  border-radius: 12px;
  padding: 1.5rem;
  margin: 2rem 0;
}

.numero-suivi-box .label {
  display: block;
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.numero-suivi-box .numero {
  font-size: 1.5rem;
  font-weight: 700;
  color: #059669;
  font-family: monospace;
}

.success-card .info {
  color: #6b7280;
  margin-bottom: 2rem;
}

.success-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* Form Container */
.form-container {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.form-container h1 {
  text-align: center;
  color: #1f2937;
  margin-bottom: 2rem;
}

/* Progress Bar */
.progress-bar {
  margin-bottom: 2rem;
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.progress-step .step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.progress-step.active .step-number {
  background: var(--primary-color, #2563eb);
  color: white;
}

.progress-step.completed .step-number {
  background: #059669;
  color: white;
}

.progress-step .step-label {
  font-size: 0.75rem;
  color: #6b7280;
}

.progress-step.active .step-label {
  color: var(--primary-color, #2563eb);
  font-weight: 500;
}

.progress-track {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  margin-top: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color, #2563eb);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* Step Content */
.step-content {
  min-height: 300px;
}

.step-content h2 {
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.step-description {
  color: #6b7280;
  margin-bottom: 1.5rem;
}

/* Form Groups */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--primary-color, #2563eb);
}

.form-group textarea {
  resize: vertical;
  min-height: 120px;
}

.char-count {
  font-size: 0.8rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* Privacy Notice */
.privacy-notice {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: #f3f4f6;
  border-radius: 8px;
  margin-top: 1.5rem;
}

.privacy-notice .icon {
  font-size: 1.5rem;
}

.privacy-notice p {
  font-size: 0.85rem;
  color: #6b7280;
  margin: 0;
}

/* Error Message */
.error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

/* Navigation */
.form-navigation {
  display: flex;
  justify-content: space-between;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
  font-size: 1rem;
}

.btn-primary {
  background: var(--primary-color, #2563eb);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-outline {
  background: transparent;
  color: var(--primary-color, #2563eb);
  border: 2px solid var(--primary-color, #2563eb);
}

.btn-outline:hover {
  background: var(--primary-color, #2563eb);
  color: white;
}

.btn-submit {
  min-width: 200px;
  justify-content: center;
}

/* Doublons Detection */
.doublons-loading {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  color: #92400e;
  margin-top: 1rem;
}

.doublons-warning {
  background: #fef3c7;
  border: 2px solid #f59e0b;
  border-radius: 12px;
  padding: 1.5rem;
  margin-top: 1.5rem;
}

.doublons-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.doublons-icon {
  font-size: 2rem;
  color: #f59e0b;
}

.doublons-header h3 {
  margin: 0 0 0.25rem 0;
  color: #92400e;
  font-size: 1.1rem;
}

.doublons-header p {
  margin: 0;
  color: #b45309;
  font-size: 0.9rem;
}

.doublons-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.doublon-item {
  display: flex;
  gap: 1rem;
  background: white;
  border-radius: 8px;
  padding: 1rem;
  align-items: flex-start;
}

.doublon-content {
  flex: 1;
  min-width: 0;
}

.doublon-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
}

.doublon-numero {
  font-weight: 600;
  color: #1f2937;
  font-family: monospace;
}

.doublon-distance {
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.doublon-date {
  color: #6b7280;
}

.doublon-statut {
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
  text-transform: capitalize;
}

.doublon-statut.nouveau {
  background: #dbeafe;
  color: #1e40af;
}

.doublon-statut.en_cours,
.doublon-statut.en_moderation {
  background: #fef3c7;
  color: #92400e;
}

.doublon-statut.traite {
  background: #d1fae5;
  color: #065f46;
}

.doublon-description {
  font-size: 0.9rem;
  color: #374151;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.doublon-photos {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.doublon-photos img {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 6px;
}

.doublon-score {
  background: #dc2626;
  color: white;
  font-weight: 700;
  font-size: 0.85rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  white-space: nowrap;
}

.doublons-actions {
  display: flex;
  justify-content: center;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

/* Location Selector */
.location-selected {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f0fdf4;
  border: 2px solid #22c55e;
  border-radius: 12px;
  margin-bottom: 1.5rem;
}

.location-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.location-info {
  flex: 1;
  min-width: 0;
}

.location-address {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
  line-height: 1.3;
}

.location-coords {
  font-size: 0.8rem;
  color: #6b7280;
  font-family: monospace;
}

.open-map-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  margin-bottom: 1.5rem;
}

.open-map-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.3);
}

.open-map-btn .map-icon {
  font-size: 2.5rem;
  flex-shrink: 0;
}

.open-map-btn .map-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.open-map-btn .map-text strong {
  font-size: 1.1rem;
}

.open-map-btn .map-text small {
  font-size: 0.85rem;
  opacity: 0.8;
}

.open-map-btn .arrow {
  font-size: 1.5rem;
  flex-shrink: 0;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .progress-step .step-label {
    display: none;
  }

  .doublons-header {
    flex-direction: column;
    text-align: center;
  }

  .doublon-item {
    flex-direction: column;
  }

  .doublon-score {
    align-self: flex-end;
  }
}
</style>

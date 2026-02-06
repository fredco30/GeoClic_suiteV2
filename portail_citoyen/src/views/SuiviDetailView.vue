<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type DemandeDetail } from '@/services/api'

const route = useRoute()
const router = useRouter()

const demande = ref<DemandeDetail | null>(null)
const loading = ref(true)
const error = ref('')

const numeroSuivi = computed(() => route.params.numeroSuivi as string)

const statutInfo = computed(() => {
  if (!demande.value) return null

  const statuts: Record<string, { label: string; color: string; icon: string }> = {
    nouveau: { label: 'Nouveau', color: '#3b82f6', icon: '&#128233;' },
    en_moderation: { label: 'En modération', color: '#f59e0b', icon: '&#128269;' },
    envoye: { label: 'Transmis au service', color: '#0ea5e9', icon: '&#128228;' },
    accepte: { label: 'Accepté', color: '#10b981', icon: '&#9989;' },
    en_cours: { label: 'En cours', color: '#8b5cf6', icon: '&#128736;' },
    planifie: { label: 'Intervention planifiée', color: '#6366f1', icon: '&#128197;' },
    traite: { label: 'Traité', color: '#059669', icon: '&#9989;' },
    rejete: { label: 'Non retenu', color: '#ef4444', icon: '&#10060;' },
    cloture: { label: 'Clôturé', color: '#6b7280', icon: '&#128274;' },
  }

  return statuts[demande.value.statut] || { label: demande.value.statut, color: '#6b7280', icon: '&#9679;' }
})

const progressPercent = computed(() => {
  if (!demande.value) return 0

  const statusOrder = ['nouveau', 'en_moderation', 'envoye', 'accepte', 'en_cours', 'planifie', 'traite']
  const currentIndex = statusOrder.indexOf(demande.value.statut)

  if (demande.value.statut === 'rejete' || demande.value.statut === 'cloture') {
    return 100
  }

  return Math.round(((currentIndex + 1) / statusOrder.length) * 100)
})

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDateShort(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
  })
}

async function loadDemande() {
  loading.value = true
  error.value = ''

  const email = sessionStorage.getItem('suivi_email')

  if (!email) {
    router.push('/suivi')
    return
  }

  try {
    demande.value = await api.getDemande(numeroSuivi.value, email)
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'response' in err) {
      const response = (err as { response?: { status: number } }).response
      if (response?.status === 404) {
        error.value = 'Demande non trouvée. Vérifiez le numéro de suivi et l\'email.'
      } else {
        error.value = 'Une erreur est survenue. Veuillez réessayer.'
      }
    } else {
      error.value = 'Une erreur est survenue. Veuillez réessayer.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDemande()
})
</script>

<template>
  <div class="suivi-detail-page">
    <div class="container">
      <!-- Loading -->
      <div v-if="loading" class="loading-card">
        <div class="spinner"></div>
        <p>Chargement...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error-card">
        <span class="error-icon">&#9888;&#65039;</span>
        <h2>Demande introuvable</h2>
        <p>{{ error }}</p>
        <router-link to="/suivi" class="btn btn-primary">Réessayer</router-link>
      </div>

      <!-- Content -->
      <div v-else-if="demande" class="detail-content">
        <!-- Header -->
        <div class="detail-header" :style="{ '--status-color': statutInfo?.color }">
          <div class="numero-box">
            <span class="label">Demande n°</span>
            <span class="numero">{{ demande.numero_suivi }}</span>
          </div>
          <div class="status-badge">
            <span v-html="statutInfo?.icon"></span>
            {{ statutInfo?.label }}
          </div>
        </div>

        <!-- Progress -->
        <div class="progress-section">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <div class="progress-label">Avancement : {{ progressPercent }}%</div>
        </div>

        <!-- Details -->
        <div class="detail-card">
          <h3>Détails du signalement</h3>

          <div class="detail-row">
            <span class="detail-label">Catégorie</span>
            <span class="detail-value">{{ demande.categorie_nom }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">Description</span>
            <span class="detail-value">{{ demande.description }}</span>
          </div>

          <div v-if="demande.adresse_approximative" class="detail-row">
            <span class="detail-label">Localisation</span>
            <span class="detail-value">{{ demande.adresse_approximative }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">Date de création</span>
            <span class="detail-value">{{ formatDate(demande.created_at) }}</span>
          </div>

          <div v-if="demande.date_prise_en_charge" class="detail-row">
            <span class="detail-label">Prise en charge</span>
            <span class="detail-value">{{ formatDate(demande.date_prise_en_charge) }}</span>
          </div>

          <div v-if="demande.date_planification" class="detail-row">
            <span class="detail-label">Intervention prévue</span>
            <span class="detail-value highlight">{{ formatDate(demande.date_planification) }}</span>
          </div>

          <div v-if="demande.date_resolution" class="detail-row">
            <span class="detail-label">Résolution</span>
            <span class="detail-value success">{{ formatDate(demande.date_resolution) }}</span>
          </div>
        </div>

        <!-- Historique -->
        <div v-if="demande.historique?.length" class="historique-card">
          <h3>Historique</h3>

          <div class="timeline">
            <div
              v-for="entry in demande.historique"
              :key="entry.id"
              class="timeline-item"
            >
              <div class="timeline-marker"></div>
              <div class="timeline-content">
                <div class="timeline-date">{{ formatDateShort(entry.created_at) }}</div>
                <div class="timeline-title">
                  {{ entry.action === 'creation' ? 'Signalement créé' :
                     entry.action === 'changement_statut' ? `Statut: ${entry.nouveau_statut}` :
                     'Mise à jour' }}
                </div>
                <div v-if="entry.commentaire" class="timeline-comment">
                  {{ entry.commentaire }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="actions">
          <router-link to="/suivi" class="btn btn-outline">
            &#8592; Nouvelle recherche
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.suivi-detail-page {
  padding: 2rem;
  min-height: 100%;
}

.container {
  max-width: 700px;
  margin: 0 auto;
}

/* Loading & Error */
.loading-card,
.error-card {
  background: white;
  border-radius: 16px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: var(--primary-color, #2563eb);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.error-card h2 {
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.error-card p {
  color: #6b7280;
  margin-bottom: 1.5rem;
}

/* Header */
.detail-header {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
}

.numero-box .label {
  display: block;
  font-size: 0.8rem;
  color: #6b7280;
}

.numero-box .numero {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  font-family: monospace;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--status-color, #6b7280);
  color: white;
  border-radius: 9999px;
  font-weight: 600;
  font-size: 0.9rem;
}

/* Progress */
.progress-section {
  background: white;
  border-radius: 12px;
  padding: 1rem 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color, #2563eb), #10b981);
  transition: width 0.5s ease;
}

.progress-label {
  font-size: 0.85rem;
  color: #6b7280;
  margin-top: 0.5rem;
  text-align: right;
}

/* Detail Card */
.detail-card,
.historique-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
}

.detail-card h3,
.historique-card h3 {
  color: #1f2937;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.detail-row {
  display: flex;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  flex: 0 0 140px;
  font-weight: 500;
  color: #6b7280;
  font-size: 0.9rem;
}

.detail-value {
  flex: 1;
  color: #1f2937;
}

.detail-value.highlight {
  color: var(--primary-color, #2563eb);
  font-weight: 500;
}

.detail-value.success {
  color: #059669;
  font-weight: 500;
}

/* Timeline */
.timeline {
  position: relative;
  padding-left: 24px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e5e7eb;
}

.timeline-item {
  position: relative;
  padding-bottom: 1.25rem;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-marker {
  position: absolute;
  left: -24px;
  top: 0;
  width: 14px;
  height: 14px;
  background: var(--primary-color, #2563eb);
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 0 0 2px var(--primary-color, #2563eb);
}

.timeline-date {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.timeline-title {
  font-weight: 500;
  color: #1f2937;
}

.timeline-comment {
  font-size: 0.9rem;
  color: #6b7280;
  margin-top: 0.25rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 6px;
}

/* Actions */
.actions {
  margin-top: 1.5rem;
}

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

.btn-outline {
  background: transparent;
  color: var(--primary-color, #2563eb);
  border: 2px solid var(--primary-color, #2563eb);
}

.btn-outline:hover {
  background: var(--primary-color, #2563eb);
  color: white;
}

@media (max-width: 640px) {
  .detail-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .detail-row {
    flex-direction: column;
    gap: 0.25rem;
  }

  .detail-label {
    flex: none;
  }
}
</style>

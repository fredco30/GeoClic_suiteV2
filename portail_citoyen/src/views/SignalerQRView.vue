<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useConfigStore } from '@/stores/config'
import { api, type Equipement } from '@/services/api'

const route = useRoute()
const router = useRouter()
const configStore = useConfigStore()

const equipement = ref<Equipement | null>(null)
const loading = ref(true)
const error = ref('')

const equipementId = route.params.equipementId as string

async function loadEquipement() {
  if (!configStore.projectId) {
    error.value = 'Configuration non chargée'
    loading.value = false
    return
  }

  try {
    equipement.value = await api.getEquipement(configStore.projectId, equipementId)
  } catch (err) {
    error.value = 'Équipement non trouvé'
  } finally {
    loading.value = false
  }
}

function continuerSignalement() {
  // Store equipment info and redirect to signaler
  sessionStorage.setItem('equipement_id', equipementId)
  if (equipement.value) {
    sessionStorage.setItem('equipement_nom', equipement.value.nom)
    if (equipement.value.coordonnees) {
      sessionStorage.setItem('equipement_coords', JSON.stringify(equipement.value.coordonnees))
    }
  }
  router.push('/signaler')
}

onMounted(() => {
  loadEquipement()
})
</script>

<template>
  <div class="signaler-qr-page">
    <div class="container">
      <!-- Loading -->
      <div v-if="loading" class="loading-card">
        <div class="spinner"></div>
        <p>Chargement de l'équipement...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error-card">
        <span class="error-icon">&#9888;&#65039;</span>
        <h2>Équipement non trouvé</h2>
        <p>Le QR code scanné ne correspond à aucun équipement connu.</p>
        <router-link to="/signaler" class="btn btn-primary">
          Faire un signalement libre
        </router-link>
      </div>

      <!-- Equipement found -->
      <div v-else-if="equipement" class="equipement-card">
        <div class="card-header">
          <span class="qr-icon">&#128204;</span>
          <h1>Signaler un problème</h1>
        </div>

        <div class="equipement-info">
          <div class="info-label">Équipement identifié</div>
          <div class="equipement-name">{{ equipement.nom }}</div>
          <div class="equipement-type">{{ equipement.type_nom }}</div>
          <div v-if="equipement.adresse" class="equipement-adresse">
            &#128205; {{ equipement.adresse }}
          </div>
        </div>

        <div class="actions">
          <p class="action-text">
            Vous allez signaler un problème concernant cet équipement.
            La localisation sera automatiquement renseignée.
          </p>
          <button @click="continuerSignalement" class="btn btn-primary btn-large">
            Continuer le signalement
          </button>
          <router-link to="/signaler" class="btn btn-outline">
            Signaler autre chose
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.signaler-qr-page {
  padding: 2rem;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.container {
  max-width: 500px;
  width: 100%;
}

.loading-card,
.error-card,
.equipement-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
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

.error-icon,
.qr-icon {
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

.card-header {
  margin-bottom: 1.5rem;
}

.card-header h1 {
  color: #1f2937;
  font-size: 1.5rem;
}

.equipement-info {
  background: #f0f9ff;
  border: 2px solid #bae6fd;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.info-label {
  font-size: 0.8rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.equipement-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0369a1;
  margin-bottom: 0.25rem;
}

.equipement-type {
  color: #0284c7;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.equipement-adresse {
  font-size: 0.9rem;
  color: #6b7280;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.action-text {
  color: #6b7280;
  font-size: 0.95rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
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

.btn-large {
  padding: 1rem 2rem;
}

.btn-primary {
  background: var(--primary-color, #2563eb);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
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
</style>

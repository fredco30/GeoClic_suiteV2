<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const numeroSuivi = ref('')
const email = ref('')
const error = ref('')
const loading = ref(false)

async function rechercher() {
  if (!numeroSuivi.value.trim()) {
    error.value = 'Veuillez entrer un numéro de suivi'
    return
  }

  if (!email.value.includes('@')) {
    error.value = 'Veuillez entrer une adresse email valide'
    return
  }

  error.value = ''
  loading.value = true

  // Store email in sessionStorage for detail page
  sessionStorage.setItem('suivi_email', email.value)

  // Navigate to detail page
  router.push(`/suivi/${numeroSuivi.value.trim()}`)
}
</script>

<template>
  <div class="suivi-page">
    <div class="container">
      <div class="suivi-card">
        <div class="suivi-header">
          <span class="header-icon">&#128269;</span>
          <div class="header-text">
            <h1>Suivre ma demande</h1>
            <p>Entrez votre numéro de suivi et email pour consulter l'avancement.</p>
          </div>
        </div>

        <form @submit.prevent="rechercher" class="suivi-form">
          <div class="form-group">
            <label for="numero">Numéro de suivi</label>
            <input
              id="numero"
              v-model="numeroSuivi"
              type="text"
              placeholder="Ex: SIG-2024-000001"
              autocomplete="off"
            />
          </div>

          <div class="form-group">
            <label for="email">Email utilisé lors du signalement</label>
            <input
              id="email"
              v-model="email"
              type="email"
              placeholder="votre@email.fr"
            />
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <button type="submit" :disabled="loading" class="btn btn-primary btn-block">
            <span v-if="loading">Recherche...</span>
            <span v-else>Rechercher</span>
          </button>
        </form>

        <div class="help-section">
          <h3>Où trouver mon numéro de suivi ?</h3>
          <p>Votre numéro de suivi vous a été communiqué :</p>
          <ul>
            <li>Sur la page de confirmation après votre signalement</li>
            <li>Dans l'email de confirmation envoyé à votre adresse</li>
          </ul>
          <p class="help-note">
            Le numéro ressemble à : <code>SIG-2024-000001</code>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.suivi-page {
  padding: 2rem;
  min-height: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.container {
  max-width: 500px;
  width: 100%;
}

.suivi-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.suivi-header {
  background: linear-gradient(135deg, var(--primary-color, #2563eb) 0%, #1d4ed8 100%);
  color: white;
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.header-text {
  flex: 1;
}

.suivi-header h1 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
}

.suivi-header p {
  opacity: 0.9;
  font-size: 0.85rem;
  margin: 0;
  line-height: 1.3;
}

.suivi-form {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-group input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary-color, #2563eb);
}

.error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
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

.btn-block {
  width: 100%;
}

.help-section {
  padding: 1.5rem 2rem 2rem;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.help-section h3 {
  color: #374151;
  font-size: 0.95rem;
  margin-bottom: 0.75rem;
}

.help-section p {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.help-section ul {
  color: #6b7280;
  font-size: 0.9rem;
  padding-left: 1.25rem;
  margin-bottom: 1rem;
}

.help-section li {
  margin-bottom: 0.25rem;
}

.help-note {
  background: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.help-note code {
  background: #f3f4f6;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9rem;
}
</style>

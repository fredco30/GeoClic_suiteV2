<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const showPassword = ref(false)

async function handleLogin() {
  if (!email.value || !password.value) return

  const success = await authStore.login(email.value, password.value)
  if (success) {
    router.push('/dashboard')
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="login-logo">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
          </svg>
        </div>
        <h1>GeoClic Services</h1>
        <p>Connectez-vous pour accéder aux demandes de votre service</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div v-if="authStore.error" class="alert alert-error">
          {{ authStore.error }}
        </div>

        <div class="form-group">
          <label class="form-label">Email</label>
          <input
            v-model="email"
            type="email"
            class="form-input"
            placeholder="votre@email.fr"
            autocomplete="email"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">Mot de passe</label>
          <div class="password-input">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              placeholder="Votre mot de passe"
              autocomplete="current-password"
              required
            />
            <button
              type="button"
              class="password-toggle"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? 'Masquer' : 'Afficher' }}
            </button>
          </div>
        </div>

        <button
          type="submit"
          class="btn btn-primary btn-lg login-btn"
          :disabled="authStore.loading || !email || !password"
        >
          <span v-if="authStore.loading" class="spinner"></span>
          <span v-else>Se connecter</span>
        </button>
      </form>

      <div class="login-footer">
        <p>
          Mot de passe oublié ?
          <a href="#">Contactez votre responsable</a>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  padding: 1rem;
}

.login-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  padding: 2.5rem;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-logo {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  color: white;
}

.login-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: 0.5rem;
}

.login-header p {
  color: var(--gray-500);
  font-size: 0.875rem;
}

.login-form {
  margin-bottom: 1.5rem;
}

.password-input {
  position: relative;
}

.password-input .form-input {
  padding-right: 80px;
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--primary);
  font-size: 0.8rem;
  cursor: pointer;
}

.login-btn {
  width: 100%;
  margin-top: 1rem;
}

.login-footer {
  text-align: center;
  font-size: 0.875rem;
  color: var(--gray-500);
}

.login-footer a {
  color: var(--primary);
}
</style>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>GéoClic SIG</h1>
        <p>Application cartographique</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="admin@geoclic.local"
            required
            :disabled="loading"
          >
        </div>

        <div class="form-group">
          <label for="password">Mot de passe</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
            :disabled="loading"
          >
        </div>

        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="loading">Connexion...</span>
          <span v-else>Se connecter</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true

  try {
    await authStore.login(email.value, password.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.message || 'Erreur de connexion'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.login-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #1a1a2e;
  margin: 0 0 5px 0;
  font-size: 1.8rem;
}

.login-header p {
  color: #666;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-message {
  background: #fee;
  color: #c00;
  padding: 12px;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #333;
}

.form-group input {
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.login-btn {
  padding: 14px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.login-btn:hover:not(:disabled) {
  background: #2980b9;
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>

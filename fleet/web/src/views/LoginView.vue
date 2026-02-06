<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function login() {
  error.value = ''
  loading.value = true
  try {
    await api.login(email.value, password.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <span class="login-logo">F</span>
        <h1>Fleet Manager</h1>
        <p>Connectez-vous avec votre compte super admin GéoClic</p>
      </div>

      <div v-if="error" class="login-error">{{ error }}</div>

      <div class="form-group">
        <label>Email</label>
        <input
          v-model="email"
          type="email"
          class="input"
          placeholder="admin@geoclic.fr"
          @keyup.enter="login"
        />
      </div>

      <div class="form-group">
        <label>Mot de passe</label>
        <input
          v-model="password"
          type="password"
          class="input"
          placeholder="Votre mot de passe"
          @keyup.enter="login"
        />
      </div>

      <button class="btn btn-primary login-btn" :disabled="loading" @click="login">
        {{ loading ? 'Connexion...' : 'Se connecter' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
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
  margin-bottom: 32px;
}

.login-logo {
  display: inline-flex;
  width: 56px;
  height: 56px;
  background: var(--primary);
  color: white;
  border-radius: 12px;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 800;
  margin-bottom: 16px;
}

.login-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
}

.login-header p {
  font-size: 14px;
  color: var(--text-secondary);
}

.login-error {
  background: #ffebee;
  color: #c62828;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 16px;
}

.login-btn {
  width: 100%;
  padding: 12px;
  font-size: 15px;
  justify-content: center;
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>

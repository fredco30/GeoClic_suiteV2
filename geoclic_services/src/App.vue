<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useTheme } from './composables/useTheme'
import { computed, ref, onMounted, watch } from 'vue'
import axios from 'axios'

const authStore = useAuthStore()
const { isDark, toggleTheme } = useTheme()

const isLoggedIn = computed(() => authStore.isLoggedIn)
const agent = computed(() => authStore.agent)

// Branding centralisé
const brandingName = ref('')

async function loadBranding() {
  try {
    const res = await axios.get('/api/settings/branding')
    if (res.data.nom_collectivite) {
      brandingName.value = res.data.nom_collectivite
    }
    if (res.data.primary_color) {
      document.documentElement.style.setProperty('--primary', res.data.primary_color)
    }
  } catch {
    // Valeurs par défaut conservées
  }
}

onMounted(() => {
  if (isLoggedIn.value) loadBranding()
})

watch(isLoggedIn, (val) => {
  if (val) loadBranding()
})

async function logout() {
  await authStore.logout()
}
</script>

<template>
  <div class="app">
    <!-- Header navigation si connecté -->
    <header v-if="isLoggedIn" class="header">
      <div class="header-content">
        <div class="header-brand">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
          </svg>
          <span class="header-title">{{ brandingName || 'GeoClic' }} Services</span>
        </div>

        <nav class="header-nav">
          <router-link to="/dashboard" class="nav-link">Dashboard</router-link>
          <router-link to="/demandes" class="nav-link">Demandes</router-link>
          <router-link v-if="agent?.role === 'responsable'" to="/agents" class="nav-link">Agents</router-link>
        </nav>

        <div class="header-actions">
          <button @click="toggleTheme" class="btn-theme" :title="isDark ? 'Mode clair' : 'Mode sombre'">
            <svg v-if="isDark" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0 .39-.39.39-1.03 0-1.41l-1.06-1.06zm1.06-10.96c.39-.39.39-1.03 0-1.41-.39-.39-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36c.39-.39.39-1.03 0-1.41-.39-.39-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-.46-.04-.92-.1-1.36-.98 1.37-2.58 2.26-4.4 2.26-2.98 0-5.4-2.42-5.4-5.4 0-1.81.89-3.42 2.26-4.4-.44-.06-.9-.1-1.36-.1z"/>
            </svg>
          </button>
        </div>

        <div class="header-user">
          <div class="user-info">
            <span class="user-name">{{ agent?.nom_complet }}</span>
            <span class="user-service">{{ agent?.service_nom }}</span>
          </div>
          <button @click="logout" class="btn btn-secondary btn-sm">
            Déconnexion
          </button>
        </div>
      </div>
    </header>

    <main :class="{ 'main-with-header': isLoggedIn }">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
}

.header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  transition: background-color 0.3s, border-color 0.3s;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--primary);
}

.header-title {
  font-size: 1.125rem;
  font-weight: 600;
}

.header-nav {
  display: flex;
  gap: 0.5rem;
}

.nav-link {
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  color: var(--gray-600);
  font-weight: 500;
  transition: all 0.2s;
}

.nav-link:hover {
  background: var(--bg-primary);
  text-decoration: none;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-theme {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius);
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-theme:hover {
  background: var(--border-color);
  color: var(--text-primary);
}

.nav-link.router-link-active {
  background: var(--primary);
  color: white;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info {
  text-align: right;
}

.user-name {
  display: block;
  font-weight: 500;
  font-size: 0.875rem;
}

.user-service {
  display: block;
  font-size: 0.75rem;
  color: var(--gray-500);
}

.main-with-header {
  padding-top: 60px;
}
</style>

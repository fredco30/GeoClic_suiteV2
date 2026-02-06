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
const isOnline = ref(navigator.onLine)

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

// Écouter les changements de connexion
window.addEventListener('online', () => isOnline.value = true)
window.addEventListener('offline', () => isOnline.value = false)

async function logout() {
  await authStore.logout()
}
</script>

<template>
  <div class="app">
    <!-- Bandeau hors-ligne -->
    <div v-if="!isOnline" class="offline-banner">
      Mode hors-ligne
    </div>

    <!-- Header simplifié mobile -->
    <header v-if="isLoggedIn" class="header" :class="{ 'header-offline': !isOnline }">
      <div class="header-content">
        <div class="header-brand">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
          </svg>
          <span class="header-title">{{ brandingName || 'GeoClic' }} Mobile</span>
        </div>

        <div class="header-user">
          <span class="user-name">{{ agent?.nom_complet?.split(' ')[0] }}</span>
          <button @click="toggleTheme" class="btn-theme" :title="isDark ? 'Mode clair' : 'Mode sombre'">
            <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1z"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-.46-.04-.92-.1-1.36-.98 1.37-2.58 2.26-4.4 2.26-2.98 0-5.4-2.42-5.4-5.4 0-1.81.89-3.42 2.26-4.4-.44-.06-.9-.1-1.36-.1z"/>
            </svg>
          </button>
          <button @click="logout" class="btn-logout" title="Déconnexion">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main :class="{ 'main-with-header': isLoggedIn, 'main-offline': !isOnline && isLoggedIn }">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  min-height: 100dvh;
}

/* Bandeau hors-ligne */
.offline-banner {
  background: #f97316;
  color: white;
  text-align: center;
  padding: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 200;
}

/* Header */
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

.header-offline {
  top: 32px;
}

.header-content {
  padding: 0 1rem;
  height: 52px;
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
  font-size: 1rem;
  font-weight: 600;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-name {
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--gray-700);
}

.btn-logout {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: var(--gray-500);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.15s;
}

.btn-logout:hover {
  background: var(--gray-100);
  color: var(--gray-700);
}

.btn-logout:active {
  transform: scale(0.95);
}

.btn-theme {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.15s;
}

.btn-theme:hover {
  background: var(--bg-primary);
  color: var(--text-primary);
}

.btn-theme:active {
  transform: scale(0.95);
}

/* Main */
.main-with-header {
  padding-top: 52px;
}

.main-offline {
  padding-top: 84px;
}
</style>

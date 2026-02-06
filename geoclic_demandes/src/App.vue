<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useDemandesStore } from './stores/demandes'
import HelpDrawer from '@/components/help/HelpDrawer.vue'
import ToastContainer from '@/components/ToastContainer.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const demandesStore = useDemandesStore()

const showSidebar = computed(() => authStore.isAuthenticated && route.name !== 'login')

// Branding chargé depuis l'API centralisée
const brandingName = ref('')
const brandingLogo = ref('')

const menuItems = [
  { name: 'dashboard', label: 'Tableau de bord', icon: '&#128200;', path: '/' },
  { name: 'demandes', label: 'Demandes', icon: '&#128203;', path: '/demandes', badge: () => demandesStore.countNouvelles },
  { name: 'carte', label: 'Carte', icon: '&#128506;', path: '/carte' },
  { name: 'categories', label: 'Catégories', icon: '&#128193;', path: '/categories' },
  { name: 'services', label: 'Services', icon: '&#127970;', path: '/services' },
  { name: 'templates', label: 'Templates', icon: '&#128221;', path: '/templates' },
  { name: 'statistiques', label: 'Statistiques', icon: '&#128202;', path: '/statistiques' },
  { name: 'parametres', label: 'Paramètres', icon: '&#9881;', path: '/parametres' },
]

function logout() {
  authStore.logout()
  router.push('/login')
}

async function loadBranding() {
  try {
    const res = await axios.get('/api/settings/branding')
    if (res.data.nom_collectivite) {
      brandingName.value = res.data.nom_collectivite
    }
    if (res.data.logo_url) {
      brandingLogo.value = res.data.logo_url
    }
    // Appliquer les couleurs si configurées
    if (res.data.primary_color) {
      document.documentElement.style.setProperty('--primary-color', res.data.primary_color)
    }
    if (res.data.sidebar_color) {
      document.documentElement.style.setProperty('--sidebar-color', res.data.sidebar_color)
    }
    return res.data
  } catch {
    // Pas grave, on garde les valeurs par défaut
    return null
  }
}

// Charger le branding après connexion
watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth) loadBranding()
})

onMounted(() => {
  if (authStore.isAuthenticated) loadBranding()
})
</script>

<template>
  <div class="app" :class="{ 'with-sidebar': showSidebar }">
    <!-- Sidebar -->
    <aside v-if="showSidebar" class="sidebar">
      <div class="sidebar-header">
        <img v-if="brandingLogo" :src="brandingLogo" alt="Logo" class="sidebar-logo" />
        <h1>{{ brandingName || 'GéoClic' }}</h1>
        <span class="subtitle">Demandes</span>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.name"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.name === item.name }"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.badge && item.badge() > 0" class="nav-badge">
            {{ item.badge() }}
          </span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <span class="user-avatar">{{ authStore.user?.name?.[0] || 'U' }}</span>
          <div class="user-details">
            <span class="user-name">{{ authStore.user?.name || 'Utilisateur' }}</span>
            <span class="user-role">{{ authStore.user?.role || 'Agent' }}</span>
          </div>
        </div>
        <button @click="logout" class="logout-btn" title="Déconnexion">
          &#128682;
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <Breadcrumbs v-if="showSidebar" />
      <router-view />
    </main>

    <!-- Aide contextuelle globale -->
    <HelpDrawer />

    <!-- Notifications toast -->
    <ToastContainer />
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  background: #f3f4f6;
}

.app.with-sidebar {
  display: flex;
}

/* Sidebar */
.sidebar {
  width: 260px;
  background: var(--sidebar-color, #1f2937);
  color: white;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-logo {
  height: 32px;
  width: auto;
  max-width: 160px;
  object-fit: contain;
  margin-bottom: 0.25rem;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
}

.sidebar-header .subtitle {
  font-size: 0.8rem;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.sidebar-nav {
  flex: 1;
  padding: 1rem 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  color: #9ca3af;
  text-decoration: none;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-left-color: var(--primary-color, #3b82f6);
}

.nav-icon {
  font-size: 1.25rem;
  width: 24px;
  text-align: center;
}

.nav-label {
  flex: 1;
}

.nav-badge {
  background: #ef4444;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
}

.sidebar-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: var(--primary-color, #3b82f6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 500;
}

.user-role {
  font-size: 0.75rem;
  color: #9ca3af;
}

.logout-btn {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

/* Main Content */
.main-content {
  flex: 1;
  min-height: 100vh;
}

.with-sidebar .main-content {
  margin-left: 260px;
}

@media (max-width: 1024px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s;
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .with-sidebar .main-content {
    margin-left: 0;
  }
}
</style>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1>{{ brandingName || 'GéoClic' }} SIG</h1>
      <span class="version">v1.0</span>
    </div>

    <nav class="sidebar-nav">
      <router-link to="/" class="nav-item" :class="{ active: $route.name === 'map' }">
        <span class="icon">🗺️</span>
        <span>Carte</span>
      </router-link>
      <router-link to="/projects" class="nav-item" :class="{ active: $route.name === 'projects' }">
        <span class="icon">📁</span>
        <span>Projets</span>
      </router-link>
      <router-link to="/import" class="nav-item" :class="{ active: $route.name === 'import' }">
        <span class="icon">📥</span>
        <span>Import</span>
      </router-link>
    </nav>

    <!-- Couches -->
    <div class="sidebar-section" v-if="mapStore.layers.length > 0">
      <h3>Couches</h3>
      <div class="layers-list">
        <div
          v-for="layer in mapStore.layers"
          :key="layer.id"
          class="layer-item"
        >
          <label class="layer-toggle">
            <input
              type="checkbox"
              :checked="layer.visible"
              @change="mapStore.toggleLayerVisibility(layer.id)"
            >
            <span
              class="layer-color"
              :style="{ backgroundColor: layer.color }"
            ></span>
            <span class="layer-name">{{ layer.name }}</span>
            <span class="layer-count">
              {{ layer.data?.features?.length || 0 }}
            </span>
          </label>
        </div>
      </div>
    </div>

    <!-- Projet actuel -->
    <div class="sidebar-section" v-if="mapStore.currentProject">
      <h3>Projet actif</h3>
      <div class="current-project">
        <strong>{{ mapStore.currentProject.name }}</strong>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="user-info">
        <span class="user-name">{{ authStore.fullName }}</span>
        <span class="user-role">{{ authStore.user?.is_super_admin ? 'Super Admin' : authStore.user?.role_sig }}</span>
      </div>
      <button @click="handleLogout" class="logout-btn">
        Déconnexion
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useMapStore } from '../stores/map'

defineProps<{
  brandingName?: string
}>()

const router = useRouter()
const authStore = useAuthStore()
const mapStore = useMapStore()

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  background: #1a1a2e;
  color: white;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar-header {
  padding: 20px;
  background: #16213e;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-header h1 {
  font-size: 1.3rem;
  margin: 0;
}

.version {
  font-size: 0.75rem;
  opacity: 0.6;
}

.sidebar-nav {
  padding: 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  color: #ccc;
  text-decoration: none;
  border-radius: 8px;
  margin-bottom: 5px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: #3498db;
  color: white;
}

.icon {
  font-size: 1.2rem;
}

.sidebar-section {
  padding: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-section h3 {
  font-size: 0.8rem;
  text-transform: uppercase;
  opacity: 0.6;
  margin-bottom: 10px;
}

.layers-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.layer-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  padding: 8px 10px;
}

.layer-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.9rem;
}

.layer-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.layer-name {
  flex: 1;
}

.layer-count {
  font-size: 0.75rem;
  opacity: 0.6;
}

.current-project {
  background: rgba(52, 152, 219, 0.2);
  padding: 10px;
  border-radius: 6px;
  font-size: 0.9rem;
}

.sidebar-footer {
  margin-top: auto;
  padding: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
}

.user-name {
  font-weight: 500;
}

.user-role {
  font-size: 0.8rem;
  opacity: 0.6;
  text-transform: capitalize;
}

.logout-btn {
  width: 100%;
  padding: 10px;
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: rgba(231, 76, 60, 0.4);
}
</style>

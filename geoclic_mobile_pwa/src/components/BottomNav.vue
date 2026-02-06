<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePointsStore } from '@/stores/points'
import { useTheme } from '@/composables/useTheme'

const route = useRoute()
const router = useRouter()
const pointsStore = usePointsStore()
const { isDark, toggleTheme } = useTheme()

const navItems = [
  { path: '/', icon: '🏠', label: 'Accueil' },
  { path: '/points', icon: '📋', label: 'Points' },
  { path: '/map', icon: '🗺️', label: 'Carte' },
  { path: '/sync', icon: '🔄', label: 'Sync' }
]

const isActive = (path: string) => route.path === path

const pendingCount = computed(() => pointsStore.pendingCount)
const isOnline = computed(() => pointsStore.isOnline)
</script>

<template>
  <nav class="bottom-nav">
    <button
      v-for="item in navItems"
      :key="item.path"
      class="nav-item"
      :class="{ active: isActive(item.path) }"
      @click="router.push(item.path)"
    >
      <span class="nav-icon">
        {{ item.icon }}
        <span
          v-if="item.path === '/sync' && pendingCount > 0"
          class="badge-count"
        >
          {{ pendingCount > 99 ? '99+' : pendingCount }}
        </span>
      </span>
      <span class="nav-label">{{ item.label }}</span>
    </button>

    <!-- Bouton thème -->
    <button class="nav-item theme-toggle" @click="toggleTheme" :title="isDark ? 'Mode clair' : 'Mode sombre'">
      <span class="nav-icon">{{ isDark ? '☀️' : '🌙' }}</span>
      <span class="nav-label">{{ isDark ? 'Clair' : 'Sombre' }}</span>
    </button>

    <!-- Indicateur hors-ligne -->
    <div v-if="!isOnline" class="offline-dot" title="Mode hors-ligne"></div>
  </nav>
</template>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(var(--bottom-nav-height) + var(--safe-area-inset-bottom));
  padding-bottom: var(--safe-area-inset-bottom);
  background: var(--surface-color);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 100;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 0;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.nav-item.active {
  color: var(--primary-color);
}

.nav-icon {
  position: relative;
  font-size: 22px;
  line-height: 1;
}

.badge-count {
  position: absolute;
  top: -6px;
  right: -10px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--error-color);
  color: white;
  font-size: 10px;
  font-weight: bold;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-label {
  font-size: 11px;
  font-weight: 500;
}

.offline-dot {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  background: var(--warning-color);
  border-radius: 50%;
  animation: pulse 2s infinite;
}
</style>

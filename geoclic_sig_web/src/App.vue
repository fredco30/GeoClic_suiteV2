<template>
  <div class="app-container">
    <Sidebar v-if="authStore.isAuthenticated" :branding-name="brandingName" />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useAuthStore } from './stores/auth'
import Sidebar from './components/Sidebar.vue'
import axios from 'axios'

const authStore = useAuthStore()

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
  if (authStore.isAuthenticated) loadBranding()
})

watch(() => authStore.isAuthenticated, (val) => {
  if (val) loadBranding()
})
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style>

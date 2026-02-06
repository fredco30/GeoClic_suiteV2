<script setup lang="ts">
import { useConfigStore } from './stores/config'
import { onMounted } from 'vue'

const configStore = useConfigStore()

onMounted(async () => {
  await configStore.loadConfig()
})
</script>

<template>
  <div class="app" :style="{ '--primary-color': configStore.theme.primaryColor }">
    <!-- Header -->
    <header class="header">
      <div class="header-content">
        <router-link to="/" class="logo">
          <img v-if="configStore.theme.logo" :src="configStore.theme.logo" alt="Logo" class="logo-img" />
          <span class="logo-text">{{ configStore.collectiviteName || 'Portail Citoyen' }}</span>
        </router-link>
        <nav class="nav">
          <router-link to="/" class="nav-link">Accueil</router-link>
          <router-link to="/signaler" class="nav-link nav-link-primary">Signaler</router-link>
          <router-link to="/suivi" class="nav-link">Suivi</router-link>
          <router-link to="/carte" class="nav-link">Carte</router-link>
        </nav>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-content">
        <p>&copy; {{ new Date().getFullYear() }} {{ configStore.collectiviteName }} - Propulsé par GéoClic Suite</p>
        <div class="footer-links">
          <router-link to="/faq">FAQ</router-link>
          <a href="#">Mentions légales</a>
          <a href="#">Contact</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: var(--bg-secondary);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  transition: background-color 0.3s;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: var(--primary-color, #2563eb);
  font-weight: 700;
  font-size: 1.25rem;
}

.logo-img {
  height: 40px;
  width: auto;
}

.nav {
  display: flex;
  gap: 1rem;
}

.nav-link {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  transition: all 0.2s;
}

.nav-link:hover {
  background: var(--bg-tertiary);
}

.nav-link.router-link-active {
  color: var(--primary-color, #2563eb);
}

.nav-link-primary {
  background: var(--primary-color, #2563eb);
  color: white !important;
}

.nav-link-primary:hover {
  background: var(--primary-color, #2563eb);
  opacity: 0.9;
}

.main {
  flex: 1;
  background: var(--bg-primary);
  transition: background-color 0.3s;
}

.footer {
  background: var(--footer-bg);
  color: var(--footer-text);
  padding: 2rem;
  transition: background-color 0.3s;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-links {
  display: flex;
  gap: 1.5rem;
}

.footer-links a {
  color: var(--footer-text);
  text-decoration: none;
}

.footer-links a:hover {
  color: white;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }

  .nav {
    flex-wrap: wrap;
    justify-content: center;
  }

  .footer-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
}
</style>

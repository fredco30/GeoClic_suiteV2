<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const isLoggedIn = computed(() => !!localStorage.getItem('fleet_auth_token'))
const isLoginPage = computed(() => route.name === 'login')

function logout() {
  localStorage.removeItem('fleet_auth_token')
  router.push('/login')
}
</script>

<template>
  <div class="app">
    <header v-if="!isLoginPage && isLoggedIn" class="header">
      <div class="header-left">
        <router-link to="/" class="logo">
          <span class="logo-icon">F</span>
          <span class="logo-text">Fleet Manager</span>
        </router-link>
      </div>
      <nav class="header-nav">
        <router-link to="/" class="nav-link" :class="{ active: route.name === 'dashboard' }">
          Dashboard
        </router-link>
        <router-link to="/add" class="nav-link" :class="{ active: route.name === 'add-server' }">
          + Ajouter
        </router-link>
        <router-link to="/help" class="nav-link" :class="{ active: route.name === 'help' }">
          Aide
        </router-link>
      </nav>
      <div class="header-right">
        <a href="/admin/" class="nav-link back-link" target="_blank">GéoClic Admin</a>
        <button class="btn-logout" @click="logout">Déconnexion</button>
      </div>
    </header>

    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary: #1a237e;
  --primary-light: #3949ab;
  --primary-dark: #0d1642;
  --accent: #00c853;
  --danger: #d32f2f;
  --warning: #ff9800;
  --bg: #f5f5f5;
  --card: #ffffff;
  --text: #212121;
  --text-secondary: #757575;
  --border: #e0e0e0;
  --radius: 8px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: var(--primary);
  color: white;
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: white;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: white;
  color: var(--primary);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 18px;
}

.logo-text {
  font-weight: 600;
  font-size: 16px;
  letter-spacing: -0.3px;
}

.header-nav {
  display: flex;
  gap: 4px;
  flex: 1;
}

.nav-link {
  color: rgba(255, 255, 255, 0.75);
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-link.active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-link {
  font-size: 13px;
}

.btn-logout {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-logout:hover {
  background: rgba(255, 255, 255, 0.25);
}

.main {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

/* Utilitaires */
.card {
  background: var(--card);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 20px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-light);
}

.btn-accent {
  background: var(--accent);
  color: white;
}

.btn-accent:hover {
  background: #00b848;
}

.btn-danger {
  background: var(--danger);
  color: white;
}

.btn-danger:hover {
  background: #b71c1c;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.btn-outline:hover {
  background: var(--bg);
}

.btn-sm {
  padding: 4px 10px;
  font-size: 13px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.badge-ok {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-error {
  background: #ffebee;
  color: #c62828;
}

.badge-warn {
  background: #fff3e0;
  color: #e65100;
}

.input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(26, 35, 126, 0.1);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>

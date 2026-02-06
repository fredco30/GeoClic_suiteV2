<template>
  <v-app>
    <!-- App Bar -->
    <v-app-bar color="primary" density="comfortable">
      <v-app-bar-nav-icon @click="drawer = !drawer" />

      <v-toolbar-title class="font-weight-bold d-flex align-center">
        <img v-if="brandingLogo" :src="brandingLogo" alt="Logo" height="32" class="mr-2" />
        <img v-else src="@/assets/logo.png" alt="GéoClic" height="32" class="mr-2" />
        {{ brandingName || 'GéoClic' }} Data
      </v-toolbar-title>

      <v-spacer />

      <!-- Recherche globale -->
      <v-text-field
        v-model="globalSearch"
        density="compact"
        variant="solo-filled"
        flat
        hide-details
        placeholder="Rechercher..."
        prepend-inner-icon="mdi-magnify"
        class="mx-4"
        style="max-width: 300px"
        @keyup.enter="doGlobalSearch"
      />

      <!-- Notifications -->
      <v-btn icon class="mr-2">
        <v-badge color="error" :content="notifications" :model-value="notifications > 0">
          <v-icon>mdi-bell-outline</v-icon>
        </v-badge>
      </v-btn>

      <!-- Thème -->
      <v-btn icon @click="toggleTheme">
        <v-icon>{{ isDark ? 'mdi-white-balance-sunny' : 'mdi-moon-waning-crescent' }}</v-icon>
      </v-btn>

      <!-- Menu utilisateur -->
      <v-menu offset-y>
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" variant="text" class="ml-2">
            <v-avatar color="secondary" size="32" class="mr-2">
              <span class="text-white text-body-2">{{ userInitials }}</span>
            </v-avatar>
            <span class="d-none d-md-inline">{{ userName }}</span>
            <v-icon end>mdi-chevron-down</v-icon>
          </v-btn>
        </template>

        <v-list density="compact">
          <v-list-item prepend-icon="mdi-account" title="Mon profil" to="/profil" />
          <v-list-item prepend-icon="mdi-cog" title="Paramètres" to="/parametres" />
          <v-divider />
          <v-list-item prepend-icon="mdi-logout" title="Déconnexion" @click="logout" />
        </v-list>
      </v-menu>
    </v-app-bar>

    <!-- Navigation Drawer -->
    <v-navigation-drawer v-model="drawer" :rail="rail" permanent @click="rail = false">
      <v-list density="compact" nav>
        <!-- Dashboard -->
        <v-list-item
          prepend-icon="mdi-view-dashboard"
          title="Tableau de bord"
          value="dashboard"
          to="/"
          :active="$route.path === '/'"
        />

        <v-divider class="my-2" />

        <!-- Données -->
        <v-list-subheader v-if="!rail">DONNÉES</v-list-subheader>

        <v-list-item
          prepend-icon="mdi-map-marker"
          title="Points"
          value="points"
          to="/points"
        />

        <v-list-item
          prepend-icon="mdi-map"
          title="Cartographie"
          value="carte"
          to="/carte"
        />

        <v-divider class="my-2" />

        <!-- Configuration -->
        <v-list-subheader v-if="!rail">CONFIGURATION</v-list-subheader>

        <v-list-item
          prepend-icon="mdi-folder-cog"
          title="Projets"
          subtitle="Structure et champs"
          value="projets"
          to="/projets"
        />

        <v-list-item
          prepend-icon="mdi-folder-eye"
          title="Lexique"
          subtitle="Vue globale"
          value="lexique"
          to="/lexique"
        />

        <v-list-item
          prepend-icon="mdi-map-marker-radius"
          title="Zones"
          subtitle="Quartiers et secteurs"
          value="zones"
          to="/zones"
        />

        <v-divider class="my-2" />

        <!-- Administration -->
        <v-list-subheader v-if="!rail">ADMINISTRATION</v-list-subheader>

        <v-list-item
          v-if="isAdmin"
          prepend-icon="mdi-account-group"
          title="Utilisateurs"
          value="utilisateurs"
          to="/utilisateurs"
        />

        <v-list-item
          prepend-icon="mdi-qrcode"
          title="QR Codes"
          value="qrcodes"
          to="/qrcodes"
        />

        <v-list-item
          prepend-icon="mdi-cloud-upload"
          title="OneGeo Suite"
          value="ogs"
          to="/ogs"
        />

        <v-list-item
          prepend-icon="mdi-file-export"
          title="Exports"
          value="exports"
          to="/exports"
        />
      </v-list>

      <!-- Rail toggle button -->
      <template v-slot:append>
        <div class="pa-2">
          <v-btn
            block
            variant="text"
            :icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
            @click.stop="rail = !rail"
          />
        </div>
      </template>
    </v-navigation-drawer>

    <!-- Main Content -->
    <v-main>
      <v-container fluid class="pa-4">
        <slot />
      </v-container>
    </v-main>

    <!-- Snackbar for notifications -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
      location="bottom right"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">
          Fermer
        </v-btn>
      </template>
    </v-snackbar>

    <!-- Wizard d'onboarding (première configuration) -->
    <OnboardingWizard
      v-if="showOnboarding"
      @complete="onOnboardingComplete"
      @skip="onOnboardingSkip"
    />
  </v-app>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import OnboardingWizard from '@/components/OnboardingWizard.vue'
import axios from 'axios'

const theme = useTheme()
const authStore = useAuthStore()
const router = useRouter()

// Branding centralisé
const brandingName = ref('')
const brandingLogo = ref('')

// Onboarding
const showOnboarding = ref(false)

async function loadBranding() {
  try {
    const res = await axios.get('/api/settings/branding')
    if (res.data.nom_collectivite) {
      brandingName.value = res.data.nom_collectivite
    }
    if (res.data.logo_url) {
      brandingLogo.value = res.data.logo_url
    }
    return res.data
  } catch {
    // Valeurs par défaut conservées
    return null
  }
}

async function checkOnboarding() {
  if (!authStore.isAdmin) return
  if (localStorage.getItem('geoclic_onboarding_complete') === 'true') return
  try {
    const data = await loadBranding()
    if (!data?.nom_collectivite) {
      showOnboarding.value = true
    } else {
      localStorage.setItem('geoclic_onboarding_complete', 'true')
    }
  } catch {
    // Ne pas bloquer
  }
}

function onOnboardingComplete() {
  showOnboarding.value = false
  localStorage.setItem('geoclic_onboarding_complete', 'true')
  window.location.reload()
}

function onOnboardingSkip() {
  showOnboarding.value = false
  localStorage.setItem('geoclic_onboarding_complete', 'true')
}

onMounted(() => {
  loadBranding()
  checkOnboarding()
})

// Navigation
const drawer = ref(true)
const rail = ref(false)
const globalSearch = ref('')

// Theme
const isDark = computed(() => theme.global.current.value.dark)

function toggleTheme() {
  theme.global.name.value = isDark.value ? 'geoclicTheme' : 'geoclicDarkTheme'
}

// User
const userName = computed(() => {
  if (!authStore.user) return 'Utilisateur'
  const { prenom, nom, email } = authStore.user
  if (prenom && nom) return `${prenom} ${nom}`
  if (nom) return nom
  return email || 'Utilisateur'
})

const userInitials = computed(() => {
  if (!authStore.user) return 'U'
  const { prenom, nom, email } = authStore.user
  if (prenom && nom) {
    return `${prenom[0]}${nom[0]}`.toUpperCase()
  }
  if (nom) return nom.substring(0, 2).toUpperCase()
  return (email || 'U').substring(0, 2).toUpperCase()
})

const isAdmin = computed(() => authStore.isAdmin)

// Notifications
const notifications = ref(0)

// Snackbar
const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
})

// Actions
function doGlobalSearch() {
  if (globalSearch.value.trim()) {
    router.push({ path: '/points', query: { search: globalSearch.value } })
  }
}

function logout() {
  authStore.logout()
}

// Expose snackbar for child components
defineExpose({
  showSnackbar(message: string, color: string = 'success') {
    snackbar.value = { show: true, message, color }
  },
})
</script>

<style scoped>
.v-navigation-drawer {
  transition: width 0.2s ease-in-out;
}
</style>

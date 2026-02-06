<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <!-- Header -->
          <v-card-title class="bg-primary text-white pa-6">
            <div class="text-center w-100">
              <v-icon size="64" class="mb-4">mdi-map-marker-multiple</v-icon>
              <h1 class="text-h4 font-weight-bold">GéoClic Data</h1>
              <p class="text-body-2 mt-2 opacity-80">
                Interface d'administration
              </p>
            </div>
          </v-card-title>

          <!-- Form -->
          <v-card-text class="pa-6">
            <v-form ref="form" v-model="valid" @submit.prevent="handleLogin">
              <v-text-field
                v-model="email"
                label="Email"
                prepend-inner-icon="mdi-email"
                type="email"
                :rules="emailRules"
                :disabled="loading"
                autocomplete="email"
                class="mb-4"
              />

              <v-text-field
                v-model="password"
                label="Mot de passe"
                prepend-inner-icon="mdi-lock"
                :type="showPassword ? 'text' : 'password'"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                :rules="passwordRules"
                :disabled="loading"
                autocomplete="current-password"
                @click:append-inner="showPassword = !showPassword"
              />

              <!-- Error message -->
              <v-alert
                v-if="error"
                type="error"
                variant="tonal"
                class="mt-4"
                closable
                @click:close="error = ''"
              >
                {{ error }}
              </v-alert>

              <!-- Submit button -->
              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                :disabled="!valid"
                class="mt-6"
              >
                <v-icon start>mdi-login</v-icon>
                Se connecter
              </v-btn>
            </v-form>
          </v-card-text>

          <!-- Footer -->
          <v-card-actions class="bg-grey-lighten-4 pa-4">
            <HelpButton page-key="login" variant="text" size="sm" />
            <v-spacer />
            <span class="text-caption text-grey">
              GéoClic V12 Pro &copy; {{ new Date().getFullYear() }}
            </span>
            <v-spacer />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HelpButton from '@/components/help/HelpButton.vue'

// Définir le layout
defineOptions({
  meta: {
    layout: 'default',
  },
})

const router = useRouter()
const authStore = useAuthStore()

// Form state
const form = ref()
const valid = ref(false)
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

// Validation rules
const emailRules = [
  (v: string) => !!v || 'Email requis',
  (v: string) => /.+@.+\..+/.test(v) || 'Email invalide',
]

const passwordRules = [
  (v: string) => !!v || 'Mot de passe requis',
  (v: string) => v.length >= 4 || 'Minimum 4 caractères',
]

// Login handler
async function handleLogin() {
  if (!valid.value) return

  loading.value = true
  error.value = ''

  try {
    const success = await authStore.login(email.value, password.value)

    if (success) {
      router.push('/')
    } else {
      error.value = authStore.error || 'Échec de la connexion'
    }
  } catch (err: any) {
    error.value = err.message || 'Erreur de connexion'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
  background: linear-gradient(135deg, #1976D2 0%, #0D47A1 100%);
}
</style>

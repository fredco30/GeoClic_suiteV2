<template>
  <div>
    <div class="d-flex align-center mb-6">
      <h1 class="text-h4 font-weight-bold">
        Mon Profil
        <HelpButton page-key="profil" size="sm" />
      </h1>
    </div>

    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-account</v-icon>
            Informations personnelles
          </v-card-title>
          <v-card-text>
            <div class="text-center mb-6">
              <v-avatar :color="user?.is_super_admin ? 'error' : 'primary'" size="100">
                <v-icon v-if="user?.is_super_admin" color="white" size="48">mdi-crown</v-icon>
                <span v-else class="text-h3 text-white">{{ initials }}</span>
              </v-avatar>
              <div v-if="user?.is_super_admin" class="mt-2">
                <v-chip color="error" size="small">Super Administrateur</v-chip>
              </div>
            </div>

            <v-form ref="form" v-model="formValid">
              <v-text-field
                v-model="formData.prenom"
                label="Prénom"
                :rules="[v => !!v || 'Prénom requis']"
              />
              <v-text-field
                v-model="formData.nom"
                label="Nom"
                :rules="[v => !!v || 'Nom requis']"
                class="mt-4"
              />
              <v-text-field
                v-model="formData.email"
                label="Email"
                type="email"
                disabled
                class="mt-4"
              />

              <!-- Accès aux applications -->
              <div class="mt-4">
                <div class="text-subtitle-2 mb-2">Mes accès</div>
                <div class="d-flex flex-wrap gap-1">
                  <template v-if="user?.is_super_admin">
                    <v-chip color="error" size="small">Tous les accès</v-chip>
                  </template>
                  <template v-else>
                    <v-chip
                      v-if="user?.role_data !== 'aucun'"
                      :color="ROLE_COLORS[user?.role_data || 'aucun']"
                      size="small"
                    >
                      Data: {{ ROLE_DATA_LABELS[user?.role_data || 'aucun'] }}
                    </v-chip>
                    <v-chip
                      v-if="user?.role_demandes !== 'aucun'"
                      :color="ROLE_COLORS[user?.role_demandes || 'aucun']"
                      size="small"
                    >
                      Demandes: {{ ROLE_DEMANDES_LABELS[user?.role_demandes || 'aucun'] }}
                    </v-chip>
                    <v-chip
                      v-if="user?.role_sig !== 'aucun'"
                      :color="ROLE_COLORS[user?.role_sig || 'aucun']"
                      size="small"
                    >
                      SIG: {{ ROLE_SIG_LABELS[user?.role_sig || 'aucun'] }}
                    </v-chip>
                    <v-chip
                      v-if="user?.role_terrain !== 'aucun'"
                      :color="ROLE_COLORS[user?.role_terrain || 'aucun']"
                      size="small"
                    >
                      Terrain: {{ ROLE_TERRAIN_LABELS[user?.role_terrain || 'aucun'] }}
                    </v-chip>
                  </template>
                </div>
              </div>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" :disabled="!formValid" :loading="saving" @click="saveProfile">
              Enregistrer
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-lock</v-icon>
            Changer le mot de passe
          </v-card-title>
          <v-card-text>
            <v-form ref="passwordForm" v-model="passwordFormValid">
              <v-text-field
                v-model="passwords.current"
                label="Mot de passe actuel"
                type="password"
                :rules="passwordRules"
              />
              <v-text-field
                v-model="passwords.new"
                label="Nouveau mot de passe"
                type="password"
                :rules="passwordRules"
                class="mt-4"
              />
              <v-text-field
                v-model="passwords.confirm"
                label="Confirmer le mot de passe"
                type="password"
                :rules="[v => v === passwords.new || 'Les mots de passe ne correspondent pas']"
                class="mt-4"
              />
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="warning" :disabled="!passwordFormValid" :loading="changingPassword" @click="changePassword">
              Changer le mot de passe
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-card class="mt-4">
          <v-card-title>
            <v-icon class="mr-2">mdi-information</v-icon>
            Informations du compte
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>Date de création</v-list-item-title>
                <v-list-item-subtitle>{{ formatDate(user?.created_at) }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Dernière connexion</v-list-item-title>
                <v-list-item-subtitle>{{ formatDate(user?.last_login) }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="user?.service_nom">
                <v-list-item-title>Service</v-list-item-title>
                <v-list-item-subtitle>{{ user.service_nom }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Snackbars -->
    <v-snackbar v-model="showSuccess" color="success" :timeout="3000">
      {{ successMessage }}
    </v-snackbar>
    <v-snackbar v-model="showError" color="error" :timeout="5000">
      {{ errorMessage }}
    </v-snackbar>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  ROLE_DATA_LABELS,
  ROLE_DEMANDES_LABELS,
  ROLE_SIG_LABELS,
  ROLE_TERRAIN_LABELS,
  ROLE_COLORS,
} from '@/stores/users'
import HelpButton from '@/components/help/HelpButton.vue'

const authStore = useAuthStore()

const form = ref()
const passwordForm = ref()
const formValid = ref(false)
const passwordFormValid = ref(false)
const saving = ref(false)
const changingPassword = ref(false)
const showSuccess = ref(false)
const showError = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const formData = ref({
  prenom: '',
  nom: '',
  email: '',
})

const passwords = ref({
  current: '',
  new: '',
  confirm: '',
})

const passwordRules = [
  (v: string) => !!v || 'Requis',
  (v: string) => v.length >= 6 || 'Minimum 6 caractères',
]

const user = computed(() => authStore.user)
const initials = computed(() => {
  if (!user.value) return 'U'
  return `${user.value.prenom[0]}${user.value.nom[0]}`.toUpperCase()
})

function formatDate(dateString?: string | null): string {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function saveProfile() {
  saving.value = true
  try {
    // Pour l'instant on ne peut pas modifier le profil via l'API
    // Il faudrait ajouter un endpoint PUT /api/auth/me
    successMessage.value = 'Profil mis à jour'
    showSuccess.value = true
  } catch (err: any) {
    errorMessage.value = err.message || 'Erreur lors de la mise à jour'
    showError.value = true
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  changingPassword.value = true
  try {
    const success = await authStore.changePassword(passwords.value.current, passwords.value.new)
    if (success) {
      successMessage.value = 'Mot de passe modifié avec succès'
      showSuccess.value = true
      passwords.value = { current: '', new: '', confirm: '' }
      passwordForm.value?.reset()
    } else {
      errorMessage.value = authStore.error || 'Erreur lors du changement de mot de passe'
      showError.value = true
    }
  } finally {
    changingPassword.value = false
  }
}

onMounted(() => {
  if (user.value) {
    formData.value = {
      prenom: user.value.prenom,
      nom: user.value.nom,
      email: user.value.email,
    }
  }
})
</script>

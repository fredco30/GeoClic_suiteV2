<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">
          Gestion des Utilisateurs
          <HelpButton page-key="utilisateurs" size="sm" />
        </h1>
        <p class="text-body-2 text-grey mt-1">
          Gérez les comptes utilisateurs et leurs accès aux applications GéoClic
        </p>
      </div>
      <v-spacer />
      <v-btn
        v-if="isSuperAdmin"
        color="warning"
        variant="outlined"
        prepend-icon="mdi-crown"
        class="mr-2"
        @click="showSuperAdminDialog = true"
      >
        Changer Super Admin
      </v-btn>
      <v-btn color="primary" prepend-icon="mdi-account-plus" @click="openCreateDialog">
        Nouvel utilisateur
      </v-btn>
    </div>

    <!-- Stats par application -->
    <v-row class="mb-4">
      <v-col cols="6" sm="2">
        <v-card color="primary" variant="tonal">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ users.length }}</div>
            <div class="text-caption">Total</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="2">
        <v-card color="success" variant="tonal">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ activeUsers.length }}</div>
            <div class="text-caption">Actifs</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="2">
        <v-card color="error" variant="tonal">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ superAdmins.length }}</div>
            <div class="text-caption">Super Admin</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="2">
        <v-card color="blue" variant="tonal">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ usersWithDemandesAccess.length }}</div>
            <div class="text-caption">Demandes</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="2">
        <v-card color="purple" variant="tonal">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ usersWithSigAccess.length }}</div>
            <div class="text-caption">SIG</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="2">
        <v-card color="orange" variant="tonal">
          <v-card-text class="text-center py-3">
            <div class="text-h5 font-weight-bold">{{ usersWithTerrainAccess.length }}</div>
            <div class="text-caption">Terrain</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filters -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="4">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Rechercher"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filterApp"
              label="Accès application"
              :items="appFilterOptions"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filterStatus"
              label="Statut"
              :items="statusOptions"
              clearable
              hide-details
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Users table -->
    <v-card>
      <v-data-table
        :headers="headers"
        :items="filteredUsers"
        :loading="loading"
        :search="search"
        hover
      >
        <template v-slot:item.nom="{ item }">
          <div class="d-flex align-center">
            <v-avatar :color="item.is_super_admin ? 'error' : 'primary'" size="36" class="mr-3">
              <v-icon v-if="item.is_super_admin" color="white" size="small">mdi-crown</v-icon>
              <span v-else class="text-white">{{ getInitials(item) }}</span>
            </v-avatar>
            <div>
              <div class="font-weight-medium">
                {{ item.prenom }} {{ item.nom }}
                <v-chip v-if="item.is_super_admin" color="error" size="x-small" class="ml-1">
                  Super Admin
                </v-chip>
              </div>
              <div class="text-caption text-grey">{{ item.email }}</div>
            </div>
          </div>
        </template>

        <template v-slot:item.roles="{ item }">
          <div class="d-flex flex-wrap gap-1">
            <template v-if="item.is_super_admin">
              <v-chip color="error" size="x-small">Tous les accès</v-chip>
            </template>
            <template v-else>
              <v-chip
                v-if="item.role_data !== 'aucun'"
                :color="ROLE_COLORS[item.role_data]"
                size="x-small"
              >
                Data: {{ ROLE_DATA_LABELS[item.role_data] }}
              </v-chip>
              <v-chip
                v-if="item.role_demandes !== 'aucun'"
                :color="ROLE_COLORS[item.role_demandes]"
                size="x-small"
              >
                Demandes: {{ ROLE_DEMANDES_LABELS[item.role_demandes] }}
              </v-chip>
              <v-chip
                v-if="item.role_sig !== 'aucun'"
                :color="ROLE_COLORS[item.role_sig]"
                size="x-small"
              >
                SIG: {{ ROLE_SIG_LABELS[item.role_sig] }}
              </v-chip>
              <v-chip
                v-if="item.role_terrain !== 'aucun'"
                :color="ROLE_COLORS[item.role_terrain]"
                size="x-small"
              >
                Terrain: {{ ROLE_TERRAIN_LABELS[item.role_terrain] }}
              </v-chip>
              <span
                v-if="item.role_data === 'aucun' && item.role_demandes === 'aucun' && item.role_sig === 'aucun' && item.role_terrain === 'aucun'"
                class="text-caption text-grey"
              >
                Aucun accès
              </span>
            </template>
          </div>
        </template>

        <template v-slot:item.service="{ item }">
          <span v-if="item.service_nom" class="text-body-2">{{ item.service_nom }}</span>
          <span v-else class="text-caption text-grey">-</span>
        </template>

        <template v-slot:item.actif="{ item }">
          <v-chip :color="item.actif ? 'success' : 'grey'" size="small">
            {{ item.actif ? 'Actif' : 'Inactif' }}
          </v-chip>
        </template>

        <template v-slot:item.last_login="{ item }">
          <span v-if="item.last_login">{{ formatDate(item.last_login) }}</span>
          <span v-else class="text-grey">Jamais</span>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn icon size="small" variant="text" @click="editUser(item)">
            <v-icon>mdi-pencil</v-icon>
            <v-tooltip activator="parent" location="top">Modifier</v-tooltip>
          </v-btn>
          <v-btn
            icon
            size="small"
            variant="text"
            @click="toggleActive(item)"
            :disabled="item.is_super_admin"
          >
            <v-icon>{{ item.actif ? 'mdi-account-off' : 'mdi-account-check' }}</v-icon>
            <v-tooltip activator="parent" location="top">
              {{ item.actif ? 'Désactiver' : 'Activer' }}
            </v-tooltip>
          </v-btn>
          <v-btn
            icon
            size="small"
            variant="text"
            color="error"
            @click="confirmDelete(item)"
            :disabled="item.is_super_admin"
          >
            <v-icon>mdi-delete</v-icon>
            <v-tooltip activator="parent" location="top">
              {{ item.is_super_admin ? 'Super admin protégé' : 'Supprimer' }}
            </v-tooltip>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog création/édition -->
    <v-dialog v-model="showDialog" max-width="700" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">
            {{ editMode ? 'mdi-account-edit' : 'mdi-account-plus' }}
          </v-icon>
          {{ editMode ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <!-- Infos de base -->
            <div class="text-subtitle-2 font-weight-medium mb-2">Informations</div>
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.prenom"
                  label="Prénom *"
                  :rules="[v => !!v || 'Prénom requis']"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="formData.nom"
                  label="Nom *"
                  :rules="[v => !!v || 'Nom requis']"
                  density="comfortable"
                />
              </v-col>
            </v-row>
            <v-text-field
              v-model="formData.email"
              label="Email *"
              type="email"
              :rules="emailRules"
              density="comfortable"
            />
            <v-text-field
              v-if="!editMode"
              v-model="formData.password"
              label="Mot de passe *"
              :type="showPassword ? 'text' : 'password'"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              :rules="passwordRules"
              @click:append-inner="showPassword = !showPassword"
              density="comfortable"
            />

            <v-divider class="my-4" />

            <!-- Rôles par application -->
            <div class="text-subtitle-2 font-weight-medium mb-3">Accès aux applications</div>

            <v-alert
              v-if="formData.is_super_admin"
              type="warning"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              <strong>Super Administrateur</strong> - Cet utilisateur a accès à toutes les applications avec tous les droits.
            </v-alert>

            <v-switch
              v-model="formData.is_super_admin"
              label="Super Administrateur (accès complet)"
              color="error"
              density="compact"
              class="mb-2"
              :disabled="editingSuperAdmin"
            />

            <template v-if="!formData.is_super_admin">
              <v-row>
                <!-- GéoClic Data -->
                <v-col cols="12" md="6">
                  <v-card variant="outlined" class="pa-3">
                    <div class="d-flex align-center mb-2">
                      <v-icon color="primary" class="mr-2">mdi-database</v-icon>
                      <span class="font-weight-medium">GéoClic Data</span>
                    </div>
                    <v-select
                      v-model="formData.role_data"
                      :items="roleDataOptions"
                      density="compact"
                      hide-details
                    />
                  </v-card>
                </v-col>

                <!-- GéoClic Demandes -->
                <v-col cols="12" md="6">
                  <v-card variant="outlined" class="pa-3">
                    <div class="d-flex align-center mb-2">
                      <v-icon color="blue" class="mr-2">mdi-clipboard-text</v-icon>
                      <span class="font-weight-medium">GéoClic Demandes</span>
                    </div>
                    <v-select
                      v-model="formData.role_demandes"
                      :items="roleDemandesOptions"
                      density="compact"
                      hide-details
                    />
                  </v-card>
                </v-col>

                <!-- GéoClic SIG -->
                <v-col cols="12" md="6">
                  <v-card variant="outlined" class="pa-3">
                    <div class="d-flex align-center mb-2">
                      <v-icon color="purple" class="mr-2">mdi-map</v-icon>
                      <span class="font-weight-medium">GéoClic SIG</span>
                    </div>
                    <v-select
                      v-model="formData.role_sig"
                      :items="roleSigOptions"
                      density="compact"
                      hide-details
                    />
                  </v-card>
                </v-col>

                <!-- GéoClic Terrain -->
                <v-col cols="12" md="6">
                  <v-card variant="outlined" class="pa-3">
                    <div class="d-flex align-center mb-2">
                      <v-icon color="orange" class="mr-2">mdi-map-marker-radius</v-icon>
                      <span class="font-weight-medium">GéoClic Terrain</span>
                    </div>
                    <v-select
                      v-model="formData.role_terrain"
                      :items="roleTerrainOptions"
                      density="compact"
                      hide-details
                    />
                  </v-card>
                </v-col>
              </v-row>

              <!-- Service (pour agents terrain) -->
              <v-expand-transition>
                <div v-if="formData.role_terrain === 'agent'" class="mt-4">
                  <v-select
                    v-model="formData.service_id"
                    label="Service assigné (pour Terrain)"
                    :items="services"
                    item-title="nom"
                    item-value="id"
                    clearable
                    density="comfortable"
                    prepend-inner-icon="mdi-domain"
                    hint="Service municipal auquel l'agent terrain est rattaché"
                    persistent-hint
                  />
                </div>
              </v-expand-transition>
            </template>

            <v-divider class="my-4" />

            <v-switch
              v-model="formData.actif"
              label="Compte actif"
              color="success"
              density="compact"
              :disabled="formData.is_super_admin"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn color="primary" :disabled="!formValid" :loading="saving" @click="saveUser">
            {{ editMode ? 'Modifier' : 'Créer' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog confirmation suppression -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">Confirmer la suppression</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer l'utilisateur
          <strong>{{ selectedUser?.prenom }} {{ selectedUser?.nom }}</strong> ?
          <v-alert type="warning" variant="tonal" class="mt-4">
            Cette action est irréversible.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Annuler</v-btn>
          <v-btn color="error" @click="deleteUser">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog changement super admin -->
    <v-dialog v-model="showSuperAdminDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon color="warning" class="mr-2">mdi-crown</v-icon>
          Changer le Super Administrateur
        </v-card-title>
        <v-card-text>
          <v-alert type="warning" variant="tonal" class="mb-4">
            <strong>Attention :</strong> Cette action va transférer les droits de super admin
            au nouveau compte. Vous serez déconnecté et devrez vous reconnecter avec le nouveau compte.
          </v-alert>

          <v-form ref="superAdminForm" v-model="superAdminFormValid">
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="superAdminData.prenom"
                  label="Prénom *"
                  :rules="[v => !!v || 'Prénom requis']"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="superAdminData.nom"
                  label="Nom *"
                  :rules="[v => !!v || 'Nom requis']"
                  density="comfortable"
                />
              </v-col>
            </v-row>
            <v-text-field
              v-model="superAdminData.email"
              label="Email *"
              type="email"
              :rules="emailRules"
              density="comfortable"
            />
            <v-text-field
              v-model="superAdminData.password"
              label="Nouveau mot de passe *"
              :type="showSuperAdminPassword ? 'text' : 'password'"
              :append-inner-icon="showSuperAdminPassword ? 'mdi-eye-off' : 'mdi-eye'"
              :rules="passwordRules"
              @click:append-inner="showSuperAdminPassword = !showSuperAdminPassword"
              density="comfortable"
            />
            <v-text-field
              v-model="superAdminData.confirmPassword"
              label="Confirmer le mot de passe *"
              :type="showSuperAdminPassword ? 'text' : 'password'"
              :rules="[
                v => !!v || 'Confirmation requise',
                v => v === superAdminData.password || 'Les mots de passe ne correspondent pas'
              ]"
              density="comfortable"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeSuperAdminDialog">Annuler</v-btn>
          <v-btn
            color="warning"
            :disabled="!superAdminFormValid"
            :loading="savingSuperAdmin"
            @click="changeSuperAdmin"
          >
            <v-icon start>mdi-crown</v-icon>
            Transférer les droits
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar erreur -->
    <v-snackbar v-model="showError" color="error" :timeout="5000">
      {{ errorMessage }}
      <template v-slot:actions>
        <v-btn variant="text" @click="showError = false">Fermer</v-btn>
      </template>
    </v-snackbar>

    <!-- Snackbar succès -->
    <v-snackbar v-model="showSuccess" color="success" :timeout="3000">
      {{ successMessage }}
    </v-snackbar>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch } from 'vue'
import HelpButton from '@/components/help/HelpButton.vue'
import { useAuthStore } from '@/stores/auth'
import {
  useUsersStore,
  type User,
  type RoleData,
  type RoleDemandes,
  type RoleSig,
  type RoleTerrain,
  ROLE_DATA_LABELS,
  ROLE_DEMANDES_LABELS,
  ROLE_SIG_LABELS,
  ROLE_TERRAIN_LABELS,
  ROLE_COLORS,
} from '@/stores/users'

defineOptions({
  meta: {
    layout: 'admin',
  },
})

const usersStore = useUsersStore()
const authStore = useAuthStore()

// Check if current user is super admin
const isSuperAdmin = computed(() => authStore.user?.is_super_admin === true)

// State
const search = ref('')
const filterApp = ref<string | null>(null)
const filterStatus = ref<string | null>(null)
const showDialog = ref(false)
const showDeleteDialog = ref(false)
const editMode = ref(false)
const editingSuperAdmin = ref(false)
const showPassword = ref(false)
const formValid = ref(false)
const selectedUser = ref<User | null>(null)
const saving = ref(false)
const showError = ref(false)
const showSuccess = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// Super admin dialog state
const showSuperAdminDialog = ref(false)
const showSuperAdminPassword = ref(false)
const superAdminFormValid = ref(false)
const savingSuperAdmin = ref(false)
const superAdminData = ref({
  prenom: '',
  nom: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const formData = ref({
  prenom: '',
  nom: '',
  email: '',
  password: '',
  actif: true,
  is_super_admin: false,
  role_data: 'aucun' as RoleData,
  role_demandes: 'aucun' as RoleDemandes,
  role_sig: 'aucun' as RoleSig,
  role_terrain: 'aucun' as RoleTerrain,
  service_id: null as string | null,
})

// Options pour les filtres
const appFilterOptions = [
  { title: 'Toutes les applications', value: null },
  { title: 'GéoClic Data', value: 'data' },
  { title: 'GéoClic Demandes', value: 'demandes' },
  { title: 'GéoClic SIG', value: 'sig' },
  { title: 'GéoClic Terrain', value: 'terrain' },
]

const statusOptions = [
  { title: 'Tous', value: null },
  { title: 'Actifs', value: 'active' },
  { title: 'Inactifs', value: 'inactive' },
]

// Options pour les rôles
const roleDataOptions = [
  { title: 'Aucun accès', value: 'aucun' },
  { title: 'Administrateur', value: 'admin' },
]

const roleDemandesOptions = [
  { title: 'Aucun accès', value: 'aucun' },
  { title: 'Agent', value: 'agent' },
  { title: 'Administrateur', value: 'admin' },
]

const roleSigOptions = [
  { title: 'Aucun accès', value: 'aucun' },
  { title: 'Lecture seule', value: 'lecture' },
  { title: 'Édition', value: 'edition' },
]

const roleTerrainOptions = [
  { title: 'Aucun accès', value: 'aucun' },
  { title: 'Agent terrain', value: 'agent' },
]

const headers = [
  { title: 'Utilisateur', key: 'nom', width: '25%' },
  { title: 'Accès', key: 'roles', width: '30%', sortable: false },
  { title: 'Service', key: 'service', width: '15%' },
  { title: 'Statut', key: 'actif', width: '10%' },
  { title: 'Dernière connexion', key: 'last_login', width: '10%' },
  { title: 'Actions', key: 'actions', sortable: false, width: '10%' },
]

// Validation rules
const emailRules = [
  (v: string) => !!v || 'Email requis',
  (v: string) => /.+@.+\..+/.test(v) || 'Email invalide',
]

const passwordRules = [
  (v: string) => !!v || 'Mot de passe requis',
  (v: string) => v.length >= 6 || 'Minimum 6 caractères',
]

// Computed
const loading = computed(() => usersStore.loading)
const users = computed(() => usersStore.users)
const services = computed(() => usersStore.services)
const activeUsers = computed(() => usersStore.activeUsers)
const superAdmins = computed(() => usersStore.superAdmins)
const usersWithDemandesAccess = computed(() => usersStore.usersWithDemandesAccess)
const usersWithSigAccess = computed(() => usersStore.usersWithSigAccess)
const usersWithTerrainAccess = computed(() => usersStore.usersWithTerrainAccess)

const filteredUsers = computed(() => {
  let result = [...users.value]

  if (filterApp.value) {
    result = result.filter(u => {
      if (u.is_super_admin) return true
      switch (filterApp.value) {
        case 'data': return u.role_data !== 'aucun'
        case 'demandes': return u.role_demandes !== 'aucun'
        case 'sig': return u.role_sig !== 'aucun'
        case 'terrain': return u.role_terrain !== 'aucun'
        default: return true
      }
    })
  }

  if (filterStatus.value === 'active') {
    result = result.filter(u => u.actif)
  } else if (filterStatus.value === 'inactive') {
    result = result.filter(u => !u.actif)
  }

  return result
})

// Methods
function getInitials(user: User): string {
  return `${user.prenom[0]}${user.nom[0]}`.toUpperCase()
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function openCreateDialog() {
  editMode.value = false
  editingSuperAdmin.value = false
  formData.value = {
    prenom: '',
    nom: '',
    email: '',
    password: '',
    actif: true,
    is_super_admin: false,
    role_data: 'aucun',
    role_demandes: 'aucun',
    role_sig: 'aucun',
    role_terrain: 'aucun',
    service_id: null,
  }
  showDialog.value = true
}

function editUser(user: User) {
  editMode.value = true
  editingSuperAdmin.value = user.is_super_admin
  selectedUser.value = user
  formData.value = {
    prenom: user.prenom,
    nom: user.nom,
    email: user.email,
    password: '',
    actif: user.actif,
    is_super_admin: user.is_super_admin,
    role_data: user.role_data,
    role_demandes: user.role_demandes,
    role_sig: user.role_sig,
    role_terrain: user.role_terrain,
    service_id: user.service_id,
  }
  showDialog.value = true
}

function closeDialog() {
  showDialog.value = false
  selectedUser.value = null
}

async function saveUser() {
  saving.value = true
  try {
    if (editMode.value && selectedUser.value) {
      const data: any = {
        nom: formData.value.nom,
        prenom: formData.value.prenom,
        email: formData.value.email,
        actif: formData.value.actif,
        role_data: formData.value.role_data,
        role_demandes: formData.value.role_demandes,
        role_sig: formData.value.role_sig,
        role_terrain: formData.value.role_terrain,
        service_id: formData.value.role_terrain === 'agent' ? formData.value.service_id : null,
      }
      const success = await usersStore.updateUser(selectedUser.value.id, data)
      if (success) {
        successMessage.value = 'Utilisateur modifié'
        showSuccess.value = true
        closeDialog()
      } else {
        errorMessage.value = usersStore.error || 'Erreur lors de la modification'
        showError.value = true
      }
    } else {
      const data = {
        nom: formData.value.nom,
        prenom: formData.value.prenom,
        email: formData.value.email,
        password: formData.value.password,
        role_data: formData.value.is_super_admin ? 'admin' as RoleData : formData.value.role_data,
        role_demandes: formData.value.is_super_admin ? 'admin' as RoleDemandes : formData.value.role_demandes,
        role_sig: formData.value.is_super_admin ? 'edition' as RoleSig : formData.value.role_sig,
        role_terrain: formData.value.is_super_admin ? 'agent' as RoleTerrain : formData.value.role_terrain,
        service_id: formData.value.role_terrain === 'agent' ? formData.value.service_id : null,
      }
      const user = await usersStore.createUser(data)
      if (user) {
        successMessage.value = 'Utilisateur créé'
        showSuccess.value = true
        closeDialog()
      } else {
        errorMessage.value = usersStore.error || 'Erreur lors de la création'
        showError.value = true
      }
    }
  } finally {
    saving.value = false
  }
}

async function toggleActive(user: User) {
  const success = await usersStore.toggleActive(user.id)
  if (success) {
    successMessage.value = user.actif ? 'Utilisateur désactivé' : 'Utilisateur activé'
    showSuccess.value = true
  } else {
    errorMessage.value = usersStore.error || 'Erreur lors du changement de statut'
    showError.value = true
  }
}

function confirmDelete(user: User) {
  selectedUser.value = user
  showDeleteDialog.value = true
}

async function deleteUser() {
  if (!selectedUser.value) return
  const success = await usersStore.deleteUser(selectedUser.value.id)
  if (success) {
    successMessage.value = 'Utilisateur supprimé'
    showSuccess.value = true
  } else {
    errorMessage.value = usersStore.error || 'Erreur lors de la suppression'
    showError.value = true
  }
  showDeleteDialog.value = false
  selectedUser.value = null
}

// Watch for super admin toggle - auto-set all roles
watch(() => formData.value.is_super_admin, (isSuperAdmin) => {
  if (isSuperAdmin) {
    formData.value.actif = true
  }
})

// Super admin management
function closeSuperAdminDialog() {
  showSuperAdminDialog.value = false
  superAdminData.value = {
    prenom: '',
    nom: '',
    email: '',
    password: '',
    confirmPassword: '',
  }
  showSuperAdminPassword.value = false
}

async function changeSuperAdmin() {
  if (!superAdminFormValid.value) return

  savingSuperAdmin.value = true
  try {
    const result = await usersStore.updateSuperAdmin({
      email: superAdminData.value.email,
      password: superAdminData.value.password,
      nom: superAdminData.value.nom,
      prenom: superAdminData.value.prenom,
    })

    if (result) {
      successMessage.value = 'Super admin transféré avec succès. Vous allez être déconnecté...'
      showSuccess.value = true
      closeSuperAdminDialog()

      // Déconnecter après 2 secondes
      setTimeout(() => {
        authStore.logout()
      }, 2000)
    } else {
      errorMessage.value = usersStore.error || 'Erreur lors du changement de super admin'
      showError.value = true
    }
  } finally {
    savingSuperAdmin.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    usersStore.fetchAll(),
    usersStore.fetchServices(),
  ])
})
</script>

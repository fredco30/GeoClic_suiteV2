<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import HelpButton from '@/components/help/HelpButton.vue'

const route = useRoute()
const authStore = useAuthStore()

const activeTab = ref<'general' | 'alertes' | 'utilisateurs' | 'profil'>('general')

// Cle d'aide dynamique selon l'onglet actif
const helpPageKey = computed(() => {
  const tabKeys: Record<string, string> = {
    general: 'parametresGeneral',
    alertes: 'parametresAlertes',
    utilisateurs: 'parametresUtilisateurs',
    profil: 'parametresProfil'
  }
  return tabKeys[activeTab.value] || 'parametresGeneral'
})

// Parametres generaux
const generalSettings = ref({
  project_name: '',
  primary_color: '#3b82f6',
  logo_url: '',
  auto_assign: false,
  moderation_enabled: true,
  notification_email_admin: ''
})

// Parametres alertes
const alertesSettings = ref({
  delai_retard_jours: 2,
  rappel_intervention_actif: true,
  rappel_intervention_heures: 24
})

// Parametres email (lecture seule, charges pour alertes)
const emailSettings = ref<any>({})

// Liste des utilisateurs
const users = ref<any[]>([])
const showUserModal = ref(false)
const editingUser = ref<any>(null)

const userForm = ref({
  email: '',
  name: '',
  role: 'agent',
  password: ''
})

// Profil
const profileForm = ref({
  name: '',
  email: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const loading = ref(true)
const saving = ref(false)
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null)

onMounted(async () => {
  // Verifier le parametre URL pour l'onglet
  const tabParam = route.query.tab as string
  if (tabParam && ['general', 'alertes', 'utilisateurs', 'profil'].includes(tabParam)) {
    activeTab.value = tabParam as typeof activeTab.value
  }

  await loadSettings()
  if (authStore.user) {
    profileForm.value.name = authStore.user.name
    profileForm.value.email = authStore.user.email
  }
})

async function loadSettings() {
  loading.value = true
  try {
    const [generalRes, emailRes, usersRes] = await Promise.all([
      axios.get('/api/settings/general'),
      axios.get('/api/settings/email').catch(() => ({ data: {} })),
      authStore.isAdmin ? axios.get('/api/users') : Promise.resolve({ data: [] })
    ])

    generalSettings.value = generalRes.data
    emailSettings.value = emailRes.data
    users.value = usersRes.data

    // Extraire les parametres d'alertes depuis les parametres email
    alertesSettings.value = {
      delai_retard_jours: Math.round((emailRes.data.reminder_hours_before || 24) / 24),
      rappel_intervention_actif: emailRes.data.notify_agent_reminder ?? true,
      rappel_intervention_heures: emailRes.data.reminder_hours_before || 24
    }
  } catch (error) {
    console.error('Erreur chargement:', error)
  } finally {
    loading.value = false
  }
}

async function saveGeneralSettings() {
  saving.value = true
  message.value = null
  try {
    await axios.put('/api/settings/general', generalSettings.value)
    message.value = { type: 'success', text: 'Parametres enregistres' }
  } catch (error) {
    message.value = { type: 'error', text: 'Erreur lors de l\'enregistrement' }
  } finally {
    saving.value = false
  }
}

async function saveAlertesSettings() {
  saving.value = true
  message.value = null
  try {
    // Convertir le delai de retard en heures pour le stockage
    const heures = alertesSettings.value.delai_retard_jours * 24

    const updatedEmailSettings = {
      ...emailSettings.value,
      notify_agent_reminder: alertesSettings.value.rappel_intervention_actif,
      reminder_hours_before: heures
    }
    await axios.put('/api/settings/email', updatedEmailSettings)
    emailSettings.value = updatedEmailSettings

    // Synchroniser les heures dans le formulaire
    alertesSettings.value.rappel_intervention_heures = heures

    message.value = { type: 'success', text: 'Parametres d\'alertes enregistres' }
  } catch (error) {
    message.value = { type: 'error', text: 'Erreur lors de l\'enregistrement' }
  } finally {
    saving.value = false
  }
}

function openCreateUser() {
  editingUser.value = null
  userForm.value = {
    email: '',
    name: '',
    role: 'agent',
    password: ''
  }
  showUserModal.value = true
}

function openEditUser(user: any) {
  editingUser.value = user
  userForm.value = {
    email: user.email,
    name: user.name,
    role: user.role,
    password: ''
  }
  showUserModal.value = true
}

async function saveUser() {
  try {
    if (editingUser.value) {
      await axios.put(`/api/users/${editingUser.value.id}`, userForm.value)
    } else {
      await axios.post('/api/users', userForm.value)
    }
    showUserModal.value = false
    await loadSettings()
    message.value = { type: 'success', text: 'Utilisateur enregistre' }
  } catch (error) {
    message.value = { type: 'error', text: 'Erreur lors de l\'enregistrement' }
  }
}

async function deleteUser(user: any) {
  if (user.id === authStore.user?.id) {
    alert('Vous ne pouvez pas supprimer votre propre compte')
    return
  }

  if (!confirm(`Supprimer l'utilisateur "${user.name}" ?`)) return

  try {
    await axios.delete(`/api/users/${user.id}`)
    await loadSettings()
    message.value = { type: 'success', text: 'Utilisateur supprime' }
  } catch (error) {
    message.value = { type: 'error', text: 'Erreur lors de la suppression' }
  }
}

async function updateProfile() {
  if (profileForm.value.newPassword !== profileForm.value.confirmPassword) {
    message.value = { type: 'error', text: 'Les mots de passe ne correspondent pas' }
    return
  }

  saving.value = true
  try {
    await authStore.updateProfile({
      name: profileForm.value.name,
      password: profileForm.value.newPassword || undefined
    })
    message.value = { type: 'success', text: 'Profil mis a jour' }
    profileForm.value.currentPassword = ''
    profileForm.value.newPassword = ''
    profileForm.value.confirmPassword = ''
  } catch (error) {
    message.value = { type: 'error', text: 'Erreur lors de la mise a jour' }
  } finally {
    saving.value = false
  }
}

function getRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    admin: 'Administrateur',
    moderateur: 'Moderateur',
    agent: 'Agent'
  }
  return labels[role] || role
}
</script>

<template>
  <div class="parametres-view">
    <header class="page-header">
      <h1>Param&#232;tres <HelpButton :page-key="helpPageKey" size="sm" /></h1>
    </header>

    <!-- Tabs -->
    <div class="tabs">
      <button
        :class="{ active: activeTab === 'general' }"
        @click="activeTab = 'general'"
      >
        &#9881; G&#233;n&#233;ral
      </button>
      <button
        :class="{ active: activeTab === 'alertes' }"
        @click="activeTab = 'alertes'"
        v-if="authStore.isAdmin"
      >
        &#128276; Alertes
      </button>
      <button
        :class="{ active: activeTab === 'utilisateurs' }"
        @click="activeTab = 'utilisateurs'"
        v-if="authStore.isAdmin"
      >
        &#128101; Utilisateurs
      </button>
      <button
        :class="{ active: activeTab === 'profil' }"
        @click="activeTab = 'profil'"
      >
        &#128100; Mon profil
      </button>
    </div>

    <!-- Message -->
    <div v-if="message" :class="['message', message.type]">
      {{ message.text }}
      <button @click="message = null">&#10005;</button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <template v-else>
      <!-- General -->
      <div v-if="activeTab === 'general'" class="settings-panel">
        <form @submit.prevent="saveGeneralSettings">
          <div class="form-group">
            <label>Nom du projet</label>
            <input v-model="generalSettings.project_name" type="text" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Couleur principale</label>
              <input v-model="generalSettings.primary_color" type="color" class="color-input" />
            </div>

            <div class="form-group">
              <label>URL du logo</label>
              <input v-model="generalSettings.logo_url" type="url" placeholder="https://..." />
            </div>
          </div>

          <div class="form-group">
            <label>Email notifications admin</label>
            <input v-model="generalSettings.notification_email_admin" type="email" />
          </div>

          <div class="form-group checkbox-group">
            <label>
              <input v-model="generalSettings.moderation_enabled" type="checkbox" />
              Activer la mod&#233;ration des demandes
            </label>
            <small>Les demandes passeront par une &#233;tape de validation</small>
          </div>

          <div class="form-group checkbox-group">
            <label>
              <input v-model="generalSettings.auto_assign" type="checkbox" />
              Assignation automatique par quartier
            </label>
            <small>Les demandes seront assign&#233;es selon le quartier</small>
          </div>

          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Enregistrement...' : 'Enregistrer' }}
          </button>
        </form>

        <!-- Info centralisation -->
        <div class="admin-redirect-info" v-if="authStore.isAdmin">
          <span class="redirect-icon">&#128712;</span>
          <div>
            <strong>Personnalisation et email</strong>
            <p>La configuration du branding (logo, couleurs, nom de la collectivit&#233;) et des notifications email est centralis&#233;e dans <strong>G&#233;oClic Admin</strong> (module Data &gt; Param&#232;tres).</p>
          </div>
        </div>
      </div>

      <!-- Alertes -->
      <div v-if="activeTab === 'alertes' && authStore.isAdmin" class="settings-panel">
        <form @submit.prevent="saveAlertesSettings">
          <div class="alertes-intro">
            <p>Configurez ici les d&#233;lais et les alertes automatiques pour le suivi des demandes.</p>
          </div>

          <h4>&#128337; D&#233;lai d'alerte</h4>

          <div class="form-group">
            <label>Une demande n&#233;cessite une attention apr&#232;s</label>
            <div class="inline-select">
              <select v-model="alertesSettings.delai_retard_jours">
                <option :value="1">1 jour</option>
                <option :value="2">2 jours</option>
                <option :value="3">3 jours</option>
                <option :value="5">5 jours</option>
                <option :value="7">7 jours (1 semaine)</option>
                <option :value="14">14 jours (2 semaines)</option>
              </select>
              <span>sans traitement</span>
            </div>
            <small>Ce d&#233;lai est utilis&#233; dans le tableau de bord pour identifier les demandes "en retard".</small>
          </div>

          <h4>&#128231; Rappels par email</h4>

          <div class="form-group checkbox-group">
            <label>
              <input v-model="alertesSettings.rappel_intervention_actif" type="checkbox" />
              <strong>Activer les rappels automatiques</strong>
            </label>
            <small>Envoie un email de rappel aux agents terrain avant une intervention planifi&#233;e (d&#233;lai = {{ alertesSettings.delai_retard_jours }} jour{{ alertesSettings.delai_retard_jours > 1 ? 's' : '' }} avant)</small>
          </div>

          <div class="alertes-note">
            <span class="note-icon">&#128712;</span>
            <span>Pour que les rappels fonctionnent, les notifications email doivent &#234;tre configur&#233;es dans <strong>G&#233;oClic Admin</strong> (module Data &gt; Param&#232;tres &gt; Email).</span>
          </div>

          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Enregistrement...' : 'Enregistrer' }}
          </button>
        </form>
      </div>

      <!-- Utilisateurs -->
      <div v-if="activeTab === 'utilisateurs' && authStore.isAdmin" class="settings-panel">
        <div class="users-header">
          <h3>Utilisateurs ({{ users.length }})</h3>
          <button class="btn btn-primary" @click="openCreateUser">
            + Nouvel utilisateur
          </button>
        </div>

        <table class="users-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>R&#244;le</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.name }}</td>
              <td>{{ user.email }}</td>
              <td>
                <span class="role-badge" :class="user.role">
                  {{ getRoleLabel(user.role) }}
                </span>
              </td>
              <td class="actions">
                <button @click="openEditUser(user)">&#9998;</button>
                <button
                  @click="deleteUser(user)"
                  :disabled="user.id === authStore.user?.id"
                >
                  &#128465;
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Profil -->
      <div v-if="activeTab === 'profil'" class="settings-panel">
        <form @submit.prevent="updateProfile">
          <div class="form-group">
            <label>Nom</label>
            <input v-model="profileForm.name" type="text" required />
          </div>

          <div class="form-group">
            <label>Email</label>
            <input v-model="profileForm.email" type="email" disabled />
            <small>L'email ne peut pas &#234;tre modifi&#233;</small>
          </div>

          <h4>Changer le mot de passe</h4>

          <div class="form-group">
            <label>Nouveau mot de passe</label>
            <input v-model="profileForm.newPassword" type="password" />
          </div>

          <div class="form-group">
            <label>Confirmer le mot de passe</label>
            <input v-model="profileForm.confirmPassword" type="password" />
          </div>

          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Enregistrement...' : 'Mettre &#224; jour' }}
          </button>
        </form>
      </div>
    </template>

    <!-- Modal Utilisateur -->
    <div v-if="showUserModal" class="modal-overlay" @click.self="showUserModal = false">
      <div class="modal">
        <h3>{{ editingUser ? 'Modifier' : 'Nouvel' }} utilisateur</h3>

        <div class="form-group">
          <label>Nom *</label>
          <input v-model="userForm.name" type="text" required />
        </div>

        <div class="form-group">
          <label>Email *</label>
          <input v-model="userForm.email" type="email" required :disabled="!!editingUser" />
        </div>

        <div class="form-group">
          <label>R&#244;le</label>
          <select v-model="userForm.role">
            <option value="admin">Administrateur</option>
            <option value="moderateur">Mod&#233;rateur</option>
            <option value="agent">Agent</option>
          </select>
        </div>

        <div class="form-group">
          <label>{{ editingUser ? 'Nouveau mot de passe' : 'Mot de passe *' }}</label>
          <input v-model="userForm.password" type="password" :required="!editingUser" />
        </div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showUserModal = false">
            Annuler
          </button>
          <button class="btn btn-primary" @click="saveUser">
            {{ editingUser ? 'Enregistrer' : 'Cr&#233;er' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.parametres-view {
  padding: 1.5rem;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  font-size: 1.75rem;
  margin: 0;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0.5rem;
}

.tabs button {
  padding: 0.75rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: 6px 6px 0 0;
  transition: all 0.2s;
}

.tabs button:hover {
  background: #f9fafb;
}

.tabs button.active {
  background: #eff6ff;
  color: #3b82f6;
  font-weight: 500;
}

/* Message */
.message {
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.message.success {
  background: #dcfce7;
  color: #15803d;
}

.message.error {
  background: #fee2e2;
  color: #dc2626;
}

.message button {
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0.7;
}

/* Loading */
.loading {
  display: flex;
  justify-content: center;
  padding: 4rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Settings Panel */
.settings-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.settings-panel h4 {
  margin: 1.5rem 0 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
}

.form-group input:disabled {
  background: #f9fafb;
  color: #6b7280;
}

.form-group small {
  display: block;
  margin-top: 0.25rem;
  color: #6b7280;
  font-size: 0.8rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-row .form-group {
  flex: 1;
}

.color-input {
  width: 60px !important;
  height: 40px;
  cursor: pointer;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  border: 1px solid #d1d5db;
}

/* Admin redirect info */
.admin-redirect-info {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
}

.admin-redirect-info .redirect-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.admin-redirect-info p {
  margin: 0.25rem 0 0;
  color: #0369a1;
  font-size: 0.9rem;
}

.admin-redirect-info strong {
  color: #0c4a6e;
}

/* Users */
.users-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.users-header h3 {
  margin: 0;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th {
  text-align: left;
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  font-size: 0.8rem;
  color: #6b7280;
}

.users-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #f3f4f6;
}

.users-table .actions button {
  padding: 0.25rem 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  margin-right: 0.5rem;
}

.users-table .actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.role-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.role-badge.admin {
  background: #fee2e2;
  color: #dc2626;
}

.role-badge.moderateur {
  background: #fef3c7;
  color: #b45309;
}

.role-badge.agent {
  background: #dbeafe;
  color: #1d4ed8;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  width: 100%;
  max-width: 400px;
  margin: 1rem;
}

.modal h3 {
  margin: 0 0 1.5rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

/* Alertes styles */
.alertes-intro {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.alertes-intro p {
  margin: 0;
  color: #0369a1;
}

.inline-select {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.inline-select select {
  width: auto;
  min-width: 150px;
}

.inline-select span {
  color: #6b7280;
}

.alertes-note {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin: 1.5rem 0;
  padding: 1rem;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
}

.alertes-note .note-icon {
  flex-shrink: 0;
  font-size: 1.1rem;
}

.alertes-note span:last-child {
  color: #92400e;
  font-size: 0.9rem;
}
</style>

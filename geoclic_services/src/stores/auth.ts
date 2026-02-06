import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import router from '../router'

/**
 * Types pour l'authentification GéoClic Services
 * Utilise le système unifié geoclic_users
 * Note: geoclic_services utilise role_terrain car c'est l'app desktop
 * pour les mêmes agents terrain qui utilisent geoclic_terrain sur mobile
 */

type RoleTerrain = 'aucun' | 'agent'
type RoleDemandes = 'aucun' | 'agent' | 'admin'
type Role = 'agent' | 'responsable'

export interface Agent {
  id: string
  email: string
  nom: string
  prenom: string
  nom_complet?: string
  actif: boolean
  is_super_admin: boolean
  role_terrain: RoleTerrain
  role_demandes?: RoleDemandes
  role: Role  // Calculé: 'responsable' si is_super_admin ou role_demandes='admin'
  service_id: string | null
  service_nom: string | null
}

// Fonction pour calculer le rôle à partir des données utilisateur
function computeRole(userData: any): Role {
  if (userData.is_super_admin || userData.role_demandes === 'admin') {
    return 'responsable'
  }
  return 'agent'
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const agent = ref<Agent | null>(null)
  const initialized = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isLoggedIn = computed(() => !!token.value && !!agent.value)

  // Nom complet de l'agent
  const fullName = computed(() =>
    agent.value ? `${agent.value.prenom} ${agent.value.nom}` : ''
  )

  // Configurer axios avec le token
  function setAxiosToken(newToken: string | null) {
    if (newToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }

  // Initialiser depuis localStorage
  async function initialize() {
    const storedToken = localStorage.getItem('services_token')
    const storedAgent = localStorage.getItem('services_agent')

    if (storedToken && storedAgent) {
      token.value = storedToken
      agent.value = JSON.parse(storedAgent)
      setAxiosToken(storedToken)

      // Vérifier que le token est toujours valide
      try {
        const response = await axios.get('/api/auth/me')
        const userData = response.data

        // Vérifier que l'utilisateur a toujours accès
        if (!userData.is_super_admin && userData.role_terrain === 'aucun') {
          await logout()
          return
        }

        // Ajouter le rôle calculé
        userData.role = computeRole(userData)
        agent.value = userData
        localStorage.setItem('services_agent', JSON.stringify(userData))
      } catch {
        // Token invalide, déconnecter
        await logout()
      }
    }

    initialized.value = true
  }

  // Connexion
  async function login(email: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)

      const response = await axios.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })

      const userData = response.data.user

      // Vérifier que l'utilisateur a accès à Services (role_terrain)
      if (!userData.is_super_admin && userData.role_terrain === 'aucun') {
        error.value = 'Vous n\'avez pas accès à GéoClic Services'
        return false
      }

      // Ajouter le rôle calculé
      userData.role = computeRole(userData)

      token.value = response.data.access_token
      agent.value = userData

      // Sauvegarder
      localStorage.setItem('services_token', response.data.access_token)
      localStorage.setItem('services_agent', JSON.stringify(userData))
      setAxiosToken(response.data.access_token)

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur de connexion'
      return false
    } finally {
      loading.value = false
    }
  }

  // Déconnexion
  async function logout() {
    token.value = null
    agent.value = null
    localStorage.removeItem('services_token')
    localStorage.removeItem('services_agent')
    setAxiosToken(null)

    router.push('/login')
  }

  // Changer mot de passe
  async function changePassword(currentPassword: string, newPassword: string): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      await axios.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      })
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du changement de mot de passe'
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    token,
    agent,
    initialized,
    loading,
    error,
    isLoggedIn,
    fullName,
    initialize,
    login,
    logout,
    changePassword
  }
})

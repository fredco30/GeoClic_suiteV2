import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import router from '../router'

/**
 * Types pour l'authentification GéoClic Terrain (PWA)
 * Utilise le système unifié geoclic_users
 */

type RoleTerrain = 'aucun' | 'agent'

export interface Agent {
  id: string
  email: string
  nom: string
  prenom: string
  actif: boolean
  is_super_admin: boolean
  role_terrain: RoleTerrain
  service_id: string | null
  service_nom: string | null
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
    const storedToken = localStorage.getItem('terrain_token')
    const storedAgent = localStorage.getItem('terrain_agent')

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

        agent.value = userData
        localStorage.setItem('terrain_agent', JSON.stringify(userData))
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

      // Vérifier que l'utilisateur a accès à Terrain (role_terrain)
      if (!userData.is_super_admin && userData.role_terrain === 'aucun') {
        error.value = 'Vous n\'avez pas accès à GéoClic Terrain'
        return false
      }

      token.value = response.data.access_token
      agent.value = userData

      // Sauvegarder
      localStorage.setItem('terrain_token', response.data.access_token)
      localStorage.setItem('terrain_agent', JSON.stringify(userData))
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
    localStorage.removeItem('terrain_token')
    localStorage.removeItem('terrain_agent')
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

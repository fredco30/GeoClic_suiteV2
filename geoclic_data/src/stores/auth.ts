/**
 * stores/auth.ts
 *
 * Store Pinia pour l'authentification GéoClic Data
 * Utilise le système unifié geoclic_users
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { jwtDecode } from 'jwt-decode'
import router from '@/router'

type RoleData = 'aucun' | 'admin'

interface User {
  id: string
  email: string
  nom: string
  prenom: string
  actif: boolean
  is_super_admin: boolean
  role_data: RoleData
  role_demandes: string
  role_sig: string
  role_terrain: string
  service_id: string | null
  service_nom: string | null
  last_login: string | null
  created_at: string
}

// Helper pour obtenir le nom complet de l'utilisateur
export function getUserDisplayName(user: User | null): string {
  if (!user) return 'Utilisateur'
  if (user.prenom && user.nom) return `${user.prenom} ${user.nom}`
  if (user.nom) return user.nom
  return user.email
}

interface JWTPayload {
  sub: string
  exp: number
  email: string
  is_super_admin: boolean
  role_data: string
  role_demandes: string
  role_sig: string
  role_terrain: string
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('data_auth_token'))
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Configure axios with token if exists
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  // Getters
  const isAuthenticated = computed(() => !!token.value && !isTokenExpired())

  // Super admin ou admin data
  const isAdmin = computed(() =>
    user.value?.is_super_admin || user.value?.role_data === 'admin'
  )

  // Utilisateur est super admin
  const isSuperAdmin = computed(() => user.value?.is_super_admin === true)

  // Nom complet de l'utilisateur
  const fullName = computed(() =>
    user.value ? `${user.value.prenom} ${user.value.nom}` : ''
  )

  // Helpers
  function isTokenExpired(): boolean {
    if (!token.value) return true
    try {
      const decoded = jwtDecode<JWTPayload>(token.value)
      return decoded.exp * 1000 < Date.now()
    } catch {
      return true
    }
  }

  // Actions
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

      // Vérifier que l'utilisateur a accès à Data
      if (!userData.is_super_admin && userData.role_data === 'aucun') {
        error.value = 'Vous n\'avez pas accès à GéoClic Data'
        return false
      }

      token.value = response.data.access_token
      user.value = userData

      localStorage.setItem('data_auth_token', response.data.access_token)
      localStorage.setItem('data_user', JSON.stringify(userData))
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur de connexion'
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchUser(): Promise<void> {
    if (!token.value) return

    try {
      const response = await axios.get('/api/auth/me')
      const userData = response.data

      // Vérifier que l'utilisateur a toujours accès
      if (!userData.is_super_admin && userData.role_data === 'aucun') {
        logout()
        return
      }

      user.value = userData
      localStorage.setItem('data_user', JSON.stringify(userData))
    } catch {
      logout()
    }
  }

  function logout(): void {
    token.value = null
    user.value = null
    localStorage.removeItem('data_auth_token')
    localStorage.removeItem('data_user')
    delete axios.defaults.headers.common['Authorization']
    router.push('/login')
  }

  function restoreSession(): void {
    const savedUser = localStorage.getItem('data_user')
    if (savedUser && token.value && !isTokenExpired()) {
      user.value = JSON.parse(savedUser)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    } else if (token.value && isTokenExpired()) {
      logout()
    }
  }

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
    // State
    token,
    user,
    loading,
    error,
    // Getters
    isAuthenticated,
    isAdmin,
    isSuperAdmin,
    fullName,
    // Actions
    login,
    logout,
    fetchUser,
    restoreSession,
    changePassword,
  }
})

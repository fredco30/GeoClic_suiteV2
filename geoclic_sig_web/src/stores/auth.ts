import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

/**
 * Types pour l'authentification GéoClic SIG
 * Utilise le système unifié geoclic_users
 */

type RoleSig = 'aucun' | 'lecture' | 'edition'

interface User {
  id: string
  email: string
  nom: string
  prenom: string
  actif: boolean
  is_super_admin: boolean
  role_sig: RoleSig
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('sig_auth_token'))
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // Super admin ou utilisateur avec rôle édition
  const isAdmin = computed(() => user.value?.is_super_admin === true)

  // Peut éditer (super admin ou role_sig = 'edition')
  const canEdit = computed(() =>
    user.value?.is_super_admin || user.value?.role_sig === 'edition'
  )

  // Peut voir (super admin, lecture ou édition)
  const canView = computed(() =>
    user.value?.is_super_admin ||
    user.value?.role_sig === 'lecture' ||
    user.value?.role_sig === 'edition'
  )

  // Nom complet de l'utilisateur
  const fullName = computed(() =>
    user.value ? `${user.value.prenom} ${user.value.nom}` : ''
  )

  // Configure axios with token
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  async function login(email: string, password: string): Promise<boolean> {
    loading.value = true
    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)
      const response = await axios.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })

      const userData = response.data.user

      // Vérifier que l'utilisateur a accès au SIG
      if (!userData.is_super_admin && userData.role_sig === 'aucun') {
        throw new Error('Vous n\'avez pas accès à GéoClic SIG')
      }

      token.value = response.data.access_token
      user.value = userData

      localStorage.setItem('sig_auth_token', token.value!)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`

      return true
    } catch (error: any) {
      console.error('Login error:', error)
      throw new Error(error.response?.data?.detail || error.message || 'Identifiants incorrects')
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('sig_auth_token')
    delete axios.defaults.headers.common['Authorization']
  }

  async function checkAuth(): Promise<boolean> {
    if (!token.value) return false

    try {
      const response = await axios.get('/api/auth/me')
      const userData = response.data

      // Vérifier que l'utilisateur a toujours accès
      if (!userData.is_super_admin && userData.role_sig === 'aucun') {
        logout()
        return false
      }

      user.value = userData
      return true
    } catch {
      logout()
      return false
    }
  }

  async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await axios.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    })
  }

  return {
    user,
    token,
    loading,
    isAuthenticated,
    isAdmin,
    canEdit,
    canView,
    fullName,
    login,
    logout,
    checkAuth,
    changePassword
  }
})

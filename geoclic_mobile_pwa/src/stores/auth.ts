import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, type User } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // État
  const user = ref<User | null>(api.getStoredUser())
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const isAuthenticated = computed(() => !!user.value && !!api.getStoredToken())
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userName = computed(() => user.value?.name || user.value?.email || '')
  const userRole = computed(() => user.value?.role || '')

  // Permissions
  const allowedProjects = computed(() => user.value?.permissions?.projets || [])
  const allowedCategories = computed(() => user.value?.permissions?.categories || [])

  const hasProjectAccess = (projectId: string): boolean => {
    if (isAdmin.value) return true
    if (allowedProjects.value.length === 0) return true // Pas de restriction
    return allowedProjects.value.includes(projectId)
  }

  const hasCategoryAccess = (categoryCode: string): boolean => {
    if (isAdmin.value) return true
    if (allowedCategories.value.length === 0) return true
    // Vérifier si le code ou un de ses parents est autorisé
    return allowedCategories.value.some(allowed =>
      categoryCode.startsWith(allowed)
    )
  }

  // Actions
  async function login(email: string, password: string): Promise<boolean> {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.login(email, password)
      user.value = response.user
      return true
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { status?: number; data?: { detail?: string } } }
        if (axiosError.response?.status === 401) {
          error.value = 'Email ou mot de passe incorrect'
        } else if (axiosError.response?.data?.detail) {
          error.value = axiosError.response.data.detail
        } else {
          error.value = 'Erreur de connexion au serveur'
        }
      } else {
        error.value = 'Erreur de connexion'
      }
      return false
    } finally {
      isLoading.value = false
    }
  }

  function logout(): void {
    api.logout()
    user.value = null
  }

  function clearError(): void {
    error.value = null
  }

  // Restaurer l'utilisateur depuis le stockage local
  function restoreSession(): boolean {
    const storedUser = api.getStoredUser()
    const token = api.getStoredToken()

    if (storedUser && token) {
      user.value = storedUser
      return true
    }
    return false
  }

  return {
    // État
    user,
    isLoading,
    error,

    // Computed
    isAuthenticated,
    isAdmin,
    userName,
    userRole,
    allowedProjects,
    allowedCategories,

    // Méthodes
    login,
    logout,
    clearError,
    restoreSession,
    hasProjectAccess,
    hasCategoryAccess
  }
})

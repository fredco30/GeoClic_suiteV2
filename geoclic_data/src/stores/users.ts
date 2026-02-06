/**
 * stores/users.ts
 *
 * Store Pinia pour la gestion des utilisateurs GéoClic Suite
 * Utilise la table geoclic_users avec rôles par application
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// Types pour les rôles par application
export type RoleData = 'aucun' | 'admin'
export type RoleDemandes = 'aucun' | 'agent' | 'admin'
export type RoleSig = 'aucun' | 'lecture' | 'edition'
export type RoleTerrain = 'aucun' | 'agent'

export interface User {
  id: string
  email: string
  nom: string
  prenom: string
  actif: boolean
  is_super_admin: boolean
  role_data: RoleData
  role_demandes: RoleDemandes
  role_sig: RoleSig
  role_terrain: RoleTerrain
  service_id: string | null
  service_nom: string | null
  last_login: string | null
  created_at: string
}

export interface UserCreate {
  email: string
  password: string
  nom: string
  prenom: string
  role_data?: RoleData
  role_demandes?: RoleDemandes
  role_sig?: RoleSig
  role_terrain?: RoleTerrain
  service_id?: string | null
}

export interface UserUpdate {
  email?: string
  password?: string
  nom?: string
  prenom?: string
  actif?: boolean
  role_data?: RoleData
  role_demandes?: RoleDemandes
  role_sig?: RoleSig
  role_terrain?: RoleTerrain
  service_id?: string | null
}

export interface Service {
  id: string
  nom: string
}

// Labels pour les rôles
export const ROLE_DATA_LABELS: Record<RoleData, string> = {
  aucun: 'Aucun accès',
  admin: 'Administrateur',
}

export const ROLE_DEMANDES_LABELS: Record<RoleDemandes, string> = {
  aucun: 'Aucun accès',
  agent: 'Agent',
  admin: 'Administrateur',
}

export const ROLE_SIG_LABELS: Record<RoleSig, string> = {
  aucun: 'Aucun accès',
  lecture: 'Lecture seule',
  edition: 'Édition',
}

export const ROLE_TERRAIN_LABELS: Record<RoleTerrain, string> = {
  aucun: 'Aucun accès',
  agent: 'Agent terrain',
}

// Couleurs pour les chips
export const ROLE_COLORS: Record<string, string> = {
  aucun: 'grey',
  admin: 'error',
  agent: 'success',
  lecture: 'info',
  edition: 'warning',
}

// API base URL
const API_BASE = '/api/auth'

export const useUsersStore = defineStore('users', () => {
  // State
  const users = ref<User[]>([])
  const services = ref<Service[]>([])
  const selectedUser = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const activeUsers = computed(() => users.value.filter(u => u.actif))
  const inactiveUsers = computed(() => users.value.filter(u => !u.actif))
  const superAdmins = computed(() => users.value.filter(u => u.is_super_admin))

  const getById = computed(() => (id: string) =>
    users.value.find(u => u.id === id)
  )

  // Statistiques par application
  const usersWithDataAccess = computed(() =>
    users.value.filter(u => u.role_data !== 'aucun' || u.is_super_admin)
  )
  const usersWithDemandesAccess = computed(() =>
    users.value.filter(u => u.role_demandes !== 'aucun' || u.is_super_admin)
  )
  const usersWithSigAccess = computed(() =>
    users.value.filter(u => u.role_sig !== 'aucun' || u.is_super_admin)
  )
  const usersWithTerrainAccess = computed(() =>
    users.value.filter(u => u.role_terrain !== 'aucun' || u.is_super_admin)
  )

  // Actions
  async function fetchAll(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${API_BASE}/users`)
      users.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du chargement des utilisateurs'
      console.error('Erreur fetchAll users:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchServices(): Promise<void> {
    try {
      const response = await axios.get(`${API_BASE}/services`)
      services.value = response.data
    } catch (err: any) {
      console.error('Erreur chargement services:', err)
    }
  }

  async function fetchById(id: string): Promise<User | null> {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${API_BASE}/users/${id}`)
      selectedUser.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du chargement de l\'utilisateur'
      return null
    } finally {
      loading.value = false
    }
  }

  async function createUser(data: UserCreate): Promise<User | null> {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post(`${API_BASE}/users`, data)
      const newUser = response.data
      users.value.push(newUser)
      return newUser
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la création'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateUser(id: string, data: UserUpdate): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      const response = await axios.put(`${API_BASE}/users/${id}`, data)
      const updated = response.data
      const index = users.value.findIndex(u => u.id === id)
      if (index !== -1) {
        users.value[index] = updated
      }
      if (selectedUser.value?.id === id) {
        selectedUser.value = updated
      }
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la mise à jour'
      return false
    } finally {
      loading.value = false
    }
  }

  async function deleteUser(id: string): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      await axios.delete(`${API_BASE}/users/${id}`)
      users.value = users.value.filter(u => u.id !== id)
      if (selectedUser.value?.id === id) {
        selectedUser.value = null
      }
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la suppression'
      return false
    } finally {
      loading.value = false
    }
  }

  async function toggleActive(id: string): Promise<boolean> {
    const user = getById.value(id)
    if (!user) return false
    return updateUser(id, { actif: !user.actif })
  }

  async function updateSuperAdmin(data: {
    email: string
    password: string
    nom: string
    prenom: string
  }): Promise<User | null> {
    loading.value = true
    error.value = null

    try {
      const response = await axios.put(`${API_BASE}/super-admin`, data)
      const newSuperAdmin = response.data
      // Recharger la liste des utilisateurs pour refléter les changements
      await fetchAll()
      return newSuperAdmin
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du changement de super admin'
      return null
    } finally {
      loading.value = false
    }
  }

  function selectUser(user: User | null): void {
    selectedUser.value = user
  }

  function clearError(): void {
    error.value = null
  }

  // Helper pour obtenir les apps accessibles d'un utilisateur
  function getAccessibleApps(user: User): string[] {
    const apps: string[] = []
    if (user.is_super_admin) {
      return ['Data', 'Demandes', 'SIG', 'Terrain']
    }
    if (user.role_data !== 'aucun') apps.push('Data')
    if (user.role_demandes !== 'aucun') apps.push('Demandes')
    if (user.role_sig !== 'aucun') apps.push('SIG')
    if (user.role_terrain !== 'aucun') apps.push('Terrain')
    return apps
  }

  return {
    // State
    users,
    services,
    selectedUser,
    loading,
    error,
    // Getters
    activeUsers,
    inactiveUsers,
    superAdmins,
    getById,
    usersWithDataAccess,
    usersWithDemandesAccess,
    usersWithSigAccess,
    usersWithTerrainAccess,
    // Actions
    fetchAll,
    fetchServices,
    fetchById,
    createUser,
    updateUser,
    deleteUser,
    toggleActive,
    updateSuperAdmin,
    selectUser,
    clearError,
    getAccessibleApps,
  }
})

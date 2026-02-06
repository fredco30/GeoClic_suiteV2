import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services/api'
import axios from 'axios'

export interface Theme {
  primaryColor: string
  secondaryColor: string
  accentColor: string
  logo?: string
  bannerImage?: string
}

export interface Category {
  id: string
  nom: string
  description?: string
  icone: string
  couleur: number
  parent_id: string | null
  actif: boolean
  children?: Category[]
}

export const useConfigStore = defineStore('config', () => {
  const projectId = ref<string>('')
  const collectiviteName = ref<string>('')
  const theme = ref<Theme>({
    primaryColor: '#2563eb',
    secondaryColor: '#1f2937',
    accentColor: '#10b981',
  })
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const contactEmail = ref<string>('')
  const contactTelephone = ref<string>('')
  const siteWeb = ref<string>('')

  async function loadBranding() {
    try {
      const response = await axios.get('/api/settings/branding')
      const data = response.data
      if (data.nom_collectivite) {
        collectiviteName.value = data.nom_collectivite
      }
      theme.value.primaryColor = data.primary_color || '#2563eb'
      theme.value.secondaryColor = data.secondary_color || '#1f2937'
      theme.value.accentColor = data.accent_color || '#10b981'
      if (data.logo_url) {
        theme.value.logo = data.logo_url
      }
      if (data.email_contact) {
        contactEmail.value = data.email_contact
      }
      if (data.telephone) {
        contactTelephone.value = data.telephone
      }
      if (data.site_web) {
        siteWeb.value = data.site_web
      }
      // Appliquer les CSS variables dynamiquement
      applyThemeColors()
    } catch (error) {
      console.error('Erreur chargement branding:', error)
      // Pas grave, on garde les valeurs par défaut
    }
  }

  function applyThemeColors() {
    const root = document.documentElement
    root.style.setProperty('--primary-color', theme.value.primaryColor)
    // Calculer une version plus sombre du primary pour les hovers
    root.style.setProperty('--primary-dark', darkenColor(theme.value.primaryColor, 15))
    // Calculer une version claire pour les backgrounds
    root.style.setProperty('--primary-light', lightenColor(theme.value.primaryColor, 85))
    root.style.setProperty('--success', theme.value.accentColor)
  }

  function darkenColor(hex: string, percent: number): string {
    const num = parseInt(hex.replace('#', ''), 16)
    const r = Math.max(0, (num >> 16) - Math.round(255 * percent / 100))
    const g = Math.max(0, ((num >> 8) & 0x00ff) - Math.round(255 * percent / 100))
    const b = Math.max(0, (num & 0x0000ff) - Math.round(255 * percent / 100))
    return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`
  }

  function lightenColor(hex: string, percent: number): string {
    const num = parseInt(hex.replace('#', ''), 16)
    const r = Math.min(255, (num >> 16) + Math.round(255 * percent / 100))
    const g = Math.min(255, ((num >> 8) & 0x00ff) + Math.round(255 * percent / 100))
    const b = Math.min(255, (num & 0x0000ff) + Math.round(255 * percent / 100))
    return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`
  }

  async function loadConfig() {
    loading.value = true
    try {
      // Charger le branding (nom collectivité, couleurs, logo)
      await loadBranding()

      // 1. Vérifier si un project_id est passé dans l'URL
      const urlParams = new URLSearchParams(window.location.search)
      const urlProjectId = urlParams.get('project')

      if (urlProjectId) {
        await loadProjectConfig(urlProjectId)
        return
      }

      // 2. Chercher le projet système "Signalements Citoyens" (prioritaire)
      const systemProject = await api.getSystemProject()
      if (systemProject) {
        await loadProjectConfig(systemProject.id)
        return
      }

      // 3. Fallback: charger depuis le localStorage
      const savedProjectId = localStorage.getItem('portail_project_id')
      if (savedProjectId) {
        projectId.value = savedProjectId
        await loadProjectConfig(savedProjectId)
        return
      }

      // 4. Fallback ultime: charger les catégories sans project_id
      await loadCategoriesDirectly()
    } catch (error) {
      console.error('Erreur chargement config:', error)
      // Fallback: charger les catégories directement
      await loadCategoriesDirectly()
    } finally {
      loading.value = false
    }
  }

  // Charger les catégories directement sans project_id (fallback)
  async function loadCategoriesDirectly() {
    try {
      const categoriesData = await api.getCategoriesAll()

      categories.value = categoriesData.map((cat: Record<string, unknown>) => ({
        ...cat,
        couleur: typeof cat.couleur === 'string' ? parseInt(cat.couleur as string, 10) : (cat.couleur as number) || 0,
        icone: (cat.icone as string) || 'report_problem',
        parent_id: cat.parent_id || null,
        actif: cat.actif !== false
      })) as Category[]

      // Extraire le project_id de la première catégorie si disponible
      if (categoriesData.length > 0 && categoriesData[0].project_id) {
        projectId.value = categoriesData[0].project_id as string
        localStorage.setItem('portail_project_id', projectId.value)
      }
    } catch (error) {
      console.error('Erreur chargement catégories directes:', error)
    }
  }

  async function loadProjectConfig(id: string) {
    try {
      // Charger les catégories
      const categoriesData = await api.getCategories(id)

      // Normaliser les données (s'assurer que couleur est un number)
      categories.value = categoriesData.map((cat: Record<string, unknown>) => ({
        ...cat,
        couleur: typeof cat.couleur === 'string' ? parseInt(cat.couleur as string, 10) : (cat.couleur as number) || 0,
        icone: (cat.icone as string) || 'report_problem',
        parent_id: cat.parent_id || null,
        actif: cat.actif !== false
      })) as Category[]

      projectId.value = id
      localStorage.setItem('portail_project_id', id)
    } catch (error) {
      console.error('Erreur chargement projet:', error)
    }
  }

  function setProject(id: string, name: string) {
    projectId.value = id
    collectiviteName.value = name
    localStorage.setItem('portail_project_id', id)
  }

  return {
    projectId,
    collectiviteName,
    theme,
    categories,
    loading,
    contactEmail,
    contactTelephone,
    siteWeb,
    loadConfig,
    loadBranding,
    loadProjectConfig,
    setProject,
  }
})

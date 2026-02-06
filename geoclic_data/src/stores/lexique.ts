/**
 * stores/lexique.ts
 *
 * Store Pinia pour la gestion du lexique (catégories hiérarchiques)
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { lexiqueAPI, champsAPI } from '@/services/api'

export interface LexiqueEntry {
  id: string
  code: string
  libelle: string
  parent_id: string | null
  niveau: number
  icone: string | null
  couleur: string | null
  actif: boolean
  ordre: number
  description?: string | null
  children?: LexiqueEntry[]
}

export interface ChampDynamique {
  id: string
  lexique_id: string
  nom: string
  type: 'text' | 'number' | 'date' | 'select' | 'multiselect' | 'photo' | 'file' | 'geometry' | 'slider' | 'color' | 'signature' | 'qrcode' | 'calculated'
  obligatoire: boolean
  ordre: number
  options?: string[] // Pour select/multiselect
  min?: number // Pour number/slider
  max?: number // Pour number/slider
  formule?: string // Pour calculated
  actif: boolean
  // Options avancées
  default_value?: string | number | null // Valeur par défaut
  display_mode?: 'auto' | 'dropdown' | 'search_select' // Mode d'affichage mobile
  search_threshold?: number // Seuil pour mode recherche (défaut: 10)
  condition_field?: string | null // ID du champ de condition
  condition_operator?: '=' | '!=' | 'in' // Opérateur de condition
  condition_value?: string[] // Valeurs de condition
}

// Mapping API -> Frontend
function mapApiToFrontend(apiEntry: any): LexiqueEntry {
  return {
    id: String(apiEntry.id),
    code: apiEntry.code,
    libelle: apiEntry.label,
    parent_id: apiEntry.parent_code || null,
    niveau: apiEntry.level || 0,
    icone: apiEntry.icon_name || null,
    couleur: apiEntry.color_value ? `#${apiEntry.color_value.toString(16).padStart(6, '0')}` : null,
    actif: apiEntry.is_active ?? true,
    ordre: apiEntry.display_order || 0,
    description: apiEntry.metadata?.description || null,
    children: apiEntry.children?.map(mapApiToFrontend) || undefined,
  }
}

// Mapping Frontend -> API
function mapFrontendToApi(entry: Partial<LexiqueEntry>): any {
  const apiData: any = {}

  if (entry.code !== undefined) apiData.code = entry.code
  if (entry.libelle !== undefined) apiData.label = entry.libelle
  if (entry.parent_id !== undefined) apiData.parent_code = entry.parent_id
  if (entry.niveau !== undefined) apiData.level = entry.niveau
  if (entry.icone !== undefined) apiData.icon_name = entry.icone
  if (entry.couleur !== undefined) {
    // Convertir couleur hex en nombre
    if (entry.couleur && entry.couleur.startsWith('#')) {
      apiData.color_value = parseInt(entry.couleur.slice(1), 16)
    } else {
      apiData.color_value = null
    }
  }
  if (entry.actif !== undefined) apiData.is_active = entry.actif
  if (entry.ordre !== undefined) apiData.display_order = entry.ordre
  // Stocker la description dans metadata
  if (entry.description !== undefined) {
    apiData.metadata = { description: entry.description }
  }

  return apiData
}

// Construire l'arbre à partir d'une liste plate
function buildTree(entries: LexiqueEntry[]): LexiqueEntry[] {
  const map = new Map<string | null, LexiqueEntry[]>()

  // Grouper par parent_id
  entries.forEach(entry => {
    const parentId = entry.parent_id
    if (!map.has(parentId)) {
      map.set(parentId, [])
    }
    map.get(parentId)!.push({ ...entry })
  })

  // Construire l'arbre récursivement
  function attachChildren(parentId: string | null): LexiqueEntry[] {
    const children = map.get(parentId) || []
    return children
      .sort((a, b) => a.ordre - b.ordre || a.libelle.localeCompare(b.libelle))
      .map(entry => ({
        ...entry,
        children: attachChildren(entry.code), // parent_code = code du parent
      }))
  }

  return attachChildren(null)
}

export const useLexiqueStore = defineStore('lexique', () => {
  // State
  const entries = ref<LexiqueEntry[]>([])
  const tree = ref<LexiqueEntry[]>([])
  const champs = ref<Map<string, ChampDynamique[]>>(new Map())
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedEntry = ref<LexiqueEntry | null>(null)

  // Getters
  const flatList = computed(() => entries.value)

  const getByNiveau = computed(() => (niveau: number) =>
    entries.value.filter(e => e.niveau === niveau)
  )

  const getChildren = computed(() => (parentId: string | null) =>
    entries.value.filter(e => e.parent_id === parentId)
  )

  const getById = computed(() => (id: string) =>
    entries.value.find(e => e.id === id)
  )

  const getByCode = computed(() => (code: string) =>
    entries.value.find(e => e.code === code)
  )

  const getChampsForLexique = computed(() => (lexiqueId: string) =>
    champs.value.get(lexiqueId) || []
  )

  // Actions
  async function fetchAll(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const apiData = await lexiqueAPI.getAll()
      entries.value = apiData.map(mapApiToFrontend)
      // Reconstruire l'arbre
      tree.value = buildTree(entries.value)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du chargement du lexique'
      console.error('fetchAll error:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchTree(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const apiData = await lexiqueAPI.getTree()
      // L'API retourne { roots: [...], total_entries, max_depth }
      if (apiData.roots) {
        entries.value = apiData.roots.map(mapApiToFrontend)
        tree.value = buildTree(entries.value)
      } else {
        // Fallback: si l'API retourne directement un tableau
        entries.value = (Array.isArray(apiData) ? apiData : []).map(mapApiToFrontend)
        tree.value = buildTree(entries.value)
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du chargement de l\'arborescence'
      console.error('fetchTree error:', err)
    } finally {
      loading.value = false
    }
  }

  async function createEntry(data: Partial<LexiqueEntry>): Promise<LexiqueEntry | null> {
    loading.value = true
    error.value = null

    try {
      const apiData = mapFrontendToApi(data)
      const response = await lexiqueAPI.create(apiData)
      const newEntry = mapApiToFrontend(response)
      entries.value.push(newEntry)
      tree.value = buildTree(entries.value)
      return newEntry
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la création'
      console.error('createEntry error:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateEntry(id: string, data: Partial<LexiqueEntry>): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      // Trouver le code correspondant à l'id
      const entry = entries.value.find(e => e.id === id)
      if (!entry) {
        throw new Error('Entrée non trouvée')
      }

      const apiData = mapFrontendToApi(data)
      const response = await lexiqueAPI.update(entry.code, apiData)
      const updated = mapApiToFrontend(response)

      const index = entries.value.findIndex(e => e.id === id)
      if (index !== -1) {
        entries.value[index] = updated
      }
      tree.value = buildTree(entries.value)
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la mise à jour'
      console.error('updateEntry error:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  async function deleteEntry(id: string): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      // Trouver le code correspondant à l'id
      const entry = entries.value.find(e => e.id === id)
      if (!entry) {
        throw new Error('Entrée non trouvée')
      }

      await lexiqueAPI.delete(entry.code)
      entries.value = entries.value.filter(e => e.id !== id)
      tree.value = buildTree(entries.value)
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la suppression'
      console.error('deleteEntry error:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  async function reorderEntries(items: { id: string; ordre: number }[]): Promise<boolean> {
    try {
      await lexiqueAPI.reorder(items)
      await fetchAll()
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors du réordonnancement'
      return false
    }
  }

  // Champs dynamiques
  async function fetchChamps(lexiqueId: string): Promise<void> {
    try {
      // Trouver le code correspondant à l'id
      const entry = entries.value.find(e => e.id === lexiqueId)
      const code = entry?.code || lexiqueId

      const champsData = await champsAPI.getByLexique(code)
      champs.value.set(lexiqueId, champsData)
    } catch (err: any) {
      console.error('Erreur chargement champs:', err)
    }
  }

  async function createChamp(data: Partial<ChampDynamique>): Promise<ChampDynamique | null> {
    try {
      const newChamp = await champsAPI.create(data)
      const existing = champs.value.get(data.lexique_id!) || []
      champs.value.set(data.lexique_id!, [...existing, newChamp])
      return newChamp
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la création du champ'
      return null
    }
  }

  async function updateChamp(id: string, data: Partial<ChampDynamique>): Promise<boolean> {
    try {
      const updated = await champsAPI.update(id, data)
      if (data.lexique_id) {
        await fetchChamps(data.lexique_id)
      }
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la mise à jour du champ'
      return false
    }
  }

  async function deleteChamp(id: string, lexiqueId: string): Promise<boolean> {
    try {
      await champsAPI.delete(id)
      const existing = champs.value.get(lexiqueId) || []
      champs.value.set(lexiqueId, existing.filter(c => c.id !== id))
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erreur lors de la suppression du champ'
      return false
    }
  }

  function selectEntry(entry: LexiqueEntry | null): void {
    selectedEntry.value = entry
  }

  return {
    // State
    entries,
    tree,
    champs,
    loading,
    error,
    selectedEntry,
    // Getters
    flatList,
    getByNiveau,
    getChildren,
    getById,
    getByCode,
    getChampsForLexique,
    // Actions
    fetchAll,
    fetchTree,
    createEntry,
    updateEntry,
    deleteEntry,
    reorderEntries,
    fetchChamps,
    createChamp,
    updateChamp,
    deleteChamp,
    selectEntry,
  }
})

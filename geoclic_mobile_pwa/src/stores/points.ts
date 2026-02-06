import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, type Point, type LexiqueItem, type Project, type ChampDynamique } from '@/services/api'
import { offlineService } from '@/services/offline'

export const usePointsStore = defineStore('points', () => {
  // État
  const points = ref<Point[]>([])
  const lexique = ref<LexiqueItem[]>([])
  const projects = ref<Project[]>([])
  const champs = ref<ChampDynamique[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const currentPage = ref(1)
  const totalPages = ref(1)
  const totalPoints = ref(0)
  const selectedProjectId = ref<string | null>(null)
  const isOnline = ref(navigator.onLine)

  // Écouter les changements de connexion
  if (typeof window !== 'undefined') {
    window.addEventListener('online', () => { isOnline.value = true })
    window.addEventListener('offline', () => { isOnline.value = false })
  }

  // Computed
  const pendingCount = ref(0)

  const lexiqueTree = computed(() => {
    // Construire l'arbre hiérarchique
    const tree: (LexiqueItem & { children: LexiqueItem[] })[] = []
    const map = new Map<string, LexiqueItem & { children: LexiqueItem[] }>()

    // Créer un map de tous les éléments
    lexique.value.forEach(item => {
      map.set(item.code, { ...item, children: [] })
    })

    // Construire l'arbre
    lexique.value.forEach(item => {
      const node = map.get(item.code)!
      if (item.parent_code && map.has(item.parent_code)) {
        map.get(item.parent_code)!.children.push(node)
      } else if (!item.parent_code || item.level === 1) {
        tree.push(node)
      }
    })

    return tree
  })

  // Initialiser le service offline
  async function initOffline(): Promise<void> {
    try {
      await offlineService.init()
      await updatePendingCount()
    } catch (err) {
      console.error('Erreur initialisation offline:', err)
    }
  }

  async function updatePendingCount(): Promise<void> {
    try {
      const count = await offlineService.getPendingPointsCount()
      pendingCount.value = count
    } catch {
      pendingCount.value = 0
    }
  }

  // Charger les points
  async function loadPoints(page = 1): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      if (isOnline.value) {
        const params: Record<string, unknown> = { page, limit: 50 }
        if (selectedProjectId.value) {
          params.project_id = selectedProjectId.value
        }

        const response = await api.getPoints(params as Parameters<typeof api.getPoints>[0])
        points.value = response.items
        currentPage.value = response.page
        totalPages.value = response.pages
        totalPoints.value = response.total

        // Sauvegarder en cache local
        for (const point of response.items) {
          await offlineService.savePoint(point)
        }
      } else {
        // Mode hors-ligne
        const cachedPoints = await offlineService.getAllPoints()
        points.value = cachedPoints
        totalPoints.value = cachedPoints.length
        totalPages.value = 1
        currentPage.value = 1
      }
    } catch (err) {
      error.value = 'Erreur lors du chargement des points'
      console.error(err)

      // Fallback vers le cache
      try {
        const cachedPoints = await offlineService.getAllPoints()
        points.value = cachedPoints
      } catch {
        points.value = []
      }
    } finally {
      isLoading.value = false
    }
  }

  // Charger le lexique
  async function loadLexique(): Promise<void> {
    try {
      if (isOnline.value) {
        const items = await api.getLexique()
        lexique.value = items
        try {
          await offlineService.init()
          await offlineService.saveLexique(items)
        } catch (e) {
          console.warn('Erreur sauvegarde lexique offline:', e)
        }
      } else {
        await offlineService.init()
        lexique.value = await offlineService.getLexique()
      }
    } catch (err) {
      console.error('Erreur chargement lexique:', err)
      // Fallback
      try {
        await offlineService.init()
        lexique.value = await offlineService.getLexique()
      } catch {
        lexique.value = []
      }
    }
  }

  // Charger les projets
  async function loadProjects(): Promise<void> {
    try {
      if (isOnline.value) {
        const items = await api.getProjects()
        projects.value = items
        try {
          await offlineService.init()
          await offlineService.saveProjects(items)
        } catch (e) {
          console.warn('Erreur sauvegarde projets offline:', e)
        }
      } else {
        await offlineService.init()
        projects.value = await offlineService.getProjects()
      }
    } catch (err) {
      console.error('Erreur chargement projets:', err)
      try {
        await offlineService.init()
        projects.value = await offlineService.getProjects()
      } catch {
        projects.value = []
      }
    }
  }

  // Charger les champs dynamiques depuis le cache local
  async function loadChamps(): Promise<void> {
    try {
      await offlineService.init()
      champs.value = await offlineService.getChamps()
    } catch (err) {
      console.error('Erreur chargement champs:', err)
      champs.value = []
    }
  }

  // Charger les champs dynamiques pour un code lexique spécifique
  async function loadChampsForLexique(lexiqueCode: string, projectId?: string): Promise<ChampDynamique[]> {
    if (!lexiqueCode) return []

    console.log(`[loadChampsForLexique] Loading champs for lexique: ${lexiqueCode}, project: ${projectId || 'none'}`)

    try {
      if (isOnline.value) {
        // Charger les champs pour ce code lexique spécifique
        const champsFromApi = await api.getChampsByLexique(lexiqueCode, projectId)
        console.log(`[loadChampsForLexique] API returned ${champsFromApi.length} champs:`, champsFromApi)

        // Convertir en objets simples via JSON pour éviter DataCloneError
        // Note: L'API retourne 'lexique_id' mais le frontend utilise 'lexique_code'
        const champsForCode: ChampDynamique[] = JSON.parse(JSON.stringify(
          champsFromApi.map(ch => ({
            id: String(ch.id),
            lexique_code: String(ch.lexique_id || ch.lexique_code || lexiqueCode),
            nom: String(ch.nom || ''),
            type: ch.type,
            obligatoire: Boolean(ch.obligatoire),
            ordre: Number(ch.ordre) || 0,
            options: ch.options ? [...ch.options] : undefined,
            min: ch.min != null ? Number(ch.min) : undefined,
            max: ch.max != null ? Number(ch.max) : undefined,
            default_value: ch.default_value ? String(ch.default_value) : undefined,
            project_id: ch.project_id ? String(ch.project_id) : undefined,
            condition_field: ch.condition_field || undefined,
            condition_operator: ch.condition_operator || undefined,
            condition_value: ch.condition_value || undefined
          }))
        ))

        console.log(`[loadChampsForLexique] Mapped ${champsForCode.length} champs:`, champsForCode)

        // Ajouter au cache local sans doublons
        for (const ch of champsForCode) {
          const existingIndex = champs.value.findIndex(c => c.id === ch.id)
          if (existingIndex === -1) {
            champs.value.push(ch)
          } else {
            // Mettre à jour si déjà existant
            champs.value[existingIndex] = ch
          }
        }

        console.log(`[loadChampsForLexique] Total champs in store: ${champs.value.length}`)

        // DÉSACTIVÉ TEMPORAIREMENT - la sauvegarde IndexedDB cause des erreurs
        // offlineService.init().then(() => {
        //   offlineService.saveChamps(JSON.parse(JSON.stringify(champs.value)))
        //     .catch(e => console.warn('Erreur sauvegarde champs offline (non-bloquant):', e))
        // }).catch(() => {})

        return champsForCode
      } else {
        await offlineService.init()
        return await offlineService.getChampsByLexique(lexiqueCode)
      }
    } catch (err) {
      console.error('Erreur chargement champs pour lexique:', err)
      try {
        await offlineService.init()
        return await offlineService.getChampsByLexique(lexiqueCode)
      } catch {
        return []
      }
    }
  }

  // Obtenir les champs pour un code lexique (avec héritage des parents)
  function getChampsByLexique(lexiqueCode: string, projectId?: string): ChampDynamique[] {
    if (!lexiqueCode) return []

    console.log(`[getChampsByLexique] Getting champs for lexique: ${lexiqueCode}, total champs in store: ${champs.value.length}`)
    console.log(`[getChampsByLexique] Champs in store:`, champs.value.map(c => ({ id: c.id, lexique_code: c.lexique_code, nom: c.nom })))

    // Trouver tous les champs pour ce code et ses parents
    const result: ChampDynamique[] = []
    const seenIds = new Set<string>()

    // Fonction récursive pour remonter la hiérarchie
    const collectChamps = (code: string) => {
      const champsForCode = champs.value.filter(c => {
        // Filtrer par code lexique (vérifier les deux propriétés car l'API retourne lexique_id)
        const champCode = c.lexique_code || (c as unknown as { lexique_id?: string }).lexique_id
        if (champCode !== code) return false
        // Filtrer par projet si spécifié (inclure les champs globaux)
        if (projectId && c.project_id && c.project_id !== projectId) return false
        return true
      })

      for (const ch of champsForCode) {
        if (!seenIds.has(ch.id)) {
          seenIds.add(ch.id)
          result.push(ch)
        }
      }

      // Trouver le parent et continuer
      const item = lexique.value.find(l => l.code === code)
      if (item?.parent_code) {
        collectChamps(item.parent_code)
      }
    }

    collectChamps(lexiqueCode)

    console.log(`[getChampsByLexique] Found ${result.length} champs for ${lexiqueCode}:`, result.map(c => c.nom))

    // Trier par ordre
    return result.sort((a, b) => (a.ordre || 0) - (b.ordre || 0))
  }

  // Charger toutes les données de référence
  async function loadReferenceData(): Promise<void> {
    await Promise.all([
      loadLexique(),
      loadProjects(),
      loadChamps()
    ])
  }

  // Créer un point
  async function createPoint(point: Partial<Point>): Promise<Point | null> {
    try {
      if (isOnline.value) {
        const created = await api.createPoint(point)
        points.value.unshift(created)
        totalPoints.value++
        return created
      } else {
        // Sauvegarder localement pour sync ultérieure
        const localId = await offlineService.savePendingPoint({
          ...point,
          sync_status: 'pending'
        } as Point)

        const localPoint: Point = {
          ...point,
          _localId: localId,
          _pendingSync: true,
          sync_status: 'pending'
        } as Point

        points.value.unshift(localPoint)
        await updatePendingCount()
        return localPoint
      }
    } catch (err) {
      error.value = 'Erreur lors de la création du point'
      console.error(err)
      return null
    }
  }

  // Mettre à jour un point
  async function updatePoint(id: string, data: Partial<Point>): Promise<Point | null> {
    try {
      if (isOnline.value) {
        const updated = await api.updatePoint(id, data)
        const index = points.value.findIndex(p => p.id === id || p._localId === id)
        if (index !== -1) {
          points.value[index] = updated
        }
        return updated
      } else {
        // Marquer pour sync
        const localPoint = points.value.find(p => p.id === id || p._localId === id)
        if (localPoint) {
          const updated = { ...localPoint, ...data, _pendingSync: true }
          await offlineService.savePoint(updated)
          const index = points.value.findIndex(p => p.id === id || p._localId === id)
          if (index !== -1) {
            points.value[index] = updated
          }
          await updatePendingCount()
          return updated
        }
        return null
      }
    } catch (err) {
      error.value = 'Erreur lors de la mise à jour'
      console.error(err)
      return null
    }
  }

  // Supprimer un point
  async function deletePoint(id: string): Promise<boolean> {
    try {
      if (isOnline.value) {
        await api.deletePoint(id)
      }
      points.value = points.value.filter(p => p.id !== id && p._localId !== id)
      await offlineService.deletePoint(id)
      totalPoints.value--
      return true
    } catch (err) {
      error.value = 'Erreur lors de la suppression'
      console.error(err)
      return false
    }
  }

  // Obtenir un point par ID
  function getPointById(id: string): Point | undefined {
    return points.value.find(p => p.id === id || p._localId === id)
  }

  // Générer le préfixe pour un nom de géométrie basé sur la catégorie
  // Ex: "Banc bois" → "BanB", "Arbre" → "Arb", "Panneau directionnel" → "PanD"
  function generateCategoryPrefix(categoryLabel: string): string {
    if (!categoryLabel) return 'Elm'

    const words = categoryLabel.trim().split(/\s+/)

    if (words.length === 1) {
      // Catégorie simple: 3 premières lettres avec première majuscule
      const word = words[0]
      return word.charAt(0).toUpperCase() + word.slice(1, 3).toLowerCase()
    } else {
      // Catégorie composée: 3 lettres du premier mot + 1ère lettre du deuxième
      const firstWord = words[0]
      const secondWord = words[1]
      const prefix = firstWord.charAt(0).toUpperCase() + firstWord.slice(1, 3).toLowerCase()
      const suffix = secondWord.charAt(0).toUpperCase()
      return prefix + suffix
    }
  }

  // Générer le prochain nom pour une géométrie basé sur la catégorie
  // Ex: "BanB 01", "BanB 02", "Arb 01", etc.
  // Réutilise les numéros libres (si BanB 01 est supprimé, le prochain sera BanB 01)
  function getNextGeometryName(categoryLabel: string, lexiqueCode: string): string {
    const prefix = generateCategoryPrefix(categoryLabel)

    // Trouver tous les points existants avec le même code lexique
    const existingOfCategory = points.value.filter(p => p.lexique_code === lexiqueCode)

    // Collecter les numéros utilisés
    const usedNumbers = new Set<number>()
    const regex = new RegExp(`^${prefix}\\s+(\\d+)$`, 'i')

    for (const point of existingOfCategory) {
      if (point.name) {
        const match = point.name.match(regex)
        if (match) {
          usedNumbers.add(parseInt(match[1], 10))
        }
      }
    }

    // Trouver le premier numéro libre (réutilisation)
    let nextNumber = 1
    while (usedNumbers.has(nextNumber)) {
      nextNumber++
    }

    // Formater avec zéro si < 10
    const formattedNumber = nextNumber.toString().padStart(2, '0')
    return `${prefix} ${formattedNumber}`
  }

  // Obtenir le label du lexique
  function getLexiqueLabel(code: string): string {
    const item = lexique.value.find(l => l.code === code)
    return item?.label || code
  }

  // Obtenir le chemin complet du lexique
  function getLexiquePath(code: string): string {
    const item = lexique.value.find(l => l.code === code)
    return item?.full_path || item?.label || code
  }

  // Sélectionner un projet
  function selectProject(projectId: string | null): void {
    selectedProjectId.value = projectId
  }

  // Uploader les photos d'un point
  async function uploadPhotosForPoint(
    pointId: string,
    photos: Array<{ localBlob: Blob; gps_lat?: number; gps_lng?: number; gps_accuracy?: number }>
  ): Promise<number> {
    let uploaded = 0
    for (const photo of photos) {
      if (!photo.localBlob) continue
      try {
        await api.uploadPhoto(pointId, photo.localBlob, {
          gps_lat: photo.gps_lat,
          gps_lng: photo.gps_lng,
          gps_accuracy: photo.gps_accuracy
        })
        uploaded++
      } catch (err) {
        console.error(`Erreur upload photo pour point ${pointId}:`, err)
        // Sauvegarder en pending pour sync ultérieure
        try {
          await offlineService.init()
          await offlineService.savePendingPhoto({
            pointId,
            blob: photo.localBlob,
            gps_lat: photo.gps_lat,
            gps_lng: photo.gps_lng,
            gps_accuracy: photo.gps_accuracy
          })
        } catch (e) {
          console.error('Erreur sauvegarde photo offline:', e)
        }
      }
    }
    return uploaded
  }

  // Réinitialiser
  function reset(): void {
    points.value = []
    currentPage.value = 1
    totalPages.value = 1
    totalPoints.value = 0
    error.value = null
  }

  return {
    // État
    points,
    lexique,
    projects,
    champs,
    isLoading,
    error,
    currentPage,
    totalPages,
    totalPoints,
    selectedProjectId,
    isOnline,
    pendingCount,

    // Computed
    lexiqueTree,

    // Actions
    initOffline,
    updatePendingCount,
    loadPoints,
    loadLexique,
    loadProjects,
    loadChamps,
    loadChampsForLexique,
    loadReferenceData,
    createPoint,
    updatePoint,
    deletePoint,
    getPointById,
    getLexiqueLabel,
    getLexiquePath,
    getChampsByLexique,
    getNextGeometryName,
    generateCategoryPrefix,
    uploadPhotosForPoint,
    selectProject,
    reset
  }
})

import { openDB, DBSchema, IDBPDatabase } from 'idb'
import type { Point, LexiqueItem, Project, ChampDynamique } from './api'

// Schéma de la base IndexedDB
interface GeoclicDB extends DBSchema {
  points: {
    key: string
    value: Point & {
      _localId: string
      _pendingSync: boolean
      _lastModified: number
    }
    indexes: {
      'by-sync-status': string
      'by-pending': number
      'by-project': string
    }
  }
  pendingPoints: {
    key: string
    value: Point & {
      _localId: string
      _createdAt: number
      _attempts: number
    }
  }
  pendingPhotos: {
    key: string
    value: {
      id: string
      pointId: string
      localPath: string
      blob: Blob
      gps_lat?: number
      gps_lng?: number
      gps_accuracy?: number
      createdAt: number
      attempts: number
    }
  }
  lexique: {
    key: string
    value: LexiqueItem
    indexes: {
      'by-parent': string
      'by-level': number
    }
  }
  projects: {
    key: string
    value: Project
  }
  champs: {
    key: string
    value: ChampDynamique
    indexes: {
      'by-lexique': string
    }
  }
  metadata: {
    key: string
    value: {
      key: string
      value: unknown
      updatedAt: number
    }
  }
}

const DB_NAME = 'geoclic-mobile'
const DB_VERSION = 2

class OfflineService {
  private db: IDBPDatabase<GeoclicDB> | null = null
  private initPromise: Promise<void> | null = null

  // Initialiser la base de données
  async init(): Promise<void> {
    if (this.db) return
    if (this.initPromise) return this.initPromise

    this.initPromise = this.openDatabase()
    await this.initPromise
  }

  private async openDatabase(): Promise<void> {
    this.db = await openDB<GeoclicDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        // Store des points synchronisés
        if (!db.objectStoreNames.contains('points')) {
          const pointsStore = db.createObjectStore('points', { keyPath: '_localId' })
          pointsStore.createIndex('by-sync-status', 'sync_status')
          pointsStore.createIndex('by-pending', '_pendingSync')
          pointsStore.createIndex('by-project', 'project_id')
        }

        // Store des points en attente de création
        if (!db.objectStoreNames.contains('pendingPoints')) {
          db.createObjectStore('pendingPoints', { keyPath: '_localId' })
        }

        // Store des photos en attente d'upload
        if (!db.objectStoreNames.contains('pendingPhotos')) {
          db.createObjectStore('pendingPhotos', { keyPath: 'id' })
        }

        // Store du lexique
        if (!db.objectStoreNames.contains('lexique')) {
          const lexiqueStore = db.createObjectStore('lexique', { keyPath: 'code' })
          lexiqueStore.createIndex('by-parent', 'parent_code')
          lexiqueStore.createIndex('by-level', 'level')
        }

        // Store des projets
        if (!db.objectStoreNames.contains('projects')) {
          db.createObjectStore('projects', { keyPath: 'id' })
        }

        // Store des champs dynamiques
        if (!db.objectStoreNames.contains('champs')) {
          const champsStore = db.createObjectStore('champs', { keyPath: 'id' })
          champsStore.createIndex('by-lexique', 'lexique_code')
        }

        // Store des métadonnées
        if (!db.objectStoreNames.contains('metadata')) {
          db.createObjectStore('metadata', { keyPath: 'key' })
        }
      }
    })
  }

  // Vérifier si initialisé
  private ensureInit(): void {
    if (!this.db) {
      throw new Error('OfflineService non initialisé. Appelez init() d\'abord.')
    }
  }

  // ========== POINTS ==========

  async savePoint(point: Point): Promise<string> {
    this.ensureInit()
    const localId = point._localId || point.id || crypto.randomUUID()

    await this.db!.put('points', {
      ...point,
      _localId: localId,
      _pendingSync: point._pendingSync ?? false,
      _lastModified: Date.now()
    })

    return localId
  }

  async getPoint(localId: string): Promise<Point | undefined> {
    this.ensureInit()
    return this.db!.get('points', localId)
  }

  async getAllPoints(): Promise<Point[]> {
    this.ensureInit()
    return this.db!.getAll('points')
  }

  async getPointsByProject(projectId: string): Promise<Point[]> {
    this.ensureInit()
    return this.db!.getAllFromIndex('points', 'by-project', projectId)
  }

  async deletePoint(localId: string): Promise<void> {
    this.ensureInit()
    await this.db!.delete('points', localId)
  }

  async clearPoints(): Promise<void> {
    this.ensureInit()
    await this.db!.clear('points')
  }

  // ========== POINTS EN ATTENTE ==========

  async savePendingPoint(point: Point): Promise<string> {
    this.ensureInit()
    const localId = point._localId || crypto.randomUUID()

    await this.db!.put('pendingPoints', {
      ...point,
      _localId: localId,
      _createdAt: Date.now(),
      _attempts: 0
    })

    return localId
  }

  async getPendingPoints(): Promise<Point[]> {
    this.ensureInit()
    return this.db!.getAll('pendingPoints')
  }

  async getPendingPointsCount(): Promise<number> {
    this.ensureInit()
    return this.db!.count('pendingPoints')
  }

  async deletePendingPoint(localId: string): Promise<void> {
    this.ensureInit()
    await this.db!.delete('pendingPoints', localId)
  }

  async incrementPendingPointAttempts(localId: string): Promise<void> {
    this.ensureInit()
    const point = await this.db!.get('pendingPoints', localId)
    if (point) {
      point._attempts = (point._attempts || 0) + 1
      await this.db!.put('pendingPoints', point)
    }
  }

  // ========== PHOTOS EN ATTENTE ==========

  async savePendingPhoto(photo: {
    pointId: string
    blob: Blob
    gps_lat?: number
    gps_lng?: number
    gps_accuracy?: number
  }): Promise<string> {
    this.ensureInit()
    const id = crypto.randomUUID()

    await this.db!.put('pendingPhotos', {
      id,
      pointId: photo.pointId,
      localPath: URL.createObjectURL(photo.blob),
      blob: photo.blob,
      gps_lat: photo.gps_lat,
      gps_lng: photo.gps_lng,
      gps_accuracy: photo.gps_accuracy,
      createdAt: Date.now(),
      attempts: 0
    })

    return id
  }

  async getPendingPhotos(): Promise<Array<{
    id: string
    pointId: string
    blob: Blob
    gps_lat?: number
    gps_lng?: number
    gps_accuracy?: number
  }>> {
    this.ensureInit()
    return this.db!.getAll('pendingPhotos')
  }

  async getPendingPhotosCount(): Promise<number> {
    this.ensureInit()
    return this.db!.count('pendingPhotos')
  }

  async getPendingPhotosByPoint(pointId: string): Promise<Array<{
    id: string
    blob: Blob
    localPath: string
  }>> {
    this.ensureInit()
    const all = await this.db!.getAll('pendingPhotos')
    return all.filter(p => p.pointId === pointId)
  }

  async deletePendingPhoto(id: string): Promise<void> {
    this.ensureInit()
    await this.db!.delete('pendingPhotos', id)
  }

  // ========== LEXIQUE ==========

  async saveLexique(items: LexiqueItem[]): Promise<void> {
    this.ensureInit()
    if (!Array.isArray(items) || items.length === 0) return
    const tx = this.db!.transaction('lexique', 'readwrite')
    await Promise.all([
      ...items.map(item => tx.store.put(item)),
      tx.done
    ])
  }

  async getLexique(): Promise<LexiqueItem[]> {
    this.ensureInit()
    return this.db!.getAll('lexique')
  }

  async getLexiqueByLevel(level: number): Promise<LexiqueItem[]> {
    this.ensureInit()
    return this.db!.getAllFromIndex('lexique', 'by-level', level)
  }

  async getLexiqueByParent(parentCode: string): Promise<LexiqueItem[]> {
    this.ensureInit()
    return this.db!.getAllFromIndex('lexique', 'by-parent', parentCode)
  }

  // ========== PROJETS ==========

  async saveProjects(projects: Project[]): Promise<void> {
    this.ensureInit()
    if (!Array.isArray(projects) || projects.length === 0) return
    const tx = this.db!.transaction('projects', 'readwrite')
    await Promise.all([
      ...projects.map(p => tx.store.put(p)),
      tx.done
    ])
  }

  async getProjects(): Promise<Project[]> {
    this.ensureInit()
    return this.db!.getAll('projects')
  }

  // ========== CHAMPS DYNAMIQUES ==========

  async saveChamps(champs: ChampDynamique[]): Promise<void> {
    this.ensureInit()
    if (!Array.isArray(champs) || champs.length === 0) return

    // Créer des copies complètement détachées de Vue pour éviter DataCloneError
    const tx = this.db!.transaction('champs', 'readwrite')

    for (let i = 0; i < champs.length; i++) {
      // Copie profonde de chaque objet individuellement
      const champ = champs[i]
      const plainChamp: ChampDynamique = {
        id: String(champ.id || ''),
        lexique_code: String(champ.lexique_code || ''),
        nom: String(champ.nom || ''),
        type: champ.type,
        obligatoire: Boolean(champ.obligatoire),
        ordre: Number(champ.ordre) || 0,
        options: champ.options ? Array.from(champ.options) : undefined,
        min: champ.min != null ? Number(champ.min) : undefined,
        max: champ.max != null ? Number(champ.max) : undefined,
        default_value: champ.default_value ? String(champ.default_value) : undefined,
        project_id: champ.project_id ? String(champ.project_id) : undefined,
        condition_field: champ.condition_field ? String(champ.condition_field) : undefined,
        condition_operator: champ.condition_operator ? String(champ.condition_operator) : undefined,
        condition_value: champ.condition_value ? String(champ.condition_value) : undefined
      }
      tx.store.put(plainChamp)
    }

    await tx.done
  }

  async getChamps(): Promise<ChampDynamique[]> {
    this.ensureInit()
    return this.db!.getAll('champs')
  }

  async getChampsByLexique(lexiqueCode: string): Promise<ChampDynamique[]> {
    this.ensureInit()
    return this.db!.getAllFromIndex('champs', 'by-lexique', lexiqueCode)
  }

  // ========== MÉTADONNÉES ==========

  async setMetadata(key: string, value: unknown): Promise<void> {
    this.ensureInit()
    await this.db!.put('metadata', {
      key,
      value,
      updatedAt: Date.now()
    })
  }

  async getMetadata<T>(key: string): Promise<T | undefined> {
    this.ensureInit()
    const entry = await this.db!.get('metadata', key)
    return entry?.value as T | undefined
  }

  async getLastSyncTimestamp(): Promise<string | undefined> {
    return this.getMetadata<string>('lastSyncAt')
  }

  async setLastSyncTimestamp(timestamp: string): Promise<void> {
    await this.setMetadata('lastSyncAt', timestamp)
  }

  // ========== STATISTIQUES ==========

  async getStats(): Promise<{
    totalPoints: number
    pendingPoints: number
    pendingPhotos: number
    lexiqueItems: number
    projects: number
    lastSync: string | undefined
  }> {
    this.ensureInit()

    const [totalPoints, pendingPoints, pendingPhotos, lexiqueItems, projects, lastSync] = await Promise.all([
      this.db!.count('points'),
      this.db!.count('pendingPoints'),
      this.db!.count('pendingPhotos'),
      this.db!.count('lexique'),
      this.db!.count('projects'),
      this.getLastSyncTimestamp()
    ])

    return {
      totalPoints,
      pendingPoints,
      pendingPhotos,
      lexiqueItems,
      projects,
      lastSync
    }
  }

  // ========== NETTOYAGE ==========

  async clearAll(): Promise<void> {
    this.ensureInit()
    await Promise.all([
      this.db!.clear('points'),
      this.db!.clear('pendingPoints'),
      this.db!.clear('pendingPhotos'),
      this.db!.clear('lexique'),
      this.db!.clear('projects'),
      this.db!.clear('champs'),
      this.db!.clear('metadata')
    ])
  }
}

// Export singleton
export const offlineService = new OfflineService()
export default offlineService

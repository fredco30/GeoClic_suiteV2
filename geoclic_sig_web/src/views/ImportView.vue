<template>
  <div class="import-view">
    <div class="import-header">
      <h2>Import de données</h2>
      <p>Importez des fichiers GeoJSON, GeoPackage ou Shapefile</p>
    </div>

    <div
      class="drop-zone"
      :class="{ dragover: isDragOver }"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
      @drop.prevent="handleDrop"
    >
      <div class="drop-content">
        <span class="drop-icon">📥</span>
        <h3>Glissez-déposez vos fichiers ici</h3>
        <p>ou</p>
        <label class="file-input-label">
          <input
            type="file"
            accept=".geojson,.json,.gpkg,.zip"
            @change="handleFileSelect"
            multiple
          >
          Parcourir les fichiers
        </label>
        <p class="supported-formats">
          Formats supportés : GeoJSON (.geojson), GeoPackage (.gpkg), Shapefile (.zip)
        </p>
        <p class="format-note">
          Pour les Shapefiles : uploadez un fichier .zip contenant .shp, .shx, .dbf et .prj
        </p>
      </div>
    </div>

    <!-- Import Queue -->
    <div v-if="importQueue.length > 0" class="import-queue">
      <h3>Fichiers en attente</h3>
      <div
        v-for="(item, index) in importQueue"
        :key="index"
        class="queue-item"
        :class="item.status"
      >
        <div class="queue-item-info">
          <span class="file-icon">{{ getFileIcon(item.file.name) }}</span>
          <span class="file-name">{{ item.file.name }}</span>
          <span class="file-size">{{ formatSize(item.file.size) }}</span>
        </div>
        <div class="queue-item-status">
          <span v-if="item.status === 'pending'">En attente</span>
          <span v-else-if="item.status === 'processing'">
            <span class="spinner"></span> Traitement...
          </span>
          <span v-else-if="item.status === 'success'" class="success">✓ Importé</span>
          <span v-else-if="item.status === 'error'" class="error">✗ {{ item.error }}</span>
        </div>
      </div>

      <button
        v-if="hasReadyFiles"
        @click="processImports"
        class="import-btn"
        :disabled="isProcessing"
      >
        Importer les fichiers
      </button>
    </div>

    <!-- Recent Imports -->
    <div v-if="recentImports.length > 0" class="recent-imports">
      <h3>Imports récents</h3>
      <div
        v-for="imp in recentImports"
        :key="imp.id"
        class="recent-item"
      >
        <span class="recent-name">{{ imp.name }}</span>
        <span class="recent-count">{{ imp.featureCount }} éléments</span>
        <button @click="addToMap(imp)" class="add-btn">
          Ajouter à la carte
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMapStore } from '../stores/map'
import axios from 'axios'

interface QueueItem {
  file: File
  status: 'pending' | 'processing' | 'success' | 'error'
  error?: string
  result?: any
}

interface RecentImport {
  id: string
  name: string
  featureCount: number
  data: GeoJSON.FeatureCollection
  type: 'points' | 'lines' | 'polygons'
}

const router = useRouter()
const mapStore = useMapStore()

const isDragOver = ref(false)
const importQueue = ref<QueueItem[]>([])
const recentImports = ref<RecentImport[]>([])
const isProcessing = ref(false)

const hasReadyFiles = computed(() =>
  importQueue.value.some(item => item.status === 'pending')
)

function handleDrop(e: DragEvent) {
  isDragOver.value = false
  const files = e.dataTransfer?.files
  if (files) {
    addFilesToQueue(Array.from(files))
  }
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    addFilesToQueue(Array.from(input.files))
  }
}

function addFilesToQueue(files: File[]) {
  files.forEach(file => {
    const ext = file.name.toLowerCase().split('.').pop()
    // .zip pour Shapefile (doit contenir .shp, .shx, .dbf, .prj)
    // .gpkg pour GeoPackage
    // .geojson/.json pour GeoJSON
    if (['geojson', 'json', 'gpkg', 'zip'].includes(ext || '')) {
      importQueue.value.push({
        file,
        status: 'pending'
      })
    }
  })
}

async function processImports() {
  isProcessing.value = true

  for (const item of importQueue.value) {
    if (item.status !== 'pending') continue

    item.status = 'processing'

    try {
      const result = await importFile(item.file)
      item.status = 'success'
      item.result = result

      // Add to recent imports
      recentImports.value.unshift({
        id: `import_${Date.now()}`,
        name: item.file.name.replace(/\.[^.]+$/, ''),
        featureCount: result.features.length,
        data: result,
        type: detectGeometryType(result)
      })
    } catch (error: any) {
      item.status = 'error'
      item.error = error.message || 'Erreur import'
    }
  }

  isProcessing.value = false
}

async function importFile(file: File): Promise<GeoJSON.FeatureCollection> {
  const ext = file.name.toLowerCase().split('.').pop()

  if (ext === 'geojson' || ext === 'json') {
    // Parse GeoJSON locally
    const text = await file.text()
    const data = JSON.parse(text)

    if (data.type === 'FeatureCollection') {
      return data
    } else if (data.type === 'Feature') {
      return { type: 'FeatureCollection', features: [data] }
    }
    throw new Error('Format GeoJSON invalide')
  }

  // For GeoPackage and Shapefile, send to server
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post('/api/sig/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

  return response.data
}

function detectGeometryType(geojson: GeoJSON.FeatureCollection): 'points' | 'lines' | 'polygons' {
  const firstFeature = geojson.features[0]
  if (!firstFeature) return 'points'

  const type = firstFeature.geometry?.type
  if (type === 'Point' || type === 'MultiPoint') return 'points'
  if (type === 'LineString' || type === 'MultiLineString') return 'lines'
  return 'polygons'
}

function addToMap(imp: RecentImport) {
  mapStore.addImportedLayer(imp.name, imp.data, imp.type)
  router.push('/')
}

function getFileIcon(filename: string): string {
  const ext = filename.toLowerCase().split('.').pop()
  switch (ext) {
    case 'geojson':
    case 'json':
      return '📄'
    case 'gpkg':
      return '📦'
    case 'zip':
      return '🗂️' // Shapefile (archive)
    default:
      return '📁'
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.import-view {
  padding: 30px;
  max-width: 800px;
  margin: 0 auto;
}

.import-header {
  margin-bottom: 30px;
}

.import-header h2 {
  margin: 0 0 5px 0;
  color: #1a1a2e;
}

.import-header p {
  margin: 0;
  color: #666;
}

.drop-zone {
  border: 3px dashed #ddd;
  border-radius: 12px;
  padding: 60px 30px;
  text-align: center;
  transition: all 0.2s;
  background: #fafafa;
}

.drop-zone.dragover {
  border-color: #3498db;
  background: #f0f8ff;
}

.drop-content {
  pointer-events: none;
}

.drop-zone.dragover .drop-content {
  pointer-events: auto;
}

.drop-icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 15px;
}

.drop-content h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.drop-content p {
  color: #666;
  margin: 10px 0;
}

.file-input-label {
  display: inline-block;
  padding: 12px 24px;
  background: #3498db;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  pointer-events: auto;
}

.file-input-label:hover {
  background: #2980b9;
}

.file-input-label input {
  display: none;
}

.supported-formats {
  font-size: 0.85rem;
  color: #999;
  margin-top: 20px !important;
}

.format-note {
  font-size: 0.8rem;
  color: #3498db;
  margin-top: 5px !important;
  font-style: italic;
}

.import-queue {
  margin-top: 30px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.import-queue h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: #333;
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #f8f9fa;
}

.queue-item.success {
  background: #d4edda;
}

.queue-item.error {
  background: #f8d7da;
}

.queue-item-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  font-size: 1.3rem;
}

.file-name {
  font-weight: 500;
}

.file-size {
  color: #666;
  font-size: 0.85rem;
}

.queue-item-status .success {
  color: #28a745;
}

.queue-item-status .error {
  color: #dc3545;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #ddd;
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  vertical-align: middle;
  margin-right: 5px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.import-btn {
  margin-top: 15px;
  width: 100%;
  padding: 14px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.import-btn:hover:not(:disabled) {
  background: #2980b9;
}

.import-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.recent-imports {
  margin-top: 30px;
}

.recent-imports h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: #333;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 15px;
  background: white;
  border-radius: 8px;
  margin-bottom: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.recent-name {
  flex: 1;
  font-weight: 500;
}

.recent-count {
  color: #666;
  font-size: 0.9rem;
}

.add-btn {
  padding: 8px 16px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.add-btn:hover {
  background: #219a52;
}
</style>

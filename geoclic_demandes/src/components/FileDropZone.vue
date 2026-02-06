<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import axios from 'axios'

export interface UploadedFile {
  url: string
  type: 'image' | 'document'
  originalName: string
  sizeBytes: number
}

interface Props {
  maxFiles?: number
  accept?: string
  label?: string
  initialFiles?: UploadedFile[]
}

interface Emits {
  (e: 'update', files: UploadedFile[]): void
}

const props = withDefaults(defineProps<Props>(), {
  maxFiles: 20,
  accept: '.jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.odt,.xls,.xlsx,.txt,.csv',
  label: 'Photos et documents',
  initialFiles: () => [],
})

const emit = defineEmits<Emits>()

const files = ref<UploadedFile[]>([...props.initialFiles])

// Synchroniser quand initialFiles change (ex: chargement async en mode édition)
watch(() => props.initialFiles, (newFiles) => {
  if (newFiles && newFiles.length > 0 && files.value.length === 0) {
    files.value = [...newFiles]
  }
}, { deep: true })
const uploading = ref(false)
const uploadProgress = ref(0)
const dragOver = ref(false)
const error = ref('')

const fileInput = ref<HTMLInputElement | null>(null)

const canAddMore = computed(() => files.value.length < props.maxFiles)

const photos = computed(() => files.value.filter(f => f.type === 'image'))
const documents = computed(() => files.value.filter(f => f.type === 'document'))

function triggerFileInput() {
  fileInput.value?.click()
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
  dragOver.value = true
}

function onDragLeave() {
  dragOver.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false
  const droppedFiles = e.dataTransfer?.files
  if (droppedFiles) {
    handleFiles(Array.from(droppedFiles))
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    handleFiles(Array.from(input.files))
    input.value = '' // Reset pour pouvoir re-sélectionner le même fichier
  }
}

async function handleFiles(newFiles: File[]) {
  error.value = ''
  const remaining = props.maxFiles - files.value.length
  if (remaining <= 0) {
    error.value = `Maximum ${props.maxFiles} fichiers atteint`
    return
  }

  const filesToUpload = newFiles.slice(0, remaining)
  uploading.value = true
  uploadProgress.value = 0

  let uploaded = 0
  for (const file of filesToUpload) {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post('/api/demandes/upload/fichier', formData, {
        headers: { 'Content-Type': undefined },
      })

      files.value.push({
        url: response.data.url,
        type: response.data.type,
        originalName: response.data.original_name,
        sizeBytes: response.data.size_bytes,
      })

      uploaded++
      uploadProgress.value = Math.round((uploaded / filesToUpload.length) * 100)
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Erreur upload'
      error.value = `${file.name}: ${detail}`
    }
  }

  uploading.value = false
  emit('update', files.value)
}

function removeFile(index: number) {
  files.value.splice(index, 1)
  emit('update', files.value)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`
}

function getFileIcon(file: UploadedFile): string {
  if (file.type === 'image') return '&#128247;'
  const ext = file.originalName.split('.').pop()?.toLowerCase()
  if (ext === 'pdf') return '&#128196;'
  if (['doc', 'docx', 'odt'].includes(ext || '')) return '&#128196;'
  if (['xls', 'xlsx'].includes(ext || '')) return '&#128200;'
  return '&#128206;'
}
</script>

<template>
  <div class="file-drop-zone">
    <label class="field-label">{{ label }}</label>

    <!-- Zone de drop -->
    <div
      class="drop-area"
      :class="{ 'drag-over': dragOver, 'has-files': files.length > 0 }"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="accept"
        multiple
        class="file-input-hidden"
        @change="onFileChange"
      />

      <div v-if="uploading" class="upload-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <span class="progress-text">Upload en cours... {{ uploadProgress }}%</span>
      </div>

      <div v-else class="drop-content">
        <span class="drop-icon">&#128206;</span>
        <p class="drop-text">
          <strong>Glisser-déposer</strong> vos fichiers ici<br />
          ou <span class="drop-link">parcourir</span>
        </p>
        <p class="drop-hint">
          Images (JPG, PNG, GIF) et documents (PDF, DOC, XLS, etc.) - Max {{ maxFiles }} fichiers, 20 Mo chacun
        </p>
      </div>
    </div>

    <!-- Erreur -->
    <div v-if="error" class="upload-error">{{ error }}</div>

    <!-- Fichiers uploadés -->
    <div v-if="files.length > 0" class="files-list">
      <!-- Photos -->
      <div v-if="photos.length > 0" class="files-section">
        <h4 class="files-section-title">Photos ({{ photos.length }})</h4>
        <div class="photos-grid">
          <div v-for="(file, i) in files" :key="file.url" class="photo-item" v-show="file.type === 'image'">
            <img :src="file.url" :alt="file.originalName" class="photo-thumb" />
            <button @click.stop="removeFile(i)" class="remove-btn" title="Supprimer">&#10005;</button>
          </div>
        </div>
      </div>

      <!-- Documents -->
      <div v-if="documents.length > 0" class="files-section">
        <h4 class="files-section-title">Documents ({{ documents.length }})</h4>
        <div class="documents-list">
          <div v-for="(file, i) in files" :key="file.url" class="document-item" v-show="file.type === 'document'">
            <span class="doc-icon" v-html="getFileIcon(file)"></span>
            <div class="doc-info">
              <span class="doc-name">{{ file.originalName }}</span>
              <span class="doc-size">{{ formatSize(file.sizeBytes) }}</span>
            </div>
            <button @click.stop="removeFile(i)" class="remove-btn-small" title="Supprimer">&#10005;</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!canAddMore" class="files-limit">
      Limite de {{ maxFiles }} fichiers atteinte
    </div>
  </div>
</template>

<style scoped>
.file-drop-zone {
  margin-bottom: 1rem;
}

.field-label {
  display: block;
  font-weight: 600;
  font-size: 0.9rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.drop-area {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}

.drop-area:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.drop-area.drag-over {
  border-color: #3b82f6;
  background: #dbeafe;
  transform: scale(1.01);
}

.file-input-hidden {
  display: none;
}

.drop-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.5rem;
}

.drop-text {
  color: #4b5563;
  margin: 0.5rem 0;
  font-size: 0.95rem;
}

.drop-link {
  color: #3b82f6;
  text-decoration: underline;
  font-weight: 500;
}

.drop-hint {
  color: #9ca3af;
  font-size: 0.8rem;
  margin: 0;
}

.upload-progress {
  padding: 1rem 0;
}

.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 4px;
  transition: width 0.3s;
}

.progress-text {
  color: #6b7280;
  font-size: 0.85rem;
}

.upload-error {
  color: #dc2626;
  font-size: 0.85rem;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #fef2f2;
  border-radius: 6px;
}

.files-list {
  margin-top: 1rem;
}

.files-section {
  margin-bottom: 1rem;
}

.files-section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 0.5rem;
}

.photo-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
}

.photo-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  font-size: 0.7rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.photo-item:hover .remove-btn {
  opacity: 1;
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.doc-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  display: block;
  font-size: 0.9rem;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-size {
  font-size: 0.75rem;
  color: #9ca3af;
}

.remove-btn-small {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: none;
  border: 1px solid #e5e7eb;
  color: #9ca3af;
  font-size: 0.7rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.remove-btn-small:hover {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #dc2626;
}

.files-limit {
  color: #f59e0b;
  font-size: 0.85rem;
  margin-top: 0.5rem;
  text-align: center;
}
</style>

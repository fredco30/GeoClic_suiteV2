<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/services/api'

interface Props {
  max?: number
}

interface Emits {
  (e: 'change', urls: string[]): void
}

const props = withDefaults(defineProps<Props>(), {
  max: 3,
})

const emit = defineEmits<Emits>()

interface PhotoItem {
  id: string
  file?: File
  url: string
  uploading: boolean
  error?: string
}

const photos = ref<PhotoItem[]>([])

// Compression image max 720x576
const MAX_WIDTH = 720
const MAX_HEIGHT = 576
const JPEG_QUALITY = 0.85

async function compressImage(file: File): Promise<File> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      let { width, height } = img

      // Calculer les nouvelles dimensions en conservant le ratio
      if (width > MAX_WIDTH || height > MAX_HEIGHT) {
        const ratio = Math.min(MAX_WIDTH / width, MAX_HEIGHT / height)
        width = Math.round(width * ratio)
        height = Math.round(height * ratio)
      }

      // Créer un canvas pour redimensionner
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height

      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('Canvas context not available'))
        return
      }

      ctx.drawImage(img, 0, 0, width, height)

      // Convertir en blob JPEG
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Compression failed'))
            return
          }

          // Créer un nouveau File avec le blob compressé
          const compressedFile = new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), {
            type: 'image/jpeg',
            lastModified: Date.now(),
          })

          resolve(compressedFile)
        },
        'image/jpeg',
        JPEG_QUALITY
      )
    }

    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = URL.createObjectURL(file)
  })
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

async function onFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files

  if (!files) return

  for (const file of Array.from(files)) {
    if (photos.value.length >= props.max) break

    if (!file.type.startsWith('image/')) {
      alert('Seules les images sont acceptées')
      continue
    }

    if (file.size > 10 * 1024 * 1024) {
      alert('La taille maximum est de 10 Mo')
      continue
    }

    const photo: PhotoItem = {
      id: generateId(),
      file,
      url: URL.createObjectURL(file),
      uploading: true,
    }

    photos.value.push(photo)

    // Timeout de sécurité pour éviter le chargement infini
    const photoId = photo.id
    const timeout = setTimeout(() => {
      const p = photos.value.find(x => x.id === photoId)
      if (p && p.uploading) {
        p.uploading = false
        emitChange()
      }
    }, 10000)

    try {
      // Compresser l'image à 720p max avant upload
      const compressedFile = await compressImage(file)
      const uploadedUrl = await api.uploadPhoto(compressedFile)
      clearTimeout(timeout)
      // Trouver la photo dans le tableau pour assurer la réactivité
      const p = photos.value.find(x => x.id === photoId)
      if (p) {
        p.url = uploadedUrl
        p.uploading = false
      }
      emitChange()
    } catch (error) {
      clearTimeout(timeout)
      const p = photos.value.find(x => x.id === photoId)
      if (p) {
        p.error = 'Erreur upload'
        p.uploading = false
      }
    }
  }

  // Reset input
  input.value = ''
}

function removePhoto(id: string) {
  const index = photos.value.findIndex((p) => p.id === id)
  if (index !== -1) {
    const photo = photos.value[index]
    if (photo.file) {
      URL.revokeObjectURL(photo.url)
    }
    photos.value.splice(index, 1)
    emitChange()
  }
}

function emitChange() {
  const urls = photos.value
    .filter((p) => !p.uploading && !p.error)
    .map((p) => p.url)
  emit('change', urls)
}
</script>

<template>
  <div class="photo-uploader">
    <div class="photos-grid">
      <!-- Existing photos -->
      <div v-for="photo in photos" :key="photo.id" class="photo-item">
        <img :src="photo.url" alt="Photo" />
        <div v-if="photo.uploading" class="photo-overlay">
          <div class="progress-bar">
            <div class="progress-fill"></div>
          </div>
        </div>
        <div v-else-if="photo.error" class="photo-overlay error">
          <span>{{ photo.error }}</span>
        </div>
        <button @click="removePhoto(photo.id)" class="remove-btn" title="Supprimer">
          &times;
        </button>
      </div>

      <!-- Camera button (mobile) -->
      <label v-if="photos.length < max" class="add-photo camera">
        <input
          type="file"
          accept="image/*"
          capture="environment"
          @change="onFileSelect"
          class="hidden"
        />
        <span class="add-icon">📷</span>
        <span class="add-text">Photo</span>
      </label>

      <!-- Gallery button -->
      <label v-if="photos.length < max" class="add-photo gallery">
        <input
          type="file"
          accept="image/*"
          multiple
          @change="onFileSelect"
          class="hidden"
        />
        <span class="add-icon">🖼️</span>
        <span class="add-text">Galerie</span>
      </label>
    </div>

    <p class="photo-hint">
      {{ photos.length }}/{{ max }} photo(s) - Max 10 Mo par photo
    </p>
  </div>
</template>

<style scoped>
.photo-uploader {
  margin-top: 0.5rem;
}

.photos-grid {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.photo-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
}

.photo-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.photo-overlay.error {
  background: rgba(220, 38, 38, 0.8);
  font-size: 0.75rem;
  text-align: center;
  padding: 0.5rem;
}

.progress-bar {
  width: 60px;
  height: 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: white;
  border-radius: 3px;
  animation: progress 2s ease-in-out infinite;
}

@keyframes progress {
  0% { width: 0%; margin-left: 0%; }
  50% { width: 60%; margin-left: 20%; }
  100% { width: 0%; margin-left: 100%; }
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
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  background: #dc2626;
}

.add-photo {
  width: 100px;
  height: 100px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.add-photo:hover {
  border-color: var(--primary-color, #2563eb);
  background: #f8fafc;
}

.add-photo.camera {
  border-color: #10b981;
  background: #ecfdf5;
}

.add-photo.camera:hover {
  border-color: #059669;
  background: #d1fae5;
}

.add-photo.gallery {
  border-color: #6366f1;
  background: #eef2ff;
}

.add-photo.gallery:hover {
  border-color: #4f46e5;
  background: #e0e7ff;
}

.add-icon {
  font-size: 1.5rem;
}

.add-text {
  font-size: 0.75rem;
  color: #6b7280;
}

.add-photo.camera .add-text {
  color: #059669;
}

.add-photo.gallery .add-text {
  color: #4f46e5;
}

.hidden {
  display: none;
}

.photo-hint {
  font-size: 0.8rem;
  color: #6b7280;
  margin-top: 0.5rem;
}
</style>

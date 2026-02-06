<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { usePointsStore } from '@/stores/points'
import { normalizeColor } from '@/services/api'
import type { LexiqueItem } from '@/services/api'

const props = defineProps<{
  modelValue?: string
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const pointsStore = usePointsStore()
const isOpen = ref(false)
const selectedPath = ref<LexiqueItem[]>([])
const currentLevel = ref(0)

// Obtenir les éléments du niveau actuel
const currentItems = computed(() => {
  if (currentLevel.value === 0) {
    // Niveau racine
    return pointsStore.lexique.filter(item => !item.parent_code || item.level === 1)
  } else {
    // Sous-niveau
    const parentCode = selectedPath.value[currentLevel.value - 1]?.code
    if (parentCode) {
      return pointsStore.lexique.filter(item => item.parent_code === parentCode)
    }
  }
  return []
})

// Label affiché
const displayLabel = computed(() => {
  if (props.modelValue) {
    const item = pointsStore.lexique.find(l => l.code === props.modelValue)
    return item?.full_path || item?.label || props.modelValue
  }
  return props.placeholder || 'Sélectionner une catégorie'
})

// Vérifier si un élément a des enfants
const hasChildren = (code: string): boolean => {
  return pointsStore.lexique.some(item => item.parent_code === code)
}

// Sélectionner un élément
const selectItem = (item: LexiqueItem) => {
  // Ajouter au chemin
  selectedPath.value = selectedPath.value.slice(0, currentLevel.value)
  selectedPath.value.push(item)

  if (hasChildren(item.code)) {
    // Aller au niveau suivant
    currentLevel.value++
  } else {
    // Sélection finale
    emit('update:modelValue', item.code)
    close()
  }
}

// Confirmer la sélection actuelle (même si pas au dernier niveau)
const confirmSelection = () => {
  if (selectedPath.value.length > 0) {
    const lastItem = selectedPath.value[selectedPath.value.length - 1]
    emit('update:modelValue', lastItem.code)
    close()
  }
}

// Revenir en arrière
const goBack = () => {
  if (currentLevel.value > 0) {
    currentLevel.value--
    selectedPath.value = selectedPath.value.slice(0, currentLevel.value)
  } else {
    close()
  }
}

// Ouvrir le sélecteur
const open = () => {
  isOpen.value = true
  currentLevel.value = 0
  selectedPath.value = []

  // Si une valeur est déjà sélectionnée, reconstruire le chemin
  if (props.modelValue) {
    const item = pointsStore.lexique.find(l => l.code === props.modelValue)
    if (item?.full_path) {
      // Le full_path contient la hiérarchie séparée par " > "
      // On pourrait reconstruire le chemin ici si nécessaire
    }
  }
}

// Fermer
const close = () => {
  isOpen.value = false
  currentLevel.value = 0
  selectedPath.value = []
}

// Titre du niveau actuel
const levelTitle = computed(() => {
  if (currentLevel.value === 0) {
    return 'Catégorie'
  }
  return selectedPath.value[currentLevel.value - 1]?.label || 'Sous-catégorie'
})

// Fil d'Ariane
const breadcrumb = computed(() => {
  return selectedPath.value.map(item => item.label).join(' > ')
})

// Sync avec modelValue externe
watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    selectedPath.value = []
    currentLevel.value = 0
  }
})
</script>

<template>
  <div class="lexique-selector">
    <!-- Bouton d'ouverture -->
    <button
      type="button"
      class="selector-button"
      :class="{ 'has-value': !!modelValue }"
      @click="open"
    >
      <span class="selector-icon">📂</span>
      <span class="selector-label">{{ displayLabel }}</span>
      <span class="selector-arrow">▼</span>
    </button>

    <!-- Modal de sélection -->
    <Teleport to="body">
      <div v-if="isOpen" class="modal-overlay" @click.self="close">
        <div class="modal-content lexique-modal">
          <!-- Header -->
          <div class="modal-header">
            <button class="back-btn" @click="goBack">
              {{ currentLevel > 0 ? '←' : '✕' }}
            </button>
            <div class="modal-title">
              <div class="level-title">{{ levelTitle }}</div>
              <div v-if="breadcrumb" class="breadcrumb">{{ breadcrumb }}</div>
            </div>
            <button
              v-if="selectedPath.length > 0"
              class="confirm-btn"
              @click="confirmSelection"
            >
              ✓
            </button>
          </div>

          <!-- Liste des éléments -->
          <div class="items-list">
            <div
              v-for="item in currentItems"
              :key="item.code"
              class="list-item"
              @click="selectItem(item)"
            >
              <span
                class="item-icon"
                :style="{ background: normalizeColor(item.color_value) || '#1976D2' }"
              >
                {{ item.label.charAt(0).toUpperCase() }}
              </span>

              <span class="item-label">{{ item.label }}</span>

              <span v-if="hasChildren(item.code)" class="item-arrow">›</span>
            </div>

            <div v-if="currentItems.length === 0" class="empty-state">
              <div class="empty-state-icon">📭</div>
              <div class="empty-state-text">Aucune catégorie disponible</div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.lexique-selector {
  width: 100%;
}

.selector-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.2s;
}

.selector-button:focus {
  outline: none;
  border-color: var(--primary-color);
}

.selector-button.has-value {
  border-color: var(--primary-color);
}

.selector-icon {
  font-size: 18px;
}

.selector-label {
  flex: 1;
  font-size: 16px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selector-button:not(.has-value) .selector-label {
  color: var(--text-secondary);
}

.selector-arrow {
  font-size: 10px;
  color: var(--text-secondary);
}

/* Modal */
.lexique-modal {
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--surface-color);
}

.back-btn,
.confirm-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-primary);
}

.back-btn:active,
.confirm-btn:active {
  background: var(--border-color);
}

.confirm-btn {
  color: var(--primary-color);
  font-weight: bold;
}

.modal-title {
  flex: 1;
}

.level-title {
  font-size: 18px;
  font-weight: 600;
}

.breadcrumb {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.items-list {
  flex: 1;
  overflow-y: auto;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background 0.2s;
}

.list-item:active {
  background: var(--background-color);
}

.item-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 16px;
  color: white;
  background: var(--primary-color);
}

.item-label {
  flex: 1;
  font-size: 16px;
}

.item-arrow {
  font-size: 20px;
  color: var(--text-secondary);
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.empty-state-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-state-text {
  color: var(--text-secondary);
}
</style>

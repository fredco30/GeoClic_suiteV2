<script setup lang="ts">
import { computed } from 'vue'
import type { GeometryType } from '@/services/api'

interface Props {
  modelValue: GeometryType
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<{
  'update:modelValue': [value: GeometryType]
}>()

const options = [
  {
    value: 'POINT' as GeometryType,
    icon: '📍',
    label: 'Point',
    description: 'Un seul emplacement'
  },
  {
    value: 'LINESTRING' as GeometryType,
    icon: '📏',
    label: 'Ligne',
    description: 'Tracé linéaire'
  },
  {
    value: 'POLYGON' as GeometryType,
    icon: '⬛',
    label: 'Zone',
    description: 'Surface fermée'
  }
]

const selectType = (type: GeometryType) => {
  if (!props.disabled) {
    emit('update:modelValue', type)
  }
}

const helpText = computed(() => {
  switch (props.modelValue) {
    case 'POINT':
      return 'Touchez la carte ou utilisez le GPS pour placer un point unique.'
    case 'LINESTRING':
      return 'Touchez la carte pour ajouter des points successifs, ou utilisez "Tracer" pour enregistrer un parcours GPS.'
    case 'POLYGON':
      return 'Touchez la carte pour définir les sommets de la zone. Minimum 3 points requis.'
    default:
      return ''
  }
})

const helpColor = computed(() => {
  switch (props.modelValue) {
    case 'POINT':
      return 'blue'
    case 'LINESTRING':
      return 'green'
    case 'POLYGON':
      return 'orange'
    default:
      return 'gray'
  }
})
</script>

<template>
  <div class="geometry-type-selector">
    <div class="selector-header">
      <span class="header-icon">📐</span>
      <span class="header-title">Type de géométrie</span>
    </div>

    <div class="type-options">
      <button
        v-for="option in options"
        :key="option.value"
        :class="['type-option', { selected: modelValue === option.value, disabled }]"
        :disabled="disabled"
        @click="selectType(option.value)"
      >
        <span class="option-icon">{{ option.icon }}</span>
        <span class="option-label">{{ option.label }}</span>
        <span class="option-desc">{{ option.description }}</span>
      </button>
    </div>

    <div :class="['help-box', `help-${helpColor}`]">
      <span class="help-icon">💡</span>
      <span class="help-text">{{ helpText }}</span>
    </div>
  </div>
</template>

<style scoped>
.geometry-type-selector {
  background: var(--surface-color);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.header-icon {
  font-size: 18px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.type-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.type-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  background: var(--background-color);
  border: 2px solid var(--border-color);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s ease;
}

.type-option:hover:not(.disabled) {
  border-color: var(--primary-light);
  background: rgba(var(--primary-rgb), 0.05);
}

.type-option.selected {
  border-color: var(--primary-color);
  background: rgba(var(--primary-rgb), 0.1);
}

.type-option.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.option-icon {
  font-size: 24px;
  margin-bottom: 6px;
}

.option-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.option-desc {
  font-size: 10px;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 2px;
}

.help-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  line-height: 1.4;
}

.help-box.help-blue {
  background: rgba(33, 150, 243, 0.1);
  color: #1565c0;
  border: 1px solid rgba(33, 150, 243, 0.2);
}

.help-box.help-green {
  background: rgba(76, 175, 80, 0.1);
  color: #2e7d32;
  border: 1px solid rgba(76, 175, 80, 0.2);
}

.help-box.help-orange {
  background: rgba(255, 152, 0, 0.1);
  color: #e65100;
  border: 1px solid rgba(255, 152, 0, 0.2);
}

.help-icon {
  flex-shrink: 0;
}

.help-text {
  flex: 1;
}
</style>

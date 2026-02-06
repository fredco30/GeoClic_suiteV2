<script setup lang="ts">
import { computed } from 'vue'
import { gpsService } from '@/services/gps'

const props = defineProps<{
  compact?: boolean
}>()

const status = computed(() => gpsService.status.value)
const position = computed(() => gpsService.position.value)
const error = computed(() => gpsService.error.value)

const statusClass = computed(() => {
  switch (status.value) {
    case 'active': return 'gps-status-active'
    case 'searching': return 'gps-status-searching'
    case 'error': return 'gps-status-error'
    default: return ''
  }
})

const statusIcon = computed(() => {
  switch (status.value) {
    case 'active': return '📍'
    case 'searching': return '🔍'
    case 'error': return '⚠️'
    default: return '📍'
  }
})

const accuracyText = computed(() => {
  if (!position.value) return ''
  return gpsService.formatAccuracy(position.value.accuracy)
})

const coordinatesText = computed(() => {
  if (!position.value) return ''
  return `${position.value.latitude.toFixed(6)}, ${position.value.longitude.toFixed(6)}`
})
</script>

<template>
  <div class="gps-status" :class="[statusClass, { compact: props.compact }]">
    <span class="gps-icon">{{ statusIcon }}</span>

    <div v-if="!props.compact" class="gps-info">
      <template v-if="status === 'active' && position">
        <div class="gps-coords">{{ coordinatesText }}</div>
        <div class="gps-accuracy">Précision: {{ accuracyText }}</div>
      </template>
      <template v-else-if="status === 'searching'">
        <div class="gps-message">Recherche GPS...</div>
      </template>
      <template v-else-if="status === 'error' && error">
        <div class="gps-error">{{ error.message }}</div>
      </template>
      <template v-else>
        <div class="gps-message">GPS inactif</div>
      </template>
    </div>

    <div v-if="status === 'searching'" class="gps-pulse" :style="{ background: 'var(--warning-color)' }"></div>
    <div v-else-if="status === 'active'" class="gps-pulse" :style="{ background: 'var(--success-color)' }"></div>
  </div>
</template>

<style scoped>
.gps-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  background: var(--surface-color);
  border: 1px solid var(--border-color);
}

.gps-status.compact {
  padding: 6px 10px;
  gap: 6px;
}

.gps-status-active {
  background: rgba(76, 175, 80, 0.08);
  border-color: rgba(76, 175, 80, 0.3);
}

.gps-status-searching {
  background: rgba(255, 152, 0, 0.08);
  border-color: rgba(255, 152, 0, 0.3);
}

.gps-status-error {
  background: rgba(244, 67, 54, 0.08);
  border-color: rgba(244, 67, 54, 0.3);
}

.gps-icon {
  font-size: 20px;
  line-height: 1;
}

.compact .gps-icon {
  font-size: 16px;
}

.gps-info {
  flex: 1;
  min-width: 0;
}

.gps-coords {
  font-size: 13px;
  font-weight: 500;
  font-family: monospace;
}

.gps-accuracy,
.gps-message {
  font-size: 12px;
  color: var(--text-secondary);
}

.gps-error {
  font-size: 12px;
  color: var(--error-color);
}

.gps-pulse {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.3);
  }
}
</style>

<script setup lang="ts">
/**
 * HelpTooltip - Infobulle d'aide contextuelle
 * Affiche une icône "?" avec un tooltip au survol ou au clic
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useHelp } from '@/composables/useHelp'

const props = defineProps<{
  /** Clé du tooltip dans le dictionnaire */
  tooltipKey: string
  /** Position du tooltip */
  position?: 'top' | 'bottom' | 'left' | 'right'
  /** Taille de l'icône */
  size?: 'sm' | 'md' | 'lg'
  /** Afficher au clic (mobile) ou au survol (desktop) */
  trigger?: 'hover' | 'click' | 'both'
}>()

const { tooltip } = useHelp()

const isVisible = ref(false)
const tooltipRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLElement | null>(null)

const tooltipText = computed(() => tooltip(props.tooltipKey))

const position = computed(() => props.position || 'top')
const size = computed(() => props.size || 'md')
const trigger = computed(() => props.trigger || 'both')

function show() {
  if (tooltipText.value) {
    isVisible.value = true
  }
}

function hide() {
  isVisible.value = false
}

function toggle() {
  if (isVisible.value) {
    hide()
  } else {
    show()
  }
}

function handleMouseEnter() {
  if (trigger.value === 'hover' || trigger.value === 'both') {
    show()
  }
}

function handleMouseLeave() {
  if (trigger.value === 'hover' || trigger.value === 'both') {
    hide()
  }
}

function handleClick(event: Event) {
  event.stopPropagation()
  if (trigger.value === 'click' || trigger.value === 'both') {
    toggle()
  }
}

// Fermer au clic extérieur
function handleClickOutside(event: MouseEvent) {
  if (
    isVisible.value &&
    triggerRef.value &&
    !triggerRef.value.contains(event.target as Node) &&
    tooltipRef.value &&
    !tooltipRef.value.contains(event.target as Node)
  ) {
    hide()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <span
    v-if="tooltipText"
    class="help-tooltip"
    :class="[`help-tooltip--${size}`]"
    ref="triggerRef"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @click="handleClick"
  >
    <span class="help-tooltip__trigger">
      <svg
        class="help-tooltip__icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    </span>

    <Transition name="tooltip">
      <span
        v-if="isVisible"
        ref="tooltipRef"
        class="help-tooltip__content"
        :class="[`help-tooltip__content--${position}`]"
        role="tooltip"
      >
        {{ tooltipText }}
        <span class="help-tooltip__arrow" />
      </span>
    </Transition>
  </span>
</template>

<style scoped>
.help-tooltip {
  position: relative;
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
}

.help-tooltip__trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: help;
  color: #9ca3af;
  transition: color 0.2s ease;
}

.help-tooltip:hover .help-tooltip__trigger {
  color: #3b82f6;
}

.help-tooltip__icon {
  display: block;
}

/* Tailles */
.help-tooltip--sm .help-tooltip__icon {
  width: 14px;
  height: 14px;
}

.help-tooltip--md .help-tooltip__icon {
  width: 16px;
  height: 16px;
}

.help-tooltip--lg .help-tooltip__icon {
  width: 20px;
  height: 20px;
}

/* Contenu du tooltip */
.help-tooltip__content {
  position: absolute;
  z-index: 1000;
  padding: 0.5rem 0.75rem;
  background: #1f2937;
  color: #f9fafb;
  font-size: 0.8125rem;
  line-height: 1.4;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  white-space: normal;
  max-width: 280px;
  min-width: 150px;
  text-align: left;
  font-weight: 400;
}

/* Positions */
.help-tooltip__content--top {
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.help-tooltip__content--bottom {
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.help-tooltip__content--left {
  right: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}

.help-tooltip__content--right {
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}

/* Flèche */
.help-tooltip__arrow {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #1f2937;
  transform: rotate(45deg);
}

.help-tooltip__content--top .help-tooltip__arrow {
  bottom: -4px;
  left: 50%;
  margin-left: -4px;
}

.help-tooltip__content--bottom .help-tooltip__arrow {
  top: -4px;
  left: 50%;
  margin-left: -4px;
}

.help-tooltip__content--left .help-tooltip__arrow {
  right: -4px;
  top: 50%;
  margin-top: -4px;
}

.help-tooltip__content--right .help-tooltip__arrow {
  left: -4px;
  top: 50%;
  margin-top: -4px;
}

/* Animation */
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
}

.help-tooltip__content--top.tooltip-enter-from,
.help-tooltip__content--top.tooltip-leave-to {
  transform: translateX(-50%) translateY(4px);
}

.help-tooltip__content--bottom.tooltip-enter-from,
.help-tooltip__content--bottom.tooltip-leave-to {
  transform: translateX(-50%) translateY(-4px);
}

.help-tooltip__content--left.tooltip-enter-from,
.help-tooltip__content--left.tooltip-leave-to {
  transform: translateY(-50%) translateX(4px);
}

.help-tooltip__content--right.tooltip-enter-from,
.help-tooltip__content--right.tooltip-leave-to {
  transform: translateY(-50%) translateX(-4px);
}
</style>

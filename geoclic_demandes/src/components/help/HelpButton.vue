<script setup lang="ts">
/**
 * HelpButton - Bouton d'aide contextuelle
 * Affiche un bouton visible "? Aide" qui ouvre le drawer d'aide pour la page spécifiée
 */

import { useHelp } from '@/composables/useHelp'

const props = defineProps<{
  /** Clé de la page d'aide à afficher */
  pageKey: string
  /** Variante d'affichage: pill (défaut), icon, text */
  variant?: 'icon' | 'text' | 'pill'
  /** Taille */
  size?: 'sm' | 'md' | 'lg'
}>()

const { openHelp } = useHelp()

function handleClick() {
  openHelp(props.pageKey)
}

// Utiliser 'pill' par défaut pour plus de visibilité
const effectiveVariant = props.variant || 'pill'
</script>

<template>
  <button
    class="help-button"
    :class="[
      `help-button--${effectiveVariant}`,
      `help-button--${size || 'md'}`
    ]"
    @click.stop="handleClick"
    type="button"
    aria-label="Afficher l'aide"
    title="Cliquez pour afficher l'aide de cette page"
  >
    <svg
      class="help-button__icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
    <span class="help-button__label">Aide</span>
  </button>
</template>

<style scoped>
.help-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  vertical-align: middle;
}

/* Variante icon */
.help-button--icon {
  background: transparent;
  color: #6b7280;
  border-radius: 50%;
}

.help-button--icon:hover {
  background: #f3f4f6;
  color: #3b82f6;
}

.help-button--icon .help-button__label {
  display: none;
}

/* Variante text */
.help-button--text {
  background: transparent;
  color: #3b82f6;
  font-weight: 500;
  padding: 0;
}

.help-button--text:hover {
  color: #2563eb;
  text-decoration: underline;
}

/* Variante pill (défaut) - Plus visible */
.help-button--pill {
  background: #1976d2;
  color: white;
  font-weight: 600;
  border-radius: 9999px;
  box-shadow: 0 2px 4px rgba(25, 118, 210, 0.3);
}

.help-button--pill:hover {
  background: #1565c0;
  box-shadow: 0 3px 6px rgba(25, 118, 210, 0.4);
  transform: translateY(-1px);
}

.help-button--pill:active {
  transform: translateY(0);
}

/* Tailles */
.help-button--sm {
  padding: 0.25rem;
}

.help-button--sm .help-button__icon {
  width: 14px;
  height: 14px;
}

.help-button--sm.help-button--pill,
.help-button--sm.help-button--text {
  font-size: 0.75rem;
  padding: 0.25rem 0.625rem;
}

.help-button--md {
  padding: 0.375rem;
}

.help-button--md .help-button__icon {
  width: 18px;
  height: 18px;
}

.help-button--md.help-button--pill,
.help-button--md.help-button--text {
  font-size: 0.875rem;
  padding: 0.375rem 0.875rem;
}

.help-button--lg {
  padding: 0.5rem;
}

.help-button--lg .help-button__icon {
  width: 22px;
  height: 22px;
}

.help-button--lg.help-button--pill,
.help-button--lg.help-button--text {
  font-size: 1rem;
  padding: 0.5rem 1rem;
}
</style>

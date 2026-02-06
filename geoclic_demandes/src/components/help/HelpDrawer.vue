<script setup lang="ts">
/**
 * HelpDrawer - Panneau latéral d'aide contextuelle
 * S'ouvre depuis la droite avec le contenu d'aide de la page courante
 */

import { useHelp } from '@/composables/useHelp'

const { isHelpDrawerOpen, currentPageHelp, closeHelp } = useHelp()

// Fermer avec Escape
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    closeHelp()
  }
}
</script>

<template>
  <!-- Overlay -->
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isHelpDrawerOpen"
        class="help-overlay"
        @click="closeHelp"
        @keydown="onKeydown"
      />
    </Transition>

    <!-- Drawer -->
    <Transition name="slide">
      <aside
        v-if="isHelpDrawerOpen && currentPageHelp"
        class="help-drawer"
        role="dialog"
        aria-modal="true"
        :aria-label="`Aide: ${currentPageHelp.title}`"
      >
        <!-- Header -->
        <header class="help-header">
          <div class="help-title">
            <span class="help-icon">{{ currentPageHelp.icon }}</span>
            <h2>{{ currentPageHelp.title }}</h2>
          </div>
          <button
            class="help-close"
            @click="closeHelp"
            aria-label="Fermer l'aide"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </header>

        <!-- Content -->
        <div class="help-content">
          <div
            v-for="(section, index) in currentPageHelp.sections"
            :key="index"
            class="help-section"
          >
            <h3>{{ section.title }}</h3>
            <div class="help-text" v-html="formatContent(section.content)" />
          </div>
        </div>

        <!-- Footer -->
        <footer class="help-footer">
          <span class="help-hint">
            Appuyez sur <kbd>Échap</kbd> pour fermer
          </span>
        </footer>
      </aside>
    </Transition>
  </Teleport>
</template>

<script lang="ts">
// Fonction pour formater le contenu markdown simplifié
function formatContent(content: string): string {
  return content
    // Gras **texte**
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italique *texte*
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Listes à puces
    .replace(/^• /gm, '<li>')
    .replace(/<li>([^\n]+)/g, '<li>$1</li>')
    // Sauts de ligne
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    // Wrapper paragraphe
    .replace(/^(.+)$/s, '<p>$1</p>')
    // Nettoyer les listes
    .replace(/<p>(<li>)/g, '<ul>$1')
    .replace(/(<\/li>)<br>/g, '$1')
    .replace(/(<\/li>)(<\/p>)/g, '$1</ul>$2')
    .replace(/(<\/li>)(<p>)/g, '$1</ul>$2')
}
</script>

<style scoped>
/* Overlay semi-transparent */
.help-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 998;
}

/* Drawer panel */
.help-drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 420px;
  max-width: 90vw;
  background: white;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.15);
  z-index: 999;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.help-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.help-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.help-icon {
  font-size: 1.5rem;
}

.help-title h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.help-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 8px;
  padding: 0.5rem;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
}

.help-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Content */
.help-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.help-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.help-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.help-section h3 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.help-text {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #4b5563;
}

.help-text :deep(p) {
  margin: 0 0 0.75rem 0;
}

.help-text :deep(p:last-child) {
  margin-bottom: 0;
}

.help-text :deep(strong) {
  color: #1f2937;
  font-weight: 600;
}

.help-text :deep(ul) {
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}

.help-text :deep(li) {
  margin-bottom: 0.25rem;
}

.help-text :deep(li:last-child) {
  margin-bottom: 0;
}

/* Footer */
.help-footer {
  padding: 1rem 1.5rem;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.help-hint {
  font-size: 0.8rem;
  color: #6b7280;
}

.help-hint kbd {
  display: inline-block;
  padding: 0.15rem 0.4rem;
  font-size: 0.75rem;
  font-family: inherit;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.05);
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

/* Responsive */
@media (max-width: 480px) {
  .help-drawer {
    width: 100%;
    max-width: 100%;
  }
}
</style>

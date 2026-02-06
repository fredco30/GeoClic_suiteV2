/**
 * Composable pour la gestion de l'aide contextuelle
 */

import { ref, computed } from 'vue'
import { getPageHelp, getTooltip, type PageHelp } from '@/i18n/help'

// État global du drawer d'aide
const isHelpDrawerOpen = ref(false)
const currentHelpPage = ref<string | null>(null)

export function useHelp() {
  /**
   * Ouvre le drawer d'aide pour une page spécifique
   */
  function openHelp(pageKey: string) {
    currentHelpPage.value = pageKey
    isHelpDrawerOpen.value = true
  }

  /**
   * Ferme le drawer d'aide
   */
  function closeHelp() {
    isHelpDrawerOpen.value = false
  }

  /**
   * Toggle le drawer d'aide
   */
  function toggleHelp(pageKey?: string) {
    if (pageKey) {
      currentHelpPage.value = pageKey
    }
    isHelpDrawerOpen.value = !isHelpDrawerOpen.value
  }

  /**
   * Récupère le contenu d'aide de la page courante
   */
  const currentPageHelp = computed<PageHelp | null>(() => {
    if (!currentHelpPage.value) return null
    return getPageHelp(currentHelpPage.value)
  })

  /**
   * Récupère un tooltip par sa clé
   */
  function tooltip(key: string): string {
    return getTooltip(key)
  }

  return {
    // État
    isHelpDrawerOpen,
    currentHelpPage,
    currentPageHelp,

    // Actions
    openHelp,
    closeHelp,
    toggleHelp,
    tooltip
  }
}

export default useHelp

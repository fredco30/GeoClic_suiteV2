import { ref, watch, onMounted } from 'vue'

const STORAGE_KEY = 'geoclic-theme'

// État partagé entre tous les composants
const isDark = ref(false)

export function useTheme() {
  // Initialiser le thème depuis localStorage ou préférence système
  function initTheme() {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      isDark.value = stored === 'dark'
    } else {
      // Utiliser la préférence système
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    applyTheme()
  }

  // Appliquer le thème au document
  function applyTheme() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // Toggle le thème
  function toggleTheme() {
    isDark.value = !isDark.value
    localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')
    applyTheme()
  }

  // Écouter les changements
  watch(isDark, applyTheme)

  onMounted(() => {
    initTheme()
  })

  return {
    isDark,
    toggleTheme,
    initTheme
  }
}

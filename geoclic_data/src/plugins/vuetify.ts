/**
 * plugins/vuetify.ts
 *
 * GéoClic Data - Configuration Vuetify
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'
import { fr } from 'vuetify/locale'

// Thème GéoClic
const geoclicTheme = {
  dark: false,
  colors: {
    background: '#F5F5F5',
    surface: '#FFFFFF',
    primary: '#1976D2',      // Bleu GéoClic
    secondary: '#424242',
    accent: '#82B1FF',
    error: '#FF5252',
    info: '#2196F3',
    success: '#4CAF50',
    warning: '#FFC107',
    // Couleurs métier
    voirie: '#795548',
    eclairage: '#FFC107',
    espacesverts: '#4CAF50',
    batiments: '#9C27B0',
    reseaux: '#00BCD4',
  },
}

const geoclicDarkTheme = {
  dark: true,
  colors: {
    background: '#121212',
    surface: '#1E1E1E',
    primary: '#2196F3',
    secondary: '#757575',
    accent: '#82B1FF',
    error: '#FF5252',
    info: '#2196F3',
    success: '#4CAF50',
    warning: '#FFC107',
    voirie: '#A1887F',
    eclairage: '#FFD54F',
    espacesverts: '#81C784',
    batiments: '#BA68C8',
    reseaux: '#4DD0E1',
  },
}

export default createVuetify({
  locale: {
    locale: 'fr',
    messages: { fr },
  },
  theme: {
    defaultTheme: 'geoclicTheme',
    themes: {
      geoclicTheme,
      geoclicDarkTheme,
    },
  },
  defaults: {
    VBtn: {
      rounded: 'lg',
    },
    VCard: {
      rounded: 'lg',
      elevation: 2,
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VDataTable: {
      hover: true,
    },
  },
})

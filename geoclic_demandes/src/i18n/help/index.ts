/**
 * Index des contenus d'aide
 * Structure multilingue préparée pour le futur
 */

import helpContentFr from './fr'

// Langues disponibles
export type Locale = 'fr' | 'en' | 'es' | 'de'

// Structure des contenus
export interface HelpSection {
  title: string
  content: string
}

export interface PageHelp {
  title: string
  icon: string
  sections: HelpSection[]
}

export interface HelpContent {
  pages: Record<string, PageHelp>
  tooltips: Record<string, string>
}

// Contenus par langue
const helpContents: Record<Locale, HelpContent> = {
  fr: helpContentFr,
  // Langues futures (non implémentées, fallback sur français)
  en: helpContentFr,
  es: helpContentFr,
  de: helpContentFr
}

// Langue par défaut
let currentLocale: Locale = 'fr'

/**
 * Définit la langue actuelle
 */
export function setHelpLocale(locale: Locale) {
  currentLocale = locale
}

/**
 * Récupère la langue actuelle
 */
export function getHelpLocale(): Locale {
  return currentLocale
}

/**
 * Récupère le contenu d'aide pour une page
 */
export function getPageHelp(pageKey: string): PageHelp | null {
  const content = helpContents[currentLocale]
  return content?.pages?.[pageKey] || null
}

/**
 * Récupère un tooltip
 */
export function getTooltip(key: string): string {
  const content = helpContents[currentLocale]
  return content?.tooltips?.[key] || ''
}

/**
 * Récupère tous les tooltips
 */
export function getAllTooltips(): Record<string, string> {
  const content = helpContents[currentLocale]
  return content?.tooltips || {}
}

export { helpContentFr }
export default helpContents

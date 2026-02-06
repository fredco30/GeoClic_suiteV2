<script setup lang="ts">
import { ref, computed } from 'vue'

interface Category {
  id: string
  parent_id: string | null
  nom: string
  description?: string
  icone: string
  couleur: number
  actif: boolean
  children?: Category[]
}

const props = defineProps<{
  categories: Category[]
  modelValue: Category | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: Category | null): void
}>()

// State
const selectedParent = ref<Category | null>(null)

// Build tree structure
const categoriesTree = computed(() => {
  const rootCats = props.categories.filter(c => !c.parent_id && c.actif)
  return rootCats.map(cat => ({
    ...cat,
    children: props.categories.filter(c => c.parent_id === cat.id && c.actif)
  }))
})

// Current view: show parents or children
const showingChildren = computed(() => selectedParent.value !== null)

const currentCategories = computed(() => {
  if (selectedParent.value) {
    const parent = categoriesTree.value.find(c => c.id === selectedParent.value?.id)
    return parent?.children || []
  }
  return categoriesTree.value
})

// Helpers
function intToHex(color: number): string {
  return '#' + (color & 0xFFFFFF).toString(16).padStart(6, '0')
}

// Material Design Icons SVG paths
const iconPaths: Record<string, string> = {
  // Voirie / Routes
  'route': 'M11 16H13V14H11V16M11 12H13V4H11V12M4 22H6V17H4V22M4 15H6V11H4V15M4 9H6V2H4V9M18 22H20V14H18V22M18 12H20V8H18V12M18 2V6H20V2H18Z',
  'directions_car': 'M18.92 6.01C18.72 5.42 18.16 5 17.5 5H6.5C5.84 5 5.28 5.42 5.08 6.01L3 12V20C3 20.55 3.45 21 4 21H5C5.55 21 6 20.55 6 20V19H18V20C18 20.55 18.45 21 19 21H20C20.55 21 21 20.55 21 20V12L18.92 6.01M6.5 16C5.67 16 5 15.33 5 14.5S5.67 13 6.5 13 8 13.67 8 14.5 7.33 16 6.5 16M17.5 16C16.67 16 16 15.33 16 14.5S16.67 13 17.5 13 19 13.67 19 14.5 18.33 16 17.5 16M5 11L6.5 6.5H17.5L19 11H5Z',
  'traffic': 'M20 10H17V8.86C18.72 8.41 20 6.86 20 5H17V4C17 3.45 16.55 3 16 3H8C7.45 3 7 3.45 7 4V5H4C4 6.86 5.28 8.41 7 8.86V10H4C4 11.86 5.28 13.41 7 13.86V15H4C4 16.86 5.28 18.41 7 18.86V20C7 20.55 7.45 21 8 21H16C16.55 21 17 20.55 17 20V18.86C18.72 18.41 20 16.86 20 15H17V13.86C18.72 13.41 20 11.86 20 10M12 19C11.45 19 11 18.55 11 18S11.45 17 12 17 13 17.45 13 18 12.55 19 12 19M12 14C11.45 14 11 13.55 11 13S11.45 12 12 12 13 12.45 13 13 12.55 14 12 14M12 9C11.45 9 11 8.55 11 8S11.45 7 12 7 13 7.45 13 8 12.55 9 12 9Z',

  // Eau
  'water_drop': 'M12 2C12 2 5 9 5 14C5 17.87 8.13 21 12 21C15.87 21 19 17.87 19 14C19 9 12 2 12 2M12 19C9.24 19 7 16.76 7 14C7 11.95 9.53 8.24 12 5.36C14.47 8.24 17 11.95 17 14C17 16.76 14.76 19 12 19Z',
  'opacity': 'M17.66 8L12 2.35L6.34 8C4.78 9.56 4 11.64 4 13.64S4.78 17.74 6.34 19.3C7.9 20.86 9.95 21.64 12 21.64S16.1 20.86 17.66 19.3C19.22 17.74 20 15.64 20 13.64S19.22 9.56 17.66 8M6 14C6 12 6.62 10.73 7.76 9.6L12 5.27L16.24 9.65C17.38 10.77 18 12 18 14H6Z',
  'local_drink': 'M3 2L5 20.23C5.13 21.23 5.97 22 7 22H17C18.03 22 18.87 21.23 19 20.23L21 2H3M5.22 4H18.78L18.25 8H5.75L5.22 4M17.75 18H6.25L5.89 14H18.11L17.75 18Z',
  'waves': 'M17 16.99C15.8 16.99 14.68 16.5 13.89 15.65C13.1 14.8 13.1 13.21 13.89 12.36L17 9L20.11 12.36C20.9 13.21 20.9 14.8 20.11 15.65C19.32 16.5 18.2 16.99 17 16.99M2 19C2 19 6 14.58 6 11C6 9.07 4.93 7.36 4.5 7C4.07 6.64 2.93 7.64 2.5 8C2.07 8.36 1 7.64 1 7C1 4.79 2.79 3 5 3C9.17 3 12 7.58 12 11C12 14.58 10 19 10 19H2M7 16C7.83 16 8.5 15.33 8.5 14.5S7.83 13 7 13 5.5 13.67 5.5 14.5 6.17 16 7 16Z',

  // Espaces verts
  'park': 'M17 12H20L12 4L4 12H7V20H10V15H14V20H17V12Z',
  'nature': 'M13 16.12C16.47 15.71 19.17 12.76 19.17 9.17C19.17 5.3 16.04 2.17 12.17 2.17C8.3 2.17 5.17 5.3 5.17 9.17C5.17 12.76 7.87 15.71 11.33 16.12V20H6V22H18V20H13V16.12M12.17 4.17C14.93 4.17 17.17 6.41 17.17 9.17C17.17 11.93 14.93 14.17 12.17 14.17C9.41 14.17 7.17 11.93 7.17 9.17C7.17 6.41 9.41 4.17 12.17 4.17Z',
  'eco': 'M6.05 8.05C7.04 7.06 8.33 6.41 9.75 6.16L12 9V2C6.48 2 2 6.48 2 12C2 14.19 2.74 16.21 3.97 17.83L6.05 8.05M19.95 15.95L17.87 5.17C16.79 3.74 15.21 2.78 13.44 2.42L11 4.87V12L19.95 15.95M14.55 21.94C14.06 21.98 13.54 22 13 22C10.81 22 8.79 21.26 7.17 20.03L15.95 8.05C16.94 9.04 17.59 10.33 17.84 11.75L14.55 21.94Z',
  'grass': 'M12 20H2V18H7.75C7.02 15.19 4.81 12.99 2 12.26V10.24C5.17 10.83 7.83 12.63 9.5 15.19V4H11.5V11H13V4H15V11H17V4H19V11.2C18.1 11.07 17.17 11 16.22 11C15.87 11 15.53 11.01 15.19 11.03C14.47 12.62 13.29 14.03 11.83 15.12C12.37 16.62 12.64 18.25 12.64 19.94C12.64 19.96 12.64 19.98 12.64 20H12Z',

  // Eclairage
  'lightbulb': 'M12 2C8.14 2 5 5.14 5 9C5 11.38 6.19 13.47 8 14.74V17C8 17.55 8.45 18 9 18H15C15.55 18 16 17.55 16 17V14.74C17.81 13.47 19 11.38 19 9C19 5.14 15.86 2 12 2M14 16H10V15H14V16M14.86 13.38L14 13.88V14H10V13.88L9.14 13.38C7.79 12.54 7 11.1 7 9.5C7 6.46 9.46 4 12.5 4C15.04 4 17 6 17 9C17 10.6 16.21 12.04 14.86 13.38Z',
  'wb_incandescent': 'M3.55 18.54L4.96 19.95L6.76 18.16L5.34 16.74M11 22.45H13V19.5H11M4 10.5H1V12.5H4M15 6.31V1.5H9V6.31C7.21 7.35 6 9.28 6 11.5C6 14.81 8.69 17.5 12 17.5S18 14.81 18 11.5C18 9.28 16.79 7.35 15 6.31M11 3.5H13V5.69C12.68 5.58 12.35 5.5 12 5.5S11.32 5.58 11 5.69M12 15.5C9.79 15.5 8 13.71 8 11.5C8 9.94 8.91 8.57 10.25 7.91L11 7.54V5.5H13V7.54L13.75 7.91C15.09 8.57 16 9.94 16 11.5C16 13.71 14.21 15.5 12 15.5M20 10.5V12.5H23V10.5M17.24 18.16L19.04 19.95L20.45 18.54L18.66 16.74',

  // Déchets
  'delete': 'M19 4H15.5L14.5 3H9.5L8.5 4H5V6H19M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19Z',
  'recycling': 'M21.82 15.42L19.32 19.75C18.83 20.61 17.92 21.06 17 21H15V19H17.82L20.32 15H17V13H22V14.18C22 14.6 21.94 15.01 21.82 15.42M12.28 20L9.78 15.67L11.18 13.29L14.63 19.12L13.23 21.5L12.28 20M12 9L10.6 11.38L9.2 9M4.18 14C4.06 13.6 4 13.18 4 12.75V11H6V13.72L3.5 18.05H7V20H2.18C1.76 20 1.43 19.73 1.18 19.36C0.93 19 0.87 18.57 1 18.18L3.5 13.85L4.18 14M12.03 3C12.5 3 12.95 3.09 13.36 3.27L15.38 0.84L16.84 2L14.96 4.29C15.36 4.7 15.65 5.21 15.78 5.78L20.56 4.44L21 6.38L15.93 7.8L15 9L14.55 9.78L14.03 10.7L10.63 4.87C11.04 4.34 11.5 3 12.03 3M7 13H2V11H4.22C4.61 10 5.31 9.13 6.22 8.5L4.44 5.22L6.16 4.28L7.94 7.56C8.6 7.35 9.28 7.25 10 7.25L12 11L9.4 15.38L7 13Z',
  'local_shipping': 'M20 8H17V4H3C1.9 4 1 4.9 1 6V17H3C3 18.66 4.34 20 6 20S9 18.66 9 17H15C15 18.66 16.34 20 18 20S21 18.66 21 17H23V12L20 8M6 18.5C5.17 18.5 4.5 17.83 4.5 17S5.17 15.5 6 15.5 7.5 16.17 7.5 17 6.83 18.5 6 18.5M19.5 9.5L21.46 12H17V9.5H19.5M18 18.5C17.17 18.5 16.5 17.83 16.5 17S17.17 15.5 18 15.5 19.5 16.17 19.5 17 18.83 18.5 18 18.5Z',

  // Signalement général
  'report_problem': 'M1 21H23L12 2L1 21M12 18C11.45 18 11 17.55 11 17S11.45 16 12 16 13 16.45 13 17 12.55 18 12 18M13 14H11V10H13V14Z',
  'warning': 'M1 21H23L12 2L1 21M12 18C11.45 18 11 17.55 11 17S11.45 16 12 16 13 16.45 13 17 12.55 18 12 18M13 14H11V10H13V14Z',
  'error': 'M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2M13 17H11V15H13V17M13 13H11V7H13V13Z',
  'info': 'M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2M13 17H11V11H13V17M13 9H11V7H13V9Z',

  // Bâtiments
  'home': 'M10 20V14H14V20H19V12H22L12 3L2 12H5V20H10Z',
  'apartment': 'M17 11H19V13H17V11M17 15H19V17H17V15M17 7H19V9H17V7M13 1V3H11V1H5V21H11V19H13V21H19V9H17V7H19V1H13M9 19H7V17H9V19M9 15H7V13H9V15M9 11H7V9H9V11M9 7H7V5H9V7M13 15H11V13H13V15M13 11H11V9H13V11M13 7H11V5H13V7Z',
  'business': 'M12 7V3H2V21H22V7H12M6 19H4V17H6V19M6 15H4V13H6V15M6 11H4V9H6V11M6 7H4V5H6V7M10 19H8V17H10V19M10 15H8V13H10V15M10 11H8V9H10V11M10 7H8V5H10V7M20 19H12V17H14V15H12V13H14V11H12V9H20V19M18 11H16V13H18V11M18 15H16V17H18V15Z',

  // Mobilier urbain
  'chair': 'M6 19H8V21H6V19M16 19H18V21H16V19M12 3C9.79 3 8 4.79 8 7V13H16V7C16 4.79 14.21 3 12 3M6 10H8V13H6V10M16 10H18V13H16V10M6 15H18V17H6V15Z',
  'deck': 'M22 9L12 2L2 9H11V22H13V9H22M4.5 11L12 5.5L19.5 11H4.5Z',
  'local_parking': 'M13 3H6V21H10V15H13C16.31 15 19 12.31 19 9S16.31 3 13 3M13 11H10V7H13C14.1 7 15 7.9 15 9S14.1 11 13 11Z',

  // Sport/Loisirs
  'sports_soccer': 'M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2M13 5.3L14.35 4.35C16.17 5.19 17.66 6.6 18.6 8.35L18.2 10.12L16.53 10.8L13 8.5V5.3M9.65 4.35L11 5.3V8.5L7.47 10.8L5.8 10.12L5.4 8.35C6.34 6.6 7.83 5.19 9.65 4.35M7.08 17.11L5.24 17.17C4.45 15.68 4 13.9 4 12C4 11.63 4.02 11.27 4.07 10.91L5.65 11.56L7.08 14V17.11M14.58 18.95C13.76 19.16 12.89 19.27 12 19.27S10.24 19.16 9.42 18.95L8.42 17.28V14.5L12 12.13L15.58 14.5V17.28L14.58 18.95M18.76 17.17L16.92 17.11V14L18.35 11.56L19.93 10.91C19.98 11.27 20 11.63 20 12C20 13.9 19.55 15.68 18.76 17.17Z',
  'beach_access': 'M13.13 14.56L14.56 13.13L21 19.57L19.57 21L13.13 14.56M17.42 8.83L20.28 5.97C16.33 2.02 9.93 2.02 5.97 5.97L8.83 8.83C11.25 6.41 15.01 6.41 17.42 8.83M5.97 5.97C2.02 9.92 2.02 16.32 5.97 20.28L8.83 17.42C6.41 15 6.41 11.24 8.83 8.83L5.97 5.97M8.83 8.83C6.41 11.25 6.41 15.01 8.83 17.42L12 14.25L8.83 8.83Z',

  // Animaux
  'pets': 'M4.5 12C5.88 12 7 10.88 7 9.5S5.88 7 4.5 7 2 8.12 2 9.5 3.12 12 4.5 12M9 8C10.38 8 11.5 6.88 11.5 5.5S10.38 3 9 3 6.5 4.12 6.5 5.5 7.62 8 9 8M15 8C16.38 8 17.5 6.88 17.5 5.5S16.38 3 15 3 12.5 4.12 12.5 5.5 13.62 8 15 8M19.5 12C20.88 12 22 10.88 22 9.5S20.88 7 19.5 7 17 8.12 17 9.5 18.12 12 19.5 12M17.34 14.86C15.73 13.7 13.68 13 12 13S8.27 13.7 6.66 14.86C5.79 15.5 5.27 16.47 5.27 17.6C5.27 19.81 7.04 21.62 9.21 21.62C10.17 21.62 11.12 21.23 11.89 20.5C11.93 20.46 11.97 20.46 12 20.46S12.07 20.46 12.11 20.5C12.88 21.23 13.83 21.62 14.79 21.62C16.96 21.62 18.73 19.81 18.73 17.6C18.73 16.47 18.21 15.5 17.34 14.86Z',

  // Construction
  'construction': 'M13.78 15.3L19.78 21.3L21.89 19.14L15.89 13.14L13.78 15.3M17.5 10.1C17.11 10.1 16.69 10.05 16.36 9.91L4.97 21.25L2.86 19.14L10.27 11.74L8.5 9.96L7.78 10.66L6.33 9.25V12.11L5.63 12.81L2.11 9.25L2.81 8.55H5.62L4.22 7.14L7.78 3.58C8.95 2.41 10.83 2.41 12 3.58L9.89 5.74L11.27 7.11L10.57 7.81L12.38 9.63L14.54 7.46C14.39 7.14 14.35 6.72 14.35 6.31C14.35 4.59 15.72 3.22 17.5 3.22C18.09 3.22 18.61 3.37 19.08 3.63L16.54 6.17L17.93 7.56L20.5 5C20.75 5.47 20.91 6 20.91 6.58C20.91 8.36 19.55 9.72 17.77 9.72L17.5 10.1Z',
  'engineering': 'M9 15C6.33 15 1 16.33 1 19V21H17V19C17 16.33 11.67 15 9 15M9 12C11.21 12 13 10.21 13 8S11.21 4 9 4 5 5.79 5 8 6.79 12 9 12M15.39 16.56C16.71 17.54 17.75 18.77 17.75 19.5V21H23V19.5C23 17.87 19.39 16.75 15.39 16.56M14.45 12C14.71 11.4 14.84 10.72 14.84 10S14.71 8.6 14.45 8C15.13 7.38 15.54 6.74 15.54 5.5C15.54 3.29 17.33 1.5 19.54 1.5S23.54 3.29 23.54 5.5C23.54 7.71 21.75 9.5 19.54 9.5C19.36 9.5 19.17 9.5 19 9.47C18.81 10.06 18.56 10.61 18.24 11.13C17.44 12.42 16 13 14.45 12Z',

  // Sécurité
  'security': 'M12 1L3 5V11C3 16.55 6.84 21.74 12 23C17.16 21.74 21 16.55 21 11V5L12 1M12 11.99H19C18.47 16.11 15.72 19.78 12 20.93V12H5V6.3L12 3.19V11.99Z',
  'local_police': 'M12 1L3 5V11C3 16.55 6.84 21.74 12 23C17.16 21.74 21 16.55 21 11V5L12 1M12 11.99H19C18.47 16.11 15.72 19.78 12 20.93V12H5V6.3L12 3.19V11.99Z',

  // Autre
  'more_horiz': 'M6 10C4.9 10 4 10.9 4 12S4.9 14 6 14 8 13.1 8 12 7.1 10 6 10M18 10C16.9 10 16 10.9 16 12S16.9 14 18 14 20 13.1 20 12 19.1 10 18 10M12 10C10.9 10 10 10.9 10 12S10.9 14 12 14 14 13.1 14 12 13.1 10 12 10Z',
  'help': 'M15.07 11.25L14.17 12.17C13.45 12.89 13 13.5 13 15H11V14.5C11 13.39 11.45 12.39 12.17 11.67L13.41 10.41C13.78 10.05 14 9.55 14 9C14 7.89 13.1 7 12 7S10 7.89 10 9H8C8 6.79 9.79 5 12 5S16 6.79 16 9C16 9.88 15.64 10.67 15.07 11.25M13 19H11V17H13V19M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2M12 20C7.59 20 4 16.41 4 12S7.59 4 12 4 20 7.59 20 12 16.41 20 12 20Z',
}

function getIconPath(iconName: string): string {
  return iconPaths[iconName] || iconPaths['report_problem']
}

// Actions
function selectCategory(category: Category & { children?: Category[] }) {
  // If it's a parent with children, navigate to children
  if (!category.parent_id && category.children && category.children.length > 0) {
    selectedParent.value = category
  } else {
    // It's a leaf category (no children or is a child itself) - select it
    emit('update:modelValue', category)
  }
}

function goBack() {
  selectedParent.value = null
}

function isSelected(category: Category): boolean {
  return props.modelValue?.id === category.id
}
</script>

<template>
  <div class="category-selector">
    <!-- Back button when showing subcategories -->
    <div v-if="showingChildren" class="back-header">
      <button class="back-btn" @click="goBack">
        <svg viewBox="0 0 24 24" class="back-icon">
          <path fill="currentColor" d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z"/>
        </svg>
        <span>Retour</span>
      </button>
      <h3 class="parent-title">{{ selectedParent!.nom }}</h3>
    </div>

    <!-- Category tiles -->
    <div class="categories-grid">
      <button
        v-for="category in currentCategories"
        :key="category.id"
        :class="['category-tile', { selected: isSelected(category) }]"
        :style="{ backgroundColor: intToHex(category.couleur) }"
        @click="selectCategory(category)"
      >
        <!-- SVG Icon -->
        <svg viewBox="0 0 24 24" class="tile-icon">
          <path fill="currentColor" :d="getIconPath(category.icone)"/>
        </svg>

        <!-- Category name -->
        <span class="tile-name">{{ category.nom }}</span>

        <!-- Category description -->
        <span v-if="category.description" class="tile-description">{{ category.description }}</span>

        <!-- Checkmark for selected -->
        <div v-if="isSelected(category)" class="selected-check">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z"/>
          </svg>
        </div>

        <!-- Arrow indicator for categories with subcategories -->
        <div
          v-if="!category.parent_id && category.children && category.children.length > 0"
          class="subcategory-arrow"
        >
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M8.59 16.59L13.17 12L8.59 7.41L10 6L16 12L10 18L8.59 16.59Z"/>
          </svg>
        </div>
      </button>
    </div>

    <!-- Empty state -->
    <div v-if="currentCategories.length === 0" class="empty-state">
      <svg viewBox="0 0 24 24" class="empty-icon">
        <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2M13 17H11V15H13V17M13 13H11V7H13V13Z"/>
      </svg>
      <p>Aucune catégorie disponible</p>
    </div>
  </div>
</template>

<style scoped>
.category-selector {
  width: 100%;
}

/* Back header */
.back-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 0.75rem 0;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f3f4f6;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  color: #374151;
  transition: background 0.2s;
}

.back-btn:hover {
  background: #e5e7eb;
}

.back-icon {
  width: 20px;
  height: 20px;
}

.parent-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

/* Categories Grid - 2 columns like mobile app */
.categories-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px;
}

/* Category Tile - Full color background */
.category-tile {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem 1rem;
  min-height: 150px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.category-tile:hover {
  filter: brightness(1.1);
  transform: scale(1.02);
}

.category-tile.selected {
  filter: brightness(0.9);
}

/* SVG Icon - White outline style */
.tile-icon {
  width: 64px;
  height: 64px;
  color: white;
  opacity: 0.95;
}

/* Category name - White uppercase */
.tile-name {
  font-weight: 700;
  font-size: 0.9rem;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  line-height: 1.2;
  max-width: 100%;
  word-wrap: break-word;
}

/* Category description */
.tile-description {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 400;
  line-height: 1.3;
  max-width: 100%;
  text-align: center;
  margin-top: -0.25rem;
  padding: 0 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Selected checkmark */
.selected-check {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  width: 28px;
  height: 28px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.selected-check svg {
  width: 18px;
  height: 18px;
  color: #059669;
}

/* Arrow for subcategories */
.subcategory-arrow {
  position: absolute;
  bottom: 0.5rem;
  right: 0.5rem;
  opacity: 0.7;
}

.subcategory-arrow svg {
  width: 24px;
  height: 24px;
  color: white;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 1rem;
  color: #9ca3af;
}

/* Responsive */
@media (max-width: 480px) {
  .category-tile {
    min-height: 130px;
    padding: 1.5rem 0.75rem;
  }

  .tile-icon {
    width: 48px;
    height: 48px;
  }

  .tile-name {
    font-size: 0.8rem;
  }
}

@media (min-width: 768px) {
  .categories-grid {
    max-width: 600px;
    margin: 0 auto;
  }

  .category-tile {
    min-height: 180px;
  }

  .tile-icon {
    width: 72px;
    height: 72px;
  }

  .tile-name {
    font-size: 1rem;
  }
}
</style>

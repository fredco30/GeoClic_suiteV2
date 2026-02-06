<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

interface BreadcrumbItem {
  label: string
  path?: string
}

const route = useRoute()

const routeLabels: Record<string, string> = {
  dashboard: 'Tableau de bord',
  demandes: 'Demandes',
  'demande-detail': 'Détail demande',
  carte: 'Carte',
  categories: 'Catégories',
  services: 'Services',
  templates: 'Templates',
  statistiques: 'Statistiques',
  parametres: 'Paramètres',
}

const breadcrumbs = computed<BreadcrumbItem[]>(() => {
  const items: BreadcrumbItem[] = [{ label: 'Accueil', path: '/' }]

  const name = route.name as string
  if (!name || name === 'dashboard') return items

  // Parent route (si c'est un détail)
  if (name === 'demande-detail') {
    items.push({ label: 'Demandes', path: '/demandes' })
    items.push({ label: route.params.id ? `#${String(route.params.id).slice(0, 8)}` : 'Détail' })
    return items
  }

  items.push({ label: routeLabels[name] || name })
  return items
})
</script>

<template>
  <nav class="breadcrumbs" v-if="breadcrumbs.length > 1" aria-label="Fil d'Ariane">
    <template v-for="(item, i) in breadcrumbs" :key="i">
      <router-link v-if="item.path && i < breadcrumbs.length - 1" :to="item.path" class="breadcrumb-link">
        {{ item.label }}
      </router-link>
      <span v-else class="breadcrumb-current">{{ item.label }}</span>
      <span v-if="i < breadcrumbs.length - 1" class="breadcrumb-sep">/</span>
    </template>
  </nav>
</template>

<style scoped>
.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  padding: 0.75rem 1.5rem 0;
  color: #9ca3af;
}

.breadcrumb-link {
  color: #6b7280;
  text-decoration: none;
  transition: color 0.15s;
}

.breadcrumb-link:hover {
  color: #3b82f6;
}

.breadcrumb-current {
  color: #374151;
  font-weight: 500;
}

.breadcrumb-sep {
  color: #d1d5db;
}
</style>

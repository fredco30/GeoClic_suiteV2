/**
 * router/index.ts
 *
 * GéoClic Data - Configuration du routeur avec guards d'authentification
 */

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// Définition manuelle des routes (plus de contrôle sur la navigation)
const routes: RouteRecordRaw[] = [
  // Login (public)
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/login.vue'),
    meta: { public: true, layout: 'default' },
  },

  // Dashboard
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/pages/index.vue'),
    meta: { title: 'Tableau de bord', layout: 'admin' },
  },

  // Lexique
  {
    path: '/lexique',
    name: 'lexique',
    component: () => import('@/pages/lexique.vue'),
    meta: { title: 'Gestion du Lexique', layout: 'admin' },
  },

  // Champs dynamiques
  {
    path: '/champs',
    name: 'champs',
    component: () => import('@/pages/lexique.vue'),
    meta: { title: 'Champs dynamiques', layout: 'admin' },
  },

  // Points
  {
    path: '/points',
    name: 'points',
    component: () => import('@/pages/points.vue'),
    meta: { title: 'Gestion des Points', layout: 'admin' },
  },

  // Carte
  {
    path: '/carte',
    name: 'carte',
    component: () => import('@/pages/carte.vue'),
    meta: { title: 'Cartographie', layout: 'admin' },
  },

  // Utilisateurs (admin only)
  {
    path: '/utilisateurs',
    name: 'utilisateurs',
    component: () => import('@/pages/utilisateurs.vue'),
    meta: { title: 'Gestion des Utilisateurs', requiresAdmin: true, layout: 'admin' },
  },

  // QR Codes
  {
    path: '/qrcodes',
    name: 'qrcodes',
    component: () => import('@/pages/qrcodes.vue'),
    meta: { title: 'Génération QR Codes', layout: 'admin' },
  },

  // Projets - Liste
  {
    path: '/projets',
    name: 'projets',
    component: () => import('@/pages/projets/index.vue'),
    meta: { title: 'Gestion des Projets', layout: 'admin' },
  },

  // Projets - Vue unifiée (détail)
  {
    path: '/projets/:id',
    name: 'projet-detail',
    component: () => import('@/pages/projets/[id].vue'),
    meta: { title: 'Configuration du Projet', layout: 'admin' },
  },

  // Exports
  {
    path: '/exports',
    name: 'exports',
    component: () => import('@/pages/exports.vue'),
    meta: { title: 'Exports', layout: 'admin' },
  },

  // OneGeo Suite (OGS)
  {
    path: '/ogs',
    name: 'ogs',
    component: () => import('@/pages/ogs.vue'),
    meta: { title: 'OneGeo Suite', layout: 'admin' },
  },

  // Imports
  {
    path: '/imports',
    name: 'imports',
    component: () => import('@/pages/imports.vue'),
    meta: { title: 'Imports', layout: 'admin' },
  },

  // Zones - Liste
  {
    path: '/zones',
    name: 'zones',
    component: () => import('@/pages/zones/index.vue'),
    meta: { title: 'Gestion des Zones', layout: 'admin' },
  },

  // Zones - Création/Édition
  {
    path: '/zones/nouvelle',
    name: 'zone-nouvelle',
    component: () => import('@/pages/zones/edit.vue'),
    meta: { title: 'Nouvelle Zone', layout: 'admin' },
  },

  // Zones - Édition
  {
    path: '/zones/:id/edit',
    name: 'zone-edit',
    component: () => import('@/pages/zones/edit.vue'),
    meta: { title: 'Modifier la Zone', layout: 'admin' },
  },

  // Profil
  {
    path: '/profil',
    name: 'profil',
    component: () => import('@/pages/profil.vue'),
    meta: { title: 'Mon Profil', layout: 'admin' },
  },

  // Paramètres
  {
    path: '/parametres',
    name: 'parametres',
    component: () => import('@/pages/parametres.vue'),
    meta: { title: 'Paramètres', layout: 'admin' },
  },

  // Point detail (public URL for QR codes)
  {
    path: '/point/:id',
    name: 'point-detail',
    component: () => import('@/pages/point-detail.vue'),
    meta: { public: true, layout: 'default' },
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  // Import auth store dynamically to avoid circular dependency
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()

  // Restore session on app start
  if (!authStore.user && localStorage.getItem('data_auth_token')) {
    authStore.restoreSession()
  }

  // Public routes
  if (to.meta.public) {
    // Redirect to dashboard if already authenticated and going to login
    if (to.path === '/login' && authStore.isAuthenticated) {
      return next('/')
    }
    return next()
  }

  // Protected routes - check authentication
  if (!authStore.isAuthenticated) {
    return next({
      path: '/login',
      query: { redirect: to.fullPath },
    })
  }

  // Admin-only routes
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return next('/')
  }

  next()
})

// Update page title
router.afterEach((to) => {
  const title = to.meta.title as string
  document.title = title ? `${title} - GéoClic Data` : 'GéoClic Data'
})

// Workaround for dynamic import errors
router.onError((err, to) => {
  if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
    if (localStorage.getItem('vuetify:dynamic-reload')) {
      console.error('Dynamic import error, reloading page did not fix it', err)
    } else {
      console.log('Reloading page to fix dynamic import error')
      localStorage.setItem('vuetify:dynamic-reload', 'true')
      location.assign(to.fullPath)
    }
  } else {
    console.error(err)
  }
})

router.isReady().then(() => {
  localStorage.removeItem('vuetify:dynamic-reload')
})

export default router

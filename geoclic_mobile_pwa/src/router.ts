import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./views/LoginView.vue'),
    meta: { requiresAuth: false, showNav: false }
  },
  {
    path: '/',
    name: 'home',
    component: () => import('./views/HomeView.vue'),
    meta: { requiresAuth: true, showNav: true }
  },
  {
    path: '/points',
    name: 'points',
    component: () => import('./views/PointsView.vue'),
    meta: { requiresAuth: true, showNav: true }
  },
  {
    path: '/point/new',
    name: 'point-new',
    component: () => import('./views/PointFormView.vue'),
    meta: { requiresAuth: true, showNav: false }
  },
  {
    path: '/point/:id',
    name: 'point-detail',
    component: () => import('./views/PointFormView.vue'),
    meta: { requiresAuth: true, showNav: false }
  },
  {
    path: '/geometry/new',
    name: 'geometry-new',
    component: () => import('./views/GeometryFormView.vue'),
    meta: { requiresAuth: true, showNav: false }
  },
  {
    path: '/geometry/:id',
    name: 'geometry-detail',
    component: () => import('./views/GeometryFormView.vue'),
    meta: { requiresAuth: true, showNav: false }
  },
  {
    path: '/map',
    name: 'map',
    component: () => import('./views/MapView.vue'),
    meta: { requiresAuth: true, showNav: true }
  },
  {
    path: '/sync',
    name: 'sync',
    component: () => import('./views/SyncView.vue'),
    meta: { requiresAuth: true, showNav: true }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('./views/SettingsView.vue'),
    meta: { requiresAuth: true, showNav: false }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory('/mobile/'),
  routes
})

// Guard de navigation
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router

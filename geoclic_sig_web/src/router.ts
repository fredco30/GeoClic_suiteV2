import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory('/sig/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue')
    },
    {
      path: '/',
      name: 'map',
      component: () => import('./views/MapView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('./views/ProjectsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/import',
      name: 'import',
      component: () => import('./views/ImportView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    const isValid = await authStore.checkAuth()
    if (!isValid) {
      next({ name: 'login' })
      return
    }
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'map' })
    return
  }

  next()
})

export default router

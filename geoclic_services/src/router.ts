import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory('/services/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('./views/DashboardView.vue')
    },
    {
      path: '/demandes',
      name: 'demandes',
      component: () => import('./views/DemandesListView.vue')
    },
    {
      path: '/demandes/:id',
      name: 'demande-detail',
      component: () => import('./views/DemandeDetailView.vue')
    },
    {
      path: '/agents',
      name: 'agents',
      component: () => import('./views/AgentsView.vue'),
      meta: { requiresResponsable: true }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard'
    }
  ]
})

// Navigation guard
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Initialiser le store si nécessaire
  if (!authStore.initialized) {
    await authStore.initialize()
  }

  // Route publique (login)
  if (to.meta.public) {
    if (authStore.isLoggedIn) {
      return next('/dashboard')
    }
    return next()
  }

  // Vérifier l'authentification
  if (!authStore.isLoggedIn) {
    return next('/login')
  }

  // Vérifier le rôle responsable
  if (to.meta.requiresResponsable && authStore.agent?.role !== 'responsable') {
    return next('/dashboard')
  }

  next()
})

export default router

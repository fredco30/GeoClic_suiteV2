import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory('/terrain/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      redirect: '/demandes'
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
      path: '/:pathMatch(.*)*',
      redirect: '/demandes'
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
      return next('/demandes')
    }
    return next()
  }

  // Vérifier l'authentification
  if (!authStore.isLoggedIn) {
    return next('/login')
  }

  next()
})

export default router

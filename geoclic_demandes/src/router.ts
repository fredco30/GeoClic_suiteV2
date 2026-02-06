import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory('/demandes/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('./views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/demandes',
      name: 'demandes',
      component: () => import('./views/DemandesListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/demandes/creer',
      name: 'creer-demande',
      component: () => import('./views/CreerDemandeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/demandes/:id',
      name: 'demande-detail',
      component: () => import('./views/DemandeDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/demandes/:id/modifier',
      name: 'modifier-demande',
      component: () => import('./views/ModifierDemandeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/carte',
      name: 'carte',
      component: () => import('./views/CarteView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/categories',
      name: 'categories',
      component: () => import('./views/CategoriesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/services',
      name: 'services',
      component: () => import('./views/ServicesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/templates',
      name: 'templates',
      component: () => import('./views/TemplatesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/statistiques',
      name: 'statistiques',
      component: () => import('./views/StatistiquesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/parametres',
      name: 'parametres',
      component: () => import('./views/ParametresView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.guest && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router

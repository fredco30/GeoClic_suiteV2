import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/fleet/'),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('./views/DashboardView.vue'),
    },
    {
      path: '/add',
      name: 'add-server',
      component: () => import('./views/AddServerView.vue'),
    },
    {
      path: '/server/:name',
      name: 'server-detail',
      component: () => import('./views/ServerDetailView.vue'),
      props: true,
    },
    {
      path: '/help',
      name: 'help',
      component: () => import('./views/HelpView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('fleet_auth_token')
  if (!token && to.name !== 'login') {
    return { name: 'login' }
  }
})

export default router

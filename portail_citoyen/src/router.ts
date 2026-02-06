import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/portail/'),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('./views/HomeView.vue'),
    },
    {
      path: '/signaler',
      name: 'signaler',
      component: () => import('./views/SignalerView.vue'),
    },
    {
      path: '/signaler/qr/:equipementId',
      name: 'signaler-qr',
      component: () => import('./views/SignalerQRView.vue'),
    },
    {
      path: '/suivi',
      name: 'suivi',
      component: () => import('./views/SuiviView.vue'),
    },
    {
      path: '/suivi/:numeroSuivi',
      name: 'suivi-detail',
      component: () => import('./views/SuiviDetailView.vue'),
    },
    {
      path: '/carte',
      name: 'carte',
      component: () => import('./views/CarteView.vue'),
    },
    {
      path: '/faq',
      name: 'faq',
      component: () => import('./views/FaqView.vue'),
    },
  ],
})

export default router

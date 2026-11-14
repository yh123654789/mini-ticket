import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from './api/session'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/tickets' },
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/tickets',
      name: 'tickets',
      component: () => import('./views/TicketsView.vue'),
    },
    {
      path: '/tickets/:id',
      name: 'ticket-detail',
      component: () => import('./views/TicketDetailView.vue'),
      props: true,
    },
    { path: '/:pathMatch(.*)*', redirect: '/tickets' },
  ],
})

// 未登录一律踢回登录页，前端只做体验层拦截，真正的权限在后端
router.beforeEach((to) => {
  const loggedIn = Boolean(getToken())
  if (!to.meta.public && !loggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && loggedIn) {
    return { name: 'tickets' }
  }
  return true
})

export default router

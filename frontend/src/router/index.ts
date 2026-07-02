import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'boards',
      component: () => import('@/views/BoardListView.vue'),
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/SearchView.vue'),
    },
    {
      path: '/mod/login',
      name: 'mod-login',
      component: () => import('@/views/mod/ModLoginView.vue'),
    },
    {
      path: '/mod',
      name: 'mod-dashboard',
      component: () => import('@/views/mod/ModDashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/:slug',
      name: 'catalog',
      component: () => import('@/views/CatalogView.vue'),
    },
    {
      path: '/:slug/new',
      name: 'create-thread',
      component: () => import('@/views/CreateThreadView.vue'),
    },
    {
      path: '/:slug/thread/:id',
      name: 'thread',
      component: () => import('@/views/ThreadView.vue'),
    },
  ],
})

// redirect unauthenticated visitors away from routes flagged requiresAuth
export function authGuard(to: RouteLocationNormalized) {
  if (to.meta.requiresAuth && !useAuthStore().isAuthenticated) {
    return { name: 'mod-login' as const }
  }
  return true
}

router.beforeEach(authGuard)

export default router

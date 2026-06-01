import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'boards',
      component: () => import('@/views/BoardListView.vue'),
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

export default router

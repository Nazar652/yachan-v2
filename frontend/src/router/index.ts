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
  ],
})

export default router

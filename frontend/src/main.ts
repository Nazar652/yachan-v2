import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import App from './App.vue'
import router from './router'
import { initSentry } from './sentry'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

const app = createApp(App)

initSentry(app, router)

app.use(createPinia())
app.use(VueQueryPlugin, { queryClient })
app.use(router)

app.mount('#app')

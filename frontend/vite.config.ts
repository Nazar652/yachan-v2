import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

// dev server proxies /api (+ws) and /media to the running stack. on the host this
// is the docker nginx (default); inside the dockerized dev container it is the
// nginx service. only affects `npm run dev`, never the production build.
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    vueDevTools(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: true,
    proxy: {
      '/api': { target: proxyTarget, changeOrigin: true, ws: true },
      '/media': { target: proxyTarget, changeOrigin: true },
    },
    ...(env.VITE_USE_POLLING ? { watch: { usePolling: true } } : {}),
})

<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <div class="grain-layer" aria-hidden="true" />
    <AppHeader />
    <main class="relative z-10 mx-auto w-full max-w-5xl flex-1 px-4 py-4">
      <RouterView />
    </main>
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
</script>

<template>
  <AppHeader />
  <main class="mx-auto max-w-5xl px-4 py-4">
    <RouterView />
  </main>
</template>

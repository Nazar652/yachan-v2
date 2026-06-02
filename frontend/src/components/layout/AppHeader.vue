<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <header class="border-b border-border bg-surface">
    <div class="mx-auto flex max-w-5xl items-center px-4 py-2">
      <RouterLink to="/" class="text-lg font-bold text-accent">yachan</RouterLink>
      <RouterLink
        :to="auth.isAuthenticated ? '/mod' : '/mod/login'"
        class="ml-auto text-sm text-accent hover:underline"
      >
        {{ auth.isAuthenticated ? 'Mod panel' : 'Mod login' }}
      </RouterLink>
    </div>
  </header>
</template>

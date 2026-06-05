<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBoards } from '@/composables/useBoards'

const auth = useAuthStore()
const route = useRoute()
const { data: boards } = useBoards()

// show board tabs only on board / thread pages, not on home or mod pages
const isOnBoardPage = computed(
  () =>
    route.name === 'catalog' ||
    route.name === 'thread' ||
    route.name === 'create-thread',
)
</script>

<template>
  <header class="border-b border-border bg-surface">
    <div class="mx-auto flex max-w-5xl items-center gap-3 px-4 py-2">
      <RouterLink to="/" class="text-lg font-bold text-accent shrink-0">yachan</RouterLink>

      <!-- board tabs — visible on board / thread pages -->
      <nav v-if="isOnBoardPage && boards?.length" class="flex flex-wrap gap-1 min-w-0">
        <RouterLink
          v-for="board in boards"
          :key="board.slug"
          :to="`/${board.slug}`"
          class="rounded px-2 py-0.5 text-sm font-mono transition-colors"
          :class="
            route.params.slug === board.slug
              ? 'bg-accent text-surface font-semibold'
              : 'text-accent hover:bg-surface-2'
          "
        >
          /{{ board.slug }}/
        </RouterLink>
      </nav>

      <RouterLink
        :to="auth.isAuthenticated ? '/mod' : '/mod/login'"
        class="ml-auto shrink-0 text-sm text-accent hover:underline"
      >
        {{ auth.isAuthenticated ? 'Mod panel' : 'Mod login' }}
      </RouterLink>
    </div>
  </header>
</template>

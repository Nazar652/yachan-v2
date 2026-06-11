<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBoards } from '@/composables/useBoards'
import { useTheme } from '@/composables/useTheme'
import BarleyEar from '@/components/brand/BarleyEar.vue'

const auth = useAuthStore()
const route = useRoute()
const { data: boards } = useBoards()
const { theme, toggle } = useTheme()

// show board tabs only on board / thread pages, not on home or mod pages
const isOnBoardPage = computed(
  () =>
    route.name === 'catalog' ||
    route.name === 'thread' ||
    route.name === 'create-thread',
)
</script>

<template>
  <header class="sticky top-0 z-30 border-b border-border bg-surface/90 shadow-card backdrop-blur-md">
    <div class="mx-auto flex h-[58px] max-w-5xl items-center gap-4 px-4">
      <RouterLink to="/" class="flex shrink-0 cursor-pointer items-center gap-2">
        <BarleyEar :height="34" />
        <span class="font-display text-[21px] font-extrabold tracking-tight text-text">
          я<b class="text-gold-2">чан</b>
        </span>
      </RouterLink>

      <!-- board tabs — visible on board / thread pages -->
      <nav v-if="isOnBoardPage && boards?.length" class="flex min-w-0 flex-wrap gap-1">
        <RouterLink
          v-for="board in boards"
          :key="board.slug"
          :to="`/${board.slug}`"
          class="whitespace-nowrap rounded-field px-2 py-1 font-mono text-[13px] transition-colors"
          :class="
            route.params.slug === board.slug
              ? 'bg-gold font-bold text-on-gold shadow-card'
              : 'text-accent hover:bg-surface-3'
          "
        >
          /{{ board.slug }}/
        </RouterLink>
      </nav>

      <div class="ml-auto flex shrink-0 items-center gap-2">
        <button
          type="button"
          class="grid h-[34px] w-[34px] cursor-pointer place-items-center rounded-field border border-border bg-surface text-text transition-colors hover:border-gold hover:bg-surface-3"
          :title="theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'"
          aria-label="Toggle theme"
          @click="toggle"
        >
          <svg
            v-if="theme === 'dark'"
            viewBox="0 0 24 24"
            class="h-[17px] w-[17px]"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
          </svg>
          <svg
            v-else
            viewBox="0 0 24 24"
            class="h-[17px] w-[17px]"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
          </svg>
        </button>

        <RouterLink
          :to="auth.isAuthenticated ? '/mod' : '/mod/login'"
          class="text-sm font-semibold text-accent transition-colors hover:text-accent-hover"
        >
          {{ auth.isAuthenticated ? 'Mod panel' : 'Mod login' }}
        </RouterLink>
      </div>
    </div>
  </header>
</template>

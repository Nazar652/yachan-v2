<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBoards } from '@/composables/useBoards'
import { useTheme } from '@/composables/useTheme'
import BarleyEar from '@/components/brand/BarleyEar.vue'
import MonogramSeal from '@/components/brand/MonogramSeal.vue'
import WatcherDropdown from '@/components/layout/WatcherDropdown.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const { data: boards } = useBoards()
const { theme, toggle } = useTheme()

const searchTerm = ref(typeof route.query.q === 'string' ? route.query.q : '')

function onSearch() {
  const trimmed = searchTerm.value.trim()
  if (trimmed) router.push({ name: 'search', query: { q: trimmed } })
}

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
    <div
      class="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2 sm:h-[58px] sm:flex-nowrap sm:py-0"
    >
      <RouterLink to="/" class="flex shrink-0 cursor-pointer items-center gap-2">
        <BarleyEar :height="34" />
        <span class="font-display text-[21px] font-extrabold tracking-tight text-text">
          я<b class="text-gold-2">чан</b>
        </span>
      </RouterLink>

      <!-- board tabs — visible on board / thread pages; wraps to its own row on mobile -->
      <nav
        v-if="isOnBoardPage && boards?.length"
        class="order-last flex w-full flex-nowrap gap-1 overflow-x-auto sm:order-none sm:w-auto sm:min-w-0 sm:flex-1"
      >
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

      <form class="ml-auto flex shrink-0 items-center" @submit.prevent="onSearch">
        <input
          v-model="searchTerm"
          type="search"
          placeholder="Search…"
          aria-label="Search posts"
          class="h-[34px] w-32 rounded-field border border-border bg-surface px-3 text-sm text-text outline-none transition-colors placeholder:text-text-muted focus:w-44 focus:border-gold focus:ring-[3px] focus:ring-gold/25 sm:w-40 sm:focus:w-56"
        />
      </form>

      <div class="flex shrink-0 items-center gap-2">
        <WatcherDropdown />

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
          class="grid h-[34px] w-[34px] cursor-pointer place-items-center transition-opacity hover:opacity-80"
          :title="auth.isAuthenticated ? 'Mod panel' : 'Mod login'"
          :aria-label="auth.isAuthenticated ? 'Mod panel' : 'Mod login'"
        >
          <MonogramSeal :size="30" bg="var(--color-surface)" />
        </RouterLink>
      </div>
    </div>
  </header>
</template>

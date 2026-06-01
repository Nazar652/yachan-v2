<script setup lang="ts">
import { useBoards } from '@/composables/useBoards'

const { data: boards, isPending, isError } = useBoards()
</script>

<template>
  <section>
    <h1 class="text-xl font-bold">Boards</h1>

    <p v-if="isPending" class="mt-2 text-text-muted">Loading…</p>
    <p v-else-if="isError" class="mt-2 text-danger">Failed to load boards.</p>
    <p v-else-if="!boards?.length" class="mt-2 text-text-muted">No boards yet.</p>

    <ul v-else class="mt-4 space-y-2">
      <li v-for="board in boards" :key="board.id">
        <RouterLink
          :to="`/${board.slug}`"
          class="block rounded-card border border-border bg-surface p-4 transition-colors hover:border-accent"
        >
          <div class="flex items-baseline gap-2">
            <span class="font-mono text-accent">/{{ board.slug }}/</span>
            <span class="font-medium">{{ board.title }}</span>
          </div>
          <p v-if="board.description" class="mt-1 text-sm text-text-muted">
            {{ board.description }}
          </p>
        </RouterLink>
      </li>
    </ul>
  </section>
</template>

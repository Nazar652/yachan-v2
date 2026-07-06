<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { useWatcherStatus } from '@/composables/useWatcherStatus'

const { watchedStatuses, totalUnread, remove } = useWatcherStatus()

const isOpen = ref(false)
const root = ref<HTMLElement | null>(null)

function toggleOpen() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}

function onDocumentClick(event: MouseEvent) {
  if (root.value && !root.value.contains(event.target as Node)) close()
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onUnmounted(() => document.removeEventListener('click', onDocumentClick))
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="relative grid h-[34px] w-[34px] cursor-pointer place-items-center rounded-field border border-border bg-surface text-text transition-colors hover:border-gold hover:bg-surface-3"
      aria-label="Watched threads"
      @click="toggleOpen"
    >
      ★
      <span
        v-if="totalUnread > 0"
        class="absolute -right-1.5 -top-1.5 rounded-full bg-danger px-1 font-mono text-[10px] font-semibold leading-[16px] text-white"
      >
        {{ totalUnread }}
      </span>
    </button>

    <div
      v-if="isOpen"
      class="absolute right-0 top-[calc(100%+6px)] z-40 w-72 rounded-card border border-border bg-surface shadow-card"
    >
      <p v-if="watchedStatuses.length === 0" class="p-3 text-sm italic text-text-muted">
        No watched threads yet.
      </p>

      <div
        v-for="status in watchedStatuses"
        :key="status.threadId"
        class="flex items-center gap-2 border-b border-border-soft px-3 py-2 last:border-b-0"
      >
        <RouterLink
          :to="`/${status.slug}/thread/${status.threadId}`"
          class="min-w-0 flex-1"
          @click="close"
        >
          <div class="truncate text-sm text-text">{{ status.title ?? '(no title)' }}</div>
          <div class="font-mono text-xs text-text-muted">/{{ status.slug }}/</div>
        </RouterLink>

        <span
          v-if="status.dead"
          class="rounded-full bg-danger/15 px-2 py-0.5 font-mono text-[10.5px] font-semibold uppercase tracking-wide text-danger"
        >
          deleted
        </span>
        <span
          v-else-if="status.unread > 0"
          class="rounded-full bg-gold/25 px-2 py-0.5 font-mono text-[10.5px] font-semibold text-accent"
        >
          {{ status.unread }}
        </span>

        <button
          type="button"
          class="shrink-0 text-text-muted transition-colors hover:text-danger"
          aria-label="Stop watching"
          @click="remove(status.threadId)"
        >
          ✕
        </button>
      </div>
    </div>
  </div>
</template>

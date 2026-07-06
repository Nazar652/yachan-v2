<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { SimilarThreadResponse } from '@/api/types'

defineProps<{ items: SimilarThreadResponse[] }>()
</script>

<template>
  <details
    v-if="items.length"
    class="mb-4 rounded-card border border-border bg-surface p-3.5 shadow-card"
  >
    <summary class="cursor-pointer select-none font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-accent">
      Similar threads
    </summary>
    <ul class="mt-2 flex flex-col gap-1.5">
      <li v-for="item in items" :key="`${item.board_slug}-${item.thread_id}`">
        <RouterLink
          :to="`/${item.board_slug}/thread/${item.thread_id}`"
          class="flex items-center gap-2 rounded-field px-2 py-1.5 text-[13px] transition-colors hover:bg-surface-2"
        >
          <span class="shrink-0 rounded-full bg-gold px-2 py-0.5 font-mono text-[10.5px] font-semibold text-on-gold">
            /{{ item.board_slug }}/
          </span>
          <img
            v-if="item.thumbnail_url"
            :src="item.thumbnail_url"
            alt=""
            class="h-8 w-8 shrink-0 rounded-field border border-border object-cover"
          />
          <span class="truncate">{{ item.title ?? item.op_snippet ?? '(no title)' }}</span>
          <span class="ml-auto shrink-0 font-mono text-xs text-text-muted">{{ item.reply_count }} replies</span>
        </RouterLink>
      </li>
    </ul>
  </details>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useThreads } from '@/composables/useThreads'
import { useBoardWs } from '@/composables/useBoardWs'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseCard from '@/components/ui/BaseCard.vue'

const route = useRoute()
const slug = computed(() => route.params.slug as string)

const { data: threads, isPending, isError } = useThreads(slug)

// stream live new_thread events into the catalog cache
useBoardWs(slug)
</script>

<template>
  <section>
    <div class="flex items-center justify-between gap-4 mb-4">
      <h1 class="text-xl font-bold">
        <span class="font-mono text-accent">/{{ slug }}/</span>
      </h1>
      <RouterLink :to="`/${slug}/new`">
        <BaseButton variant="primary" size="sm">+ New thread</BaseButton>
      </RouterLink>
    </div>

    <p v-if="isPending" class="mt-2 text-text-muted">Loading…</p>
    <p v-else-if="isError" class="mt-2 text-danger">Failed to load threads.</p>
    <p v-else-if="!threads?.length" class="mt-4 text-text-muted">No threads yet.</p>

    <ul v-else class="mt-4 space-y-3">
      <li v-for="thread in threads" :key="thread.id">
        <RouterLink :to="`/${slug}/thread/${thread.id}`" class="block">
          <BaseCard :interactive="true">
            <div class="flex items-start justify-between gap-2">
              <div class="flex items-center gap-2">
                <span v-if="thread.is_sticky" title="Sticky" class="text-accent">📌</span>
                <span v-if="thread.is_locked" title="Locked" class="text-text-muted">🔒</span>
                <span class="font-medium">
                  {{ thread.title ?? '(no title)' }}
                </span>
              </div>
              <span class="shrink-0 text-sm text-text-muted">
                {{ thread.reply_count }} {{ thread.reply_count === 1 ? 'reply' : 'replies' }}
              </span>
            </div>
          </BaseCard>
        </RouterLink>
      </li>
    </ul>
  </section>
</template>


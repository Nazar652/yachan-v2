<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

import { useBoards } from '@/composables/useBoards'
import { useThreads } from '@/composables/useThreads'
import { useBoardWs } from '@/composables/useBoardWs'
import { useCatalogModeration } from '@/composables/useCatalogModeration'
import { useAuthStore } from '@/stores/auth'
import BaseButton from '@/components/ui/BaseButton.vue'
import type { ReplyPreview, ThreadResponse } from '@/api/types'

const route = useRoute()
const slug = computed(() => route.params.slug as string)

const { data: boards } = useBoards()
const { data: threads, isPending, isError } = useThreads(slug)

useBoardWs(slug)

const auth = useAuthStore()
const moderation = useCatalogModeration(slug)

const board = computed(() => boards.value?.find((b) => b.slug === slug.value))

async function onToggleLock(thread: ThreadResponse) {
  await moderation.setLocked(thread.id, !thread.is_locked)
}

async function onToggleSticky(thread: ThreadResponse) {
  await moderation.setSticky(thread.id, !thread.is_sticky)
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

function bodyPreview(body: string | null | undefined, maxLen = 120): string {
  if (!body) return ''
  return body.length > maxLen ? body.slice(0, maxLen) + '…' : body
}

function replyPreview(body: string | null | undefined, maxLen = 80): string {
  if (!body) return ''
  return body.length > maxLen ? body.slice(0, maxLen) + '…' : body
}

function formatReplyDate(reply: ReplyPreview): string {
  return new Date(reply.created_at).toLocaleString()
}
</script>

<template>
  <section>
    <!-- board header -->
    <div class="mb-4 rounded-card border border-border bg-surface p-4">
      <h1 class="text-xl font-bold text-accent">/{{ slug }}/</h1>
      <p v-if="board?.description" class="mt-1 text-sm text-text-muted">
        {{ board.description }}
      </p>
    </div>

    <!-- new thread form -->
    <div class="mb-6 flex justify-end">
      <RouterLink :to="`/${slug}/new`">
        <BaseButton variant="primary" size="sm">+ New thread</BaseButton>
      </RouterLink>
    </div>

    <p v-if="isPending" class="mt-2 text-text-muted">Loading…</p>
    <p v-else-if="isError" class="mt-2 text-danger">Failed to load threads.</p>
    <p v-else-if="!threads?.length" class="mt-4 text-text-muted">No threads yet.</p>

    <ul v-else class="space-y-4">
      <li v-for="thread in threads" :key="thread.id">
        <div class="rounded-card border border-border bg-surface overflow-hidden">
          <RouterLink :to="`/${slug}/thread/${thread.id}`" class="block hover:bg-surface-2 transition-colors">
            <div class="flex gap-4 p-3">
              <!-- thumbnail -->
              <div class="shrink-0">
                <img
                  v-if="thread.op_post?.thumbnail_url"
                  :src="thread.op_post.thumbnail_url"
                  alt=""
                  class="h-24 w-24 object-cover rounded border border-border"
                />
                <div
                  v-else
                  class="h-24 w-24 rounded border border-border bg-surface-2 flex items-center justify-center text-text-muted text-xs"
                >
                  no img
                </div>
              </div>

              <!-- thread info -->
              <div class="min-w-0 flex-1">
                <div class="flex items-start gap-2 mb-1">
                  <span v-if="thread.is_sticky" title="Sticky">📌</span>
                  <span v-if="thread.is_locked" title="Locked">🔒</span>
                  <span class="font-semibold text-accent truncate">
                    {{ thread.title ?? '(no title)' }}
                  </span>
                  <span class="ml-auto shrink-0 text-xs text-text-muted">
                    {{ formatDate(thread.created_at) }}
                  </span>
                </div>
                <p class="text-sm text-text-muted line-clamp-2">
                  {{ bodyPreview(thread.op_post?.body) }}
                </p>
              </div>

              <!-- replies count -->
              <div class="shrink-0 self-start text-right">
                <span class="text-sm text-text-muted">
                  {{ thread.reply_count }}
                  {{ thread.reply_count === 1 ? 'reply' : 'replies' }}
                </span>
              </div>
            </div>
          </RouterLink>

          <!-- latest replies -->
          <div class="border-t border-border px-3 py-2">
            <p class="mb-1 text-xs font-semibold text-text-muted">Latest posts:</p>
            <p
              v-if="!thread.last_replies?.length"
              class="text-xs text-text-muted italic"
            >
              Nobody posted anything yet
            </p>
            <ul v-else class="space-y-0.5">
              <li
                v-for="reply in thread.last_replies"
                :key="reply.id"
                class="flex items-baseline gap-2 text-xs text-text-muted"
              >
                <span class="shrink-0 font-mono">№{{ reply.id }}</span>
                <span class="min-w-0 flex-1 truncate">{{ replyPreview(reply.body) }}</span>
                <span class="shrink-0">{{ formatReplyDate(reply) }}</span>
              </li>
            </ul>
          </div>

          <!-- mod controls outside the link -->
          <div v-if="auth.isAuthenticated" class="flex gap-2 border-t border-border px-3 py-1">
            <BaseButton variant="ghost" size="sm" @click="onToggleLock(thread)">
              {{ thread.is_locked ? 'Unlock' : 'Lock' }}
            </BaseButton>
            <BaseButton variant="ghost" size="sm" @click="onToggleSticky(thread)">
              {{ thread.is_sticky ? 'Unsticky' : 'Sticky' }}
            </BaseButton>
          </div>
        </div>
      </li>
    </ul>
  </section>
</template>

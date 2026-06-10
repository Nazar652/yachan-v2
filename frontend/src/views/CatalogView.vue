<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

import { useBoards } from '@/composables/useBoards'
import { useThreads } from '@/composables/useThreads'
import { useBoardWs } from '@/composables/useBoardWs'
import { useCatalogModeration } from '@/composables/useCatalogModeration'
import { useAuthStore } from '@/stores/auth'
import BaseButton from '@/components/ui/BaseButton.vue'
import PostBody from '@/components/ui/PostBody.vue'
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

function formatReplyDate(reply: ReplyPreview): string {
  return new Date(reply.created_at).toLocaleString()
}

// the default poster name carries no information, so only a custom name is shown
function replyName(name: string | null | undefined): string | null {
  return name && name !== 'Anonymous' ? name : null
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
          <!-- whole card navigates into the thread -->
          <RouterLink
            :to="`/${slug}/thread/${thread.id}`"
            class="grid gap-4 p-4 hover:bg-surface-2 transition-colors md:grid-cols-2"
          >
            <!-- op column -->
            <div class="flex min-w-0 flex-col gap-2">
              <div class="flex items-baseline gap-2 text-xs text-text-muted">
                <span v-if="thread.is_sticky" title="Sticky">📌</span>
                <span v-if="thread.is_locked" title="Locked">🔒</span>
                <span class="font-mono">ID: {{ thread.id }}</span>
                <span class="truncate font-semibold text-accent">{{ thread.title ?? '(no title)' }}</span>
                <span class="ml-auto shrink-0">
                  {{ thread.reply_count }} {{ thread.reply_count === 1 ? 'reply' : 'replies' }}
                </span>
              </div>

              <img
                v-if="thread.op_post?.thumbnail_url"
                :src="thread.op_post.thumbnail_url"
                alt=""
                loading="lazy"
                class="h-40 w-40 self-start rounded border border-border object-cover"
              />

              <PostBody
                v-if="thread.op_post?.body_html"
                :html="thread.op_post.body_html"
                class="max-h-40 overflow-hidden text-sm"
              />

              <span class="mt-auto text-xs text-text-muted">{{ formatDate(thread.created_at) }}</span>
            </div>

            <!-- latest posts column -->
            <div class="flex min-w-0 flex-col gap-2">
              <p class="text-xs font-semibold text-text-muted">Latest posts:</p>
              <p v-if="!thread.last_replies?.length" class="text-xs italic text-text-muted">
                Nobody posted anything yet
              </p>
              <ul v-else class="flex flex-col gap-2">
                <li
                  v-for="reply in thread.last_replies"
                  :key="reply.id"
                  class="rounded border border-border bg-bg/50 p-2"
                >
                  <div class="flex items-baseline gap-2 text-xs text-text-muted">
                    <span class="font-mono">ID: {{ reply.id }}</span>
                    <span v-if="replyName(reply.name)" class="font-semibold text-accent">
                      {{ replyName(reply.name) }}
                    </span>
                    <span class="ml-auto shrink-0">{{ formatReplyDate(reply) }}</span>
                  </div>
                  <PostBody
                    v-if="reply.body_html"
                    :html="reply.body_html"
                    class="mt-1 max-h-16 overflow-hidden text-sm"
                  />
                </li>
              </ul>
            </div>
          </RouterLink>

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

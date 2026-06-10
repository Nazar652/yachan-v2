<script setup lang="ts">
import { computed, ref, toRef } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useThread } from '@/composables/useThread'
import { useThreadWs } from '@/composables/useThreadWs'
import { useModeration } from '@/composables/useModeration'
import { useAuthStore } from '@/stores/auth'
import { extractPostRefs } from '@/utils/postRefs'
import ReplyForm from '@/components/ReplyForm.vue'
import PostArticle from '@/components/PostArticle.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const route = useRoute()
const slug = computed(() => route.params.slug as string)
const threadId = computed(() => Number(route.params.id))

const { data: thread, isPending, isError } = useThread(
  toRef(slug),
  toRef(threadId),
)

// stream live new_post / post_edited events into the thread cache
useThreadWs(slug, threadId)

const auth = useAuthStore()
const moderation = useModeration(slug, threadId)

// reverse map post_number -> numbers of posts that reference it, derived from the
// thread's posts so it stays in sync with live new_post / post_edited events
const backlinksByPostNumber = computed(() => {
  const map = new Map<number, number[]>()
  for (const post of thread.value?.posts ?? []) {
    for (const target of extractPostRefs(post.body_html)) {
      if (target === post.post_number) continue
      const sources = map.get(target) ?? []
      if (!sources.includes(post.post_number)) sources.push(post.post_number)
      map.set(target, sources)
    }
  }
  return map
})

const replyForm = ref<InstanceType<typeof ReplyForm> | null>(null)

function onQuote(postNumber: number) {
  replyForm.value?.quote(postNumber)
}

function onNavigate(postNumber: number) {
  const target = document.getElementById(`post-${postNumber}`)
  if (!target) return
  if (typeof target.scrollIntoView === 'function') {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  target.classList.add('post-highlight')
  window.setTimeout(() => target.classList.remove('post-highlight'), 1500)
}

async function onToggleLock() {
  if (thread.value) await moderation.setLocked(!thread.value.is_locked)
}

async function onToggleSticky() {
  if (thread.value) await moderation.setSticky(!thread.value.is_sticky)
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <div class="mb-4 text-sm text-secondary">
      <RouterLink :to="`/${slug}`" class="cursor-pointer hover:text-accent hover:underline">← /{{ slug }}/</RouterLink>
    </div>

    <div v-if="isPending" class="text-secondary py-8 text-center">Loading…</div>

    <div v-else-if="isError" class="text-red-500 py-8 text-center">
      Failed to load thread
    </div>

    <template v-else-if="thread">
      <div class="mb-4 flex items-center gap-2">
        <h1 class="text-xl font-semibold">
          {{ thread.title ?? '(no title)' }}
        </h1>
        <span v-if="thread.is_sticky" title="Sticky">📌</span>
        <span v-if="thread.is_locked" title="Locked">🔒</span>
        <span class="ml-auto text-sm text-secondary">{{ thread.reply_count }} replies</span>
      </div>

      <div v-if="auth.isAuthenticated" class="mb-4 flex gap-2">
        <BaseButton variant="ghost" size="sm" @click="onToggleLock">
          {{ thread.is_locked ? 'Unlock' : 'Lock' }}
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="onToggleSticky">
          {{ thread.is_sticky ? 'Unsticky' : 'Sticky' }}
        </BaseButton>
      </div>

      <div class="flex flex-col gap-6">
        <PostArticle
          v-for="post in thread.posts ?? []"
          :key="post.id"
          :post="post"
          :slug="slug"
          :thread-id="threadId"
          :backlinks="backlinksByPostNumber.get(post.post_number) ?? []"
          @quote="onQuote"
          @navigate="onNavigate"
        />
      </div>

      <div class="mt-6">
        <p v-if="thread.is_locked" class="text-sm text-secondary italic py-4 text-center">
          🔒 This thread is locked.
        </p>
        <ReplyForm v-else ref="replyForm" :slug="slug" :thread-id="threadId" />
      </div>
    </template>
  </div>
</template>

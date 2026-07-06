<script setup lang="ts">
import { computed, nextTick, ref, toRef, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useThread } from '@/composables/useThread'
import { useThreadWs } from '@/composables/useThreadWs'
import { useModeration } from '@/composables/useModeration'
import { useSimilarThreads } from '@/composables/useSimilarThreads'
import { useAuthStore } from '@/stores/auth'
import { errorDetail } from '@/api/errors'
import { extractPostRefs } from '@/utils/postRefs'
import ReplyForm from '@/components/ReplyForm.vue'
import PostArticle from '@/components/PostArticle.vue'
import RefPreviews from '@/components/RefPreviews.vue'
import SimilarThreadsPanel from '@/components/SimilarThreadsPanel.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import SealDivider from '@/components/ui/SealDivider.vue'

const route = useRoute()
const router = useRouter()
const slug = computed(() => route.params.slug as string)
const threadId = computed(() => Number(route.params.id))

const { data: thread, isPending, isError } = useThread(
  toRef(slug),
  toRef(threadId),
)

// if a mod deletes the thread while it is open, leave for the catalog instead
// of staying on a dead page
useThreadWs(slug, threadId, () => {
  void router.push(`/${slug.value}`)
})

const auth = useAuthStore()
const moderation = useModeration(slug, threadId)
const { data: similarThreads } = useSimilarThreads(toRef(slug), toRef(threadId))

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

function scrollToPost(postNumber: number, smooth: boolean): boolean {
  const target = document.getElementById(`post-${postNumber}`)
  if (!target) return false
  if (typeof target.scrollIntoView === 'function') {
    target.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'start' })
  }
  target.classList.add('post-highlight')
  window.setTimeout(() => target.classList.remove('post-highlight'), 1500)
  return true
}

function onNavigate(postNumber: number) {
  scrollToPost(postNumber, true)
}

// arriving from the catalog with a #post-N hash: jump to that post once the
// thread has loaded. the post may render a flush after the data lands, so retry
// across frames until the element exists instead of relying on a single tick
function scrollToHashPost() {
  const match = /^#post-(\d+)$/.exec(route.hash)
  if (!match) return
  const postNumber = Number(match[1])
  let attempts = 0
  const attempt = () => {
    if (scrollToPost(postNumber, false) || ++attempts > 20) return
    requestAnimationFrame(attempt)
  }
  attempt()
}

watch(
  thread,
  (loaded) => {
    if (loaded) nextTick(scrollToHashPost)
  },
  { immediate: true },
)

const modError = ref<string | null>(null)

async function onToggleLock() {
  if (!thread.value) return
  modError.value = null
  try {
    await moderation.setLocked(!thread.value.is_locked)
  } catch (error: unknown) {
    modError.value = errorDetail(error, 'Failed to update thread.')
  }
}

async function onToggleSticky() {
  if (!thread.value) return
  modError.value = null
  try {
    await moderation.setSticky(!thread.value.is_sticky)
  } catch (error: unknown) {
    modError.value = errorDetail(error, 'Failed to update thread.')
  }
}

async function onDeleteThread() {
  if (!window.confirm('Delete this thread and all its posts and files? This cannot be undone.')) {
    return
  }
  modError.value = null
  try {
    await moderation.removeThread()
    await router.push(`/${slug.value}`)
  } catch (error: unknown) {
    modError.value = errorDetail(error, 'Failed to delete thread.')
  }
}

const isGeneratingSummary = ref(false)

async function onGenerateSummary() {
  modError.value = null
  isGeneratingSummary.value = true
  try {
    await moderation.generateSummary()
  } catch (error: unknown) {
    modError.value = errorDetail(error, 'Failed to generate summary.')
  } finally {
    isGeneratingSummary.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[880px] py-4">
    <RouterLink
      :to="`/${slug}`"
      class="mb-1 inline-flex cursor-pointer items-center gap-1.5 rounded-field px-1.5 py-1 font-mono text-[13px] text-accent transition-all hover:gap-2.5 hover:bg-surface-3 hover:text-accent-hover"
    >
      ‹ /{{ slug }}/
    </RouterLink>

    <div v-if="isPending" class="py-8 text-center text-text-muted">Loading…</div>

    <div v-else-if="isError" class="py-8 text-center text-danger">
      Failed to load thread
    </div>

    <template v-else-if="thread">
      <div class="mb-3 flex flex-wrap items-baseline gap-3">
        <h1 class="text-3xl font-extrabold tracking-tight">
          {{ thread.title ?? '(no title)' }}
        </h1>
        <span
          v-if="thread.is_sticky"
          class="rounded-full bg-gold/25 px-2 py-0.5 font-mono text-[10.5px] font-semibold uppercase tracking-wide text-accent"
        >
          ★ sticky
        </span>
        <span
          v-if="thread.is_locked"
          class="rounded-full bg-danger/15 px-2 py-0.5 font-mono text-[10.5px] font-semibold uppercase tracking-wide text-danger"
        >
          ⊘ locked
        </span>
        <span class="ml-auto font-mono text-xs text-text-muted">{{ thread.reply_count }} replies</span>
      </div>

      <div v-if="auth.isAuthenticated" class="mb-4 flex gap-2">
        <BaseButton variant="ghost" size="sm" @click="onToggleLock">
          {{ thread.is_locked ? 'Unlock' : 'Lock' }}
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="onToggleSticky">
          {{ thread.is_sticky ? 'Unsticky' : 'Sticky' }}
        </BaseButton>
        <BaseButton
          v-if="auth.isAdmin"
          variant="ghost"
          size="sm"
          :disabled="isGeneratingSummary"
          @click="onGenerateSummary"
        >
          {{ isGeneratingSummary ? 'Generating…' : 'Generate AI summary' }}
        </BaseButton>
        <BaseButton
          v-if="auth.isAdmin"
          variant="ghost"
          size="sm"
          class="ml-auto text-danger"
          @click="onDeleteThread"
        >
          Delete thread
        </BaseButton>
      </div>

      <p v-if="modError" class="mb-4 text-sm text-danger">{{ modError }}</p>

      <details
        v-if="thread.summary"
        open
        class="mb-4 rounded-card border border-border bg-surface p-3.5 shadow-card"
      >
        <summary class="cursor-pointer select-none font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-accent">
          TL;DR
        </summary>
        <p class="mt-2 whitespace-pre-wrap text-[13.5px] leading-relaxed text-text">
          {{ thread.summary }}
        </p>
      </details>

      <SimilarThreadsPanel :items="similarThreads ?? []" />

      <div class="flex flex-col gap-2.5">
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

      <RefPreviews :posts="thread.posts ?? []" :slug="slug" @navigate="onNavigate" />

      <SealDivider />

      <p v-if="thread.is_locked" class="py-4 text-center text-sm italic text-text-muted">
        ⊘ This thread is locked.
      </p>
      <ReplyForm v-else ref="replyForm" :slug="slug" :thread-id="threadId" />
    </template>
  </div>
</template>

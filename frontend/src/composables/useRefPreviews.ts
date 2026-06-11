import { onScopeDispose, ref } from 'vue'

import type { PostResponse } from '@/api/types'

export interface RefPreview {
  postNumber: number
  level: number
  post: PostResponse
  top: number
  left: number
}

// how long a preview lingers after the pointer leaves a ref or card, giving the
// pointer time to travel into the card (or a deeper ref) before it closes
const CLOSE_DELAY = 500
const PREVIEW_MAX_WIDTH = 480

// hover-preview stack for >>N references. a single document-level delegation
// catches refs both in the thread posts and inside previews themselves, so
// hovering a ref within a preview stacks another one on top (the level grows
// with the nesting depth). getPost looks a post up by number — returning
// undefined (e.g. a ref to another thread) simply shows nothing.
export function useRefPreviews(getPost: (postNumber: number) => PostResponse | undefined) {
  const previews = ref<RefPreview[]>([])
  let settleTimer: ReturnType<typeof setTimeout> | null = null

  function cancelSettle() {
    if (settleTimer !== null) {
      clearTimeout(settleTimer)
      settleTimer = null
    }
  }

  // shrink the stack to `depth` cards after a short grace period — never
  // immediately, so the pointer can brush across a parent card on its way to a
  // deeper one without the deeper card being yanked out from under it
  function shrinkTo(depth: number) {
    cancelSettle()
    settleTimer = setTimeout(() => {
      settleTimer = null
      if (previews.value.length > depth) previews.value = previews.value.slice(0, depth)
    }, CLOSE_DELAY)
  }

  // -1 when the element is not inside a preview (i.e. in a thread post), so a
  // ref there opens at level 0; a ref inside a level-N card opens at level N+1
  function previewLevelOf(element: HTMLElement): number {
    const card = element.closest<HTMLElement>('.ref-preview')
    return card ? Number(card.dataset.level) : -1
  }

  function openFromAnchor(anchor: HTMLElement) {
    const postNumber = Number(anchor.dataset.post)
    const post = getPost(postNumber)
    if (!post) return

    const level = previewLevelOf(anchor) + 1
    // the same ref is already the deepest card — leave the stack untouched
    if (previews.value.length === level + 1 && previews.value[level]?.postNumber === postNumber) {
      return
    }

    const rect = anchor.getBoundingClientRect()
    const left = Math.min(rect.left, window.innerWidth - PREVIEW_MAX_WIDTH - 8)
    const entry: RefPreview = {
      postNumber,
      level,
      post,
      top: rect.bottom + 4,
      left: Math.max(8, left),
    }
    previews.value = [...previews.value.slice(0, level), entry]
  }

  function handleOver(event: MouseEvent) {
    const target = event.target as HTMLElement | null
    if (!target) return

    const anchor = target.closest<HTMLElement>('a.post-ref[data-post]')
    if (anchor) {
      cancelSettle()
      openFromAnchor(anchor)
      return
    }

    // over a preview card but not a ref: keep it and its ancestors, and schedule
    // (don't force) dropping any cards stacked deeper than it
    const level = previewLevelOf(target)
    if (level >= 0) shrinkTo(level + 1)
  }

  function handleOut(event: MouseEvent) {
    const target = event.target as HTMLElement | null
    if (target?.closest('a.post-ref[data-post], .ref-preview')) shrinkTo(0)
  }

  document.addEventListener('mouseover', handleOver)
  document.addEventListener('mouseout', handleOut)
  onScopeDispose(() => {
    document.removeEventListener('mouseover', handleOver)
    document.removeEventListener('mouseout', handleOut)
    cancelSettle()
  })

  function clear() {
    cancelSettle()
    previews.value = []
  }

  return { previews, clear }
}

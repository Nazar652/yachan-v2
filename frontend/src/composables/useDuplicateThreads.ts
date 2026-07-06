import { computed, onScopeDispose, ref, watch, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import { getSimilarThreadsForText } from '@/api/search'

const DEBOUNCE_MS = 600
// shorter drafts are too noisy to embed meaningfully
const MIN_TEXT_LENGTH = 15

export function duplicateThreadsQueryKey(slug: string | Ref<string>, text: string | Ref<string>) {
  return ['duplicate-threads', slug, text] as const
}

export function useDuplicateThreads(slug: Ref<string>, text: Ref<string>) {
  // starts empty regardless of the initial text, so even a pre-filled draft
  // debounces before firing its first request
  const debouncedText = ref('')
  let timer: ReturnType<typeof setTimeout> | undefined

  watch(text, (value) => {
    if (timer !== undefined) clearTimeout(timer)
    timer = setTimeout(() => {
      debouncedText.value = value
    }, DEBOUNCE_MS)
  })

  onScopeDispose(() => {
    if (timer !== undefined) clearTimeout(timer)
  })

  return useQuery({
    queryKey: duplicateThreadsQueryKey(slug, debouncedText),
    queryFn: () => getSimilarThreadsForText(slug.value, debouncedText.value),
    enabled: computed(() => debouncedText.value.trim().length >= MIN_TEXT_LENGTH),
  })
}

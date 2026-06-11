import { computed, ref, toValue, type MaybeRefOrGetter } from 'vue'

export const OWN_POSTS_STORAGE_KEY = 'yachan_you_posts'

// post numbers the visitor authored, grouped by board slug (numbers are unique
// per board). purely client-side — the backend never knows "who" a poster is.
type OwnPostsBySlug = Record<string, number[]>

function readStored(): OwnPostsBySlug {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(OWN_POSTS_STORAGE_KEY) ?? '{}')
    if (!parsed || typeof parsed !== 'object') return {}
    const result: OwnPostsBySlug = {}
    for (const [slug, numbers] of Object.entries(parsed as Record<string, unknown>)) {
      if (Array.isArray(numbers)) {
        result[slug] = numbers.filter((value): value is number => typeof value === 'number')
      }
    }
    return result
  } catch {
    return {}
  }
}

// module-level shared state so every component that calls useOwnPosts observes
// the same set — a reply marked in ReplyForm immediately lights up "(You)" in
// the already-mounted PostArticle list
const ownPostsBySlug = ref<OwnPostsBySlug>(readStored())

function persist() {
  localStorage.setItem(OWN_POSTS_STORAGE_KEY, JSON.stringify(ownPostsBySlug.value))
}

export function useOwnPosts(slug: MaybeRefOrGetter<string>) {
  const ownNumbers = computed(() => new Set(ownPostsBySlug.value[toValue(slug)] ?? []))

  function isOwn(postNumber: number): boolean {
    return ownNumbers.value.has(postNumber)
  }

  function markOwn(postNumber: number) {
    const key = toValue(slug)
    const current = ownPostsBySlug.value[key] ?? []
    if (current.includes(postNumber)) return
    ownPostsBySlug.value = { ...ownPostsBySlug.value, [key]: [...current, postNumber] }
    persist()
  }

  return { ownNumbers, isOwn, markOwn }
}

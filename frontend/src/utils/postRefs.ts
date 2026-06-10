const POST_REF_RE = /data-post="(\d+)"/g

// the body html is rendered server-side, where every >>N reference becomes an
// <a class="post-ref" data-post="N">; reading the data-post attributes mirrors
// exactly which references are clickable, ignoring stray >>N inside code blocks
export function extractPostRefs(html: string | null | undefined): number[] {
  if (!html) return []
  const seen = new Set<number>()
  for (const match of html.matchAll(POST_REF_RE)) {
    seen.add(Number(match[1]))
  }
  return [...seen]
}

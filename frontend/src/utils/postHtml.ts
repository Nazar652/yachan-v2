const CODE_BLOCK_RE = /<pre><code([^>]*)>([\s\S]*?)<\/code><\/pre>/g

const POST_REF_TAG_RE = /<a class="post-ref" data-post="(\d+)"[^>]*>[^<]*<\/a>/g

// the body html renders every >>N reference as <a class="post-ref" data-post="N">;
// append a (You) marker right after any reference that points at one of the
// visitor's own posts, mirroring the tag shown on the post itself
export function annotateOwnRefs(html: string, ownNumbers: Set<number>): string {
  if (ownNumbers.size === 0) return html
  return html.replace(POST_REF_TAG_RE, (whole, number: string) =>
    ownNumbers.has(Number(number))
      ? `${whole}<span class="post-you"> (You)</span>`
      : whole,
  )
}

// the code content comes from the backend renderer with raw html escaped,
// so it never contains nested tags — splitting on newlines is safe
export function numberCodeLines(html: string): string {
  return html.replace(CODE_BLOCK_RE, (wholeMatch, attributes: string, content: string) => {
    const lines = content.split('\n')
    if (lines.length > 0 && lines[lines.length - 1] === '') {
      lines.pop()
    }
    const numbered = lines.map((line) => `<span class="code-line">${line}</span>`).join('')
    return `<pre><code${attributes}>${numbered}</code></pre>`
  })
}

const CODE_BLOCK_RE = /<pre><code([^>]*)>([\s\S]*?)<\/code><\/pre>/g

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

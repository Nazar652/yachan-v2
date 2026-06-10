import { describe, expect, it } from 'vitest'

import { numberCodeLines } from '@/utils/postHtml'

describe('numberCodeLines', () => {
  it('wraps each code block line in a numbered span', () => {
    expect(numberCodeLines('<pre><code>a\nb\n</code></pre>')).toBe(
      '<pre><code><span class="code-line">a</span><span class="code-line">b</span></code></pre>',
    )
  })

  it('preserves the language class on the code element', () => {
    expect(numberCodeLines('<pre><code class="language-python">x\n</code></pre>')).toContain(
      '<code class="language-python">',
    )
  })

  it('keeps empty lines as empty spans', () => {
    expect(numberCodeLines('<pre><code>a\n\nb\n</code></pre>')).toContain('<span class="code-line"></span>')
  })

  it('transforms every code block in the html', () => {
    const html = '<pre><code>a\n</code></pre><p>x</p><pre><code>b\n</code></pre>'
    expect(numberCodeLines(html).match(/code-line/g)).toHaveLength(2)
  })

  it('leaves html without code blocks unchanged', () => {
    expect(numberCodeLines('<p><strong>x</strong></p>')).toBe('<p><strong>x</strong></p>')
  })

  it('leaves inline code untouched', () => {
    expect(numberCodeLines('<p><code>x</code></p>')).toBe('<p><code>x</code></p>')
  })
})

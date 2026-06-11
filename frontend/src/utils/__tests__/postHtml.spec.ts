import { describe, expect, it } from 'vitest'

import { annotateOwnRefs, numberCodeLines } from '@/utils/postHtml'

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

describe('annotateOwnRefs', () => {
  const ownRef = '<a class="post-ref" data-post="101">&gt;&gt;101</a>'
  const otherRef = '<a class="post-ref" data-post="202">&gt;&gt;202</a>'

  it('appends a (You) marker after a reference to an own post', () => {
    expect(annotateOwnRefs(ownRef, new Set([101]))).toBe(
      `${ownRef}<span class="post-you"> (You)</span>`,
    )
  })

  it('leaves references to other posts untouched', () => {
    expect(annotateOwnRefs(otherRef, new Set([101]))).toBe(otherRef)
  })

  it('annotates only the own references among several', () => {
    const result = annotateOwnRefs(`${ownRef}${otherRef}`, new Set([101]))
    expect(result.match(/post-you/g)).toHaveLength(1)
    expect(result).toBe(`${ownRef}<span class="post-you"> (You)</span>${otherRef}`)
  })

  it('returns the html unchanged when there are no own posts', () => {
    expect(annotateOwnRefs(ownRef, new Set())).toBe(ownRef)
  })
})

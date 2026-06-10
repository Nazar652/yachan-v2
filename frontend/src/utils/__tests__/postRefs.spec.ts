import { describe, expect, it } from 'vitest'

import { extractPostRefs } from '@/utils/postRefs'

describe('extractPostRefs', () => {
  it('returns an empty array for empty input', () => {
    expect(extractPostRefs('')).toEqual([])
    expect(extractPostRefs(null)).toEqual([])
    expect(extractPostRefs(undefined)).toEqual([])
  })

  it('extracts referenced post numbers from data-post attributes', () => {
    const html = '<p><a class="post-ref" data-post="101">&gt;&gt;101</a> hi</p>'
    expect(extractPostRefs(html)).toEqual([101])
  })

  it('extracts multiple references in order of first appearance', () => {
    const html = '<a data-post="5"></a><a data-post="9"></a><a data-post="5"></a>'
    expect(extractPostRefs(html)).toEqual([5, 9])
  })

  it('ignores html without post references', () => {
    expect(extractPostRefs('<p>plain body</p>')).toEqual([])
  })
})

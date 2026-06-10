import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import PostBody from '@/components/ui/PostBody.vue'

describe('PostBody', () => {
  it('renders the server html', () => {
    const wrapper = mount(PostBody, { props: { html: '<p><strong>x</strong></p>' } })
    expect(wrapper.find('.post-body').html()).toContain('<strong>x</strong>')
  })

  it('numbers code block lines', () => {
    const wrapper = mount(PostBody, { props: { html: '<pre><code>a\nb\n</code></pre>' } })
    expect(wrapper.findAll('.code-line').map((line) => line.text())).toEqual(['a', 'b'])
  })

  it('leaves inline code untouched', () => {
    const wrapper = mount(PostBody, { props: { html: '<p><code>x</code></p>' } })
    expect(wrapper.findAll('.code-line')).toHaveLength(0)
  })
})

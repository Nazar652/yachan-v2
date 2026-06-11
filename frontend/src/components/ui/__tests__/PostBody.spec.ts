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

  it('tags a reference to an own post with (You)', () => {
    const wrapper = mount(PostBody, {
      props: {
        html: '<a class="post-ref" data-post="101">&gt;&gt;101</a>',
        ownNumbers: new Set([101]),
      },
    })
    expect(wrapper.find('.post-you').text()).toBe('(You)')
  })

  it('does not tag references to other posts', () => {
    const wrapper = mount(PostBody, {
      props: {
        html: '<a class="post-ref" data-post="202">&gt;&gt;202</a>',
        ownNumbers: new Set([101]),
      },
    })
    expect(wrapper.find('.post-you').exists()).toBe(false)
  })

  it('emits navigate with the referenced post number when a post-ref is clicked', async () => {
    const wrapper = mount(PostBody, {
      props: { html: '<a class="post-ref" data-post="101">&gt;&gt;101</a>' },
    })
    await wrapper.find('a.post-ref').trigger('click')
    expect(wrapper.emitted('navigate')).toEqual([[101]])
  })

  it('does not emit navigate when a non-reference element is clicked', async () => {
    const wrapper = mount(PostBody, { props: { html: '<p>plain</p>' } })
    await wrapper.find('p').trigger('click')
    expect(wrapper.emitted('navigate')).toBeUndefined()
  })
})

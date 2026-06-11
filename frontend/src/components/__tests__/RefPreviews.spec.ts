import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'

import RefPreviews from '@/components/RefPreviews.vue'
import { useOwnPosts } from '@/composables/useOwnPosts'
import type { PostResponse } from '@/api/types'

function makePost(overrides: Partial<PostResponse> = {}): PostResponse {
  return {
    id: 101, post_number: 101, thread_id: 1, board_id: 1, name: 'Anon', tripcode: null,
    body: 'hello', body_html: '<p>hello</p>', sage: false, is_op: false, is_edited: false,
    edited_at: null, created_at: '2024-01-01T00:00:00', can_edit: false, attachments: [],
    ...overrides,
  }
}

const POSTS: PostResponse[] = [
  makePost({ id: 101, post_number: 101, is_op: true, body_html: '<p>hello <a class="post-ref" data-post="102">&gt;&gt;102</a></p>' }),
  makePost({ id: 102, post_number: 102, body: 'world', body_html: '<p>world</p>' }),
]

function hover(postNumber: number) {
  const anchor = document.createElement('a')
  anchor.className = 'post-ref'
  anchor.dataset.post = String(postNumber)
  document.body.appendChild(anchor)
  anchor.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }))
  return anchor
}

function mountPreviews() {
  return mount(RefPreviews, { props: { posts: POSTS, slug: 'b' }, attachTo: document.body })
}

let wrapper: VueWrapper

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  wrapper?.unmount()
  document.body.innerHTML = ''
})

describe('RefPreviews', () => {
  it('shows a preview card with the referenced post on hover', async () => {
    wrapper = mountPreviews()
    hover(101)
    await nextTick()

    const card = document.body.querySelector('.ref-preview')
    expect(card).not.toBeNull()
    expect(card!.textContent).toContain('No.101')
    expect(card!.textContent).toContain('hello')
  })

  it('shows nothing for a ref to a post outside the thread', async () => {
    wrapper = mountPreviews()
    hover(404)
    await nextTick()
    expect(document.body.querySelector('.ref-preview')).toBeNull()
  })

  it('renders image thumbnails of the referenced post', async () => {
    wrapper = mount(RefPreviews, {
      props: {
        posts: [makePost({
          attachments: [{ id: 5, media_type: 'image', original_name: 'p.jpg', url: '/media/p.jpg', thumbnail_url: '/media/t.jpg', mime_type: 'image/jpeg', width: 1, height: 1, size_bytes: 1, duration_seconds: null }],
        })],
        slug: 'b',
      },
      attachTo: document.body,
    })
    hover(101)
    await nextTick()
    expect(document.body.querySelector('.ref-preview img')!.getAttribute('src')).toBe('/media/t.jpg')
  })

  it('emits navigate and closes the previews when a ref inside the card is clicked', async () => {
    wrapper = mountPreviews()
    hover(101)
    await nextTick()

    const innerRef = document.body.querySelector<HTMLElement>('.ref-preview a.post-ref')!
    innerRef.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await nextTick()

    expect(wrapper.emitted('navigate')).toEqual([[102]])
    expect(document.body.querySelector('.ref-preview')).toBeNull()
  })

  it('tags the preview header with (You) for your own post', async () => {
    useOwnPosts('b').markOwn(101)
    wrapper = mountPreviews()
    hover(101)
    await nextTick()
    expect(document.body.querySelector('.ref-preview .post-you')!.textContent).toBe('(You)')
  })
})

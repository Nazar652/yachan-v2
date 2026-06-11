import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'

import { useRefPreviews, type RefPreview } from '@/composables/useRefPreviews'
import type { PostResponse } from '@/api/types'

function makePost(postNumber: number): PostResponse {
  return {
    id: postNumber, post_number: postNumber, thread_id: 1, board_id: 1, name: 'Anon',
    tripcode: null, body: `body ${postNumber}`, body_html: `<p>body ${postNumber}</p>`,
    sage: false, is_op: false, is_edited: false, edited_at: null,
    created_at: '2024-01-01T00:00:00', can_edit: false, attachments: [],
  }
}

// the thread posts the lookup resolves against; refs to anything else (another
// thread) return undefined and must not open a preview
const POSTS = new Map([101, 102, 103].map((number) => [number, makePost(number)]))

function mountHost() {
  return mount(
    defineComponent({
      setup(_, { expose }) {
        const api = useRefPreviews((postNumber) => POSTS.get(postNumber))
        expose(api)
        return () => h('div')
      },
    }),
    { attachTo: document.body },
  )
}

function previewsOf(wrapper: VueWrapper): RefPreview[] {
  return (wrapper.vm as unknown as { previews: RefPreview[] }).previews
}

function makeAnchor(postNumber: number, parent: HTMLElement = document.body): HTMLElement {
  const anchor = document.createElement('a')
  anchor.className = 'post-ref'
  anchor.dataset.post = String(postNumber)
  parent.appendChild(anchor)
  return anchor
}

function hover(element: HTMLElement) {
  element.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }))
}

function leave(element: HTMLElement) {
  element.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }))
}

let wrapper: VueWrapper

beforeEach(() => {
  wrapper = mountHost()
})

afterEach(() => {
  wrapper.unmount()
  document.body.innerHTML = ''
  vi.useRealTimers()
})

describe('useRefPreviews', () => {
  it('opens a preview when hovering a ref to a post in the thread', () => {
    hover(makeAnchor(101))
    const previews = previewsOf(wrapper)
    expect(previews).toHaveLength(1)
    expect(previews[0]!.postNumber).toBe(101)
    expect(previews[0]!.level).toBe(0)
    expect(previews[0]!.post.post_number).toBe(101)
  })

  it('ignores a ref to a post outside the thread', () => {
    hover(makeAnchor(999))
    expect(previewsOf(wrapper)).toHaveLength(0)
  })

  it('stacks a deeper preview when hovering a ref inside a preview card', () => {
    hover(makeAnchor(101))

    const card = document.createElement('div')
    card.className = 'ref-preview'
    card.dataset.level = '0'
    document.body.appendChild(card)
    hover(makeAnchor(102, card))

    const previews = previewsOf(wrapper)
    expect(previews.map((preview) => preview.postNumber)).toEqual([101, 102])
    expect(previews[1]!.level).toBe(1)
  })

  it('keeps a deeper card while the pointer brushes a parent card en route to it', () => {
    vi.useFakeTimers()
    hover(makeAnchor(101))

    const cardLevel0 = document.createElement('div')
    cardLevel0.className = 'ref-preview'
    cardLevel0.dataset.level = '0'
    document.body.appendChild(cardLevel0)
    hover(makeAnchor(102, cardLevel0))

    const cardLevel1 = document.createElement('div')
    cardLevel1.className = 'ref-preview'
    cardLevel1.dataset.level = '1'
    document.body.appendChild(cardLevel1)
    hover(makeAnchor(103, cardLevel1))

    // pointer passes over the level-1 card on its way down to the level-2 card:
    // the level-2 card must survive the brush, only collapsing after the delay
    cardLevel1.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }))
    expect(previewsOf(wrapper)).toHaveLength(3)

    vi.runAllTimers()
    expect(previewsOf(wrapper)).toHaveLength(2)
  })

  it('replaces the preview when hovering another ref at the same level', () => {
    hover(makeAnchor(101))
    hover(makeAnchor(102))
    const previews = previewsOf(wrapper)
    expect(previews).toHaveLength(1)
    expect(previews[0]!.postNumber).toBe(102)
  })

  it('does not rebuild the stack when re-hovering the same deepest ref', () => {
    const anchor = makeAnchor(101)
    hover(anchor)
    const first = previewsOf(wrapper)
    hover(anchor)
    expect(previewsOf(wrapper)).toBe(first)
  })

  it('closes the previews after the pointer leaves and the delay elapses', () => {
    vi.useFakeTimers()
    const anchor = makeAnchor(101)
    hover(anchor)
    expect(previewsOf(wrapper)).toHaveLength(1)

    leave(anchor)
    vi.runAllTimers()
    expect(previewsOf(wrapper)).toHaveLength(0)
  })

  it('keeps the preview open when the pointer moves onto the card before the delay', () => {
    vi.useFakeTimers()
    const anchor = makeAnchor(101)
    hover(anchor)
    leave(anchor)

    const card = document.createElement('div')
    card.className = 'ref-preview'
    card.dataset.level = '0'
    document.body.appendChild(card)
    hover(card)

    vi.runAllTimers()
    expect(previewsOf(wrapper)).toHaveLength(1)
  })

  it('clear empties the stack', () => {
    hover(makeAnchor(101))
    ;(wrapper.vm as unknown as { clear: () => void }).clear()
    expect(previewsOf(wrapper)).toHaveLength(0)
  })

  it('detaches its listeners on unmount', () => {
    wrapper.unmount()
    hover(makeAnchor(101))
    expect(previewsOf(wrapper)).toHaveLength(0)
  })
})

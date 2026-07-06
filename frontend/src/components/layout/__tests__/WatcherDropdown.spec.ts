import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import WatcherDropdown from '@/components/layout/WatcherDropdown.vue'
import type { WatchedThreadStatus } from '@/composables/useWatcherStatus'

const { watcherStatusMock, removeMock, routerLinkStub } = vi.hoisted(() => ({
  watcherStatusMock: vi.fn(),
  removeMock: vi.fn(),
  routerLinkStub: { props: ['to'], template: '<a :href="to"><slot /></a>' },
}))

vi.mock('@/composables/useWatcherStatus', () => ({
  useWatcherStatus: watcherStatusMock,
}))

vi.mock('vue-router', () => ({
  RouterLink: routerLinkStub,
}))

function stub(watchedStatuses: WatchedThreadStatus[], totalUnread = 0) {
  watcherStatusMock.mockReturnValue({ watchedStatuses, totalUnread, remove: removeMock })
}

function mountDropdown() {
  return mount(WatcherDropdown, { attachTo: document.body })
}

beforeEach(() => {
  removeMock.mockReset()
  stub([])
})

describe('WatcherDropdown', () => {
  it('hides the unread badge when totalUnread is zero', () => {
    stub([], 0)
    const wrapper = mountDropdown()
    expect(wrapper.text()).not.toMatch(/\d/)
    wrapper.unmount()
  })

  it('shows the unread badge when totalUnread is positive', () => {
    stub([], 3)
    const wrapper = mountDropdown()
    expect(wrapper.text()).toContain('3')
    wrapper.unmount()
  })

  it('is closed until the toggle button is clicked', async () => {
    stub([{ threadId: 1, slug: 'b', title: 'hi', unread: 0, dead: false }])
    const wrapper = mountDropdown()
    expect(wrapper.find('a').exists()).toBe(false)

    await wrapper.find('button[aria-label="Watched threads"]').trigger('click')

    expect(wrapper.find('a').exists()).toBe(true)
    wrapper.unmount()
  })

  it('shows an empty message with no watched threads', async () => {
    stub([])
    const wrapper = mountDropdown()
    await wrapper.find('button[aria-label="Watched threads"]').trigger('click')
    expect(wrapper.text()).toContain('No watched threads')
    wrapper.unmount()
  })

  it('lists a watched thread with title, slug and unread badge', async () => {
    stub([{ threadId: 1, slug: 'b', title: 'hello', unread: 4, dead: false }])
    const wrapper = mountDropdown()
    await wrapper.find('button[aria-label="Watched threads"]').trigger('click')

    expect(wrapper.text()).toContain('hello')
    expect(wrapper.text()).toContain('/b/')
    expect(wrapper.text()).toContain('4')
    expect(wrapper.find('a').attributes('href')).toBe('/b/thread/1')
    wrapper.unmount()
  })

  it('falls back to (no title) for an untitled thread', async () => {
    stub([{ threadId: 1, slug: 'b', title: null, unread: 0, dead: false }])
    const wrapper = mountDropdown()
    await wrapper.find('button[aria-label="Watched threads"]').trigger('click')
    expect(wrapper.text()).toContain('(no title)')
    wrapper.unmount()
  })

  it('marks a dead thread as deleted instead of showing an unread badge', async () => {
    stub([{ threadId: 1, slug: 'b', title: 'gone', unread: 0, dead: true }])
    const wrapper = mountDropdown()
    await wrapper.find('button[aria-label="Watched threads"]').trigger('click')
    expect(wrapper.text()).toContain('deleted')
    wrapper.unmount()
  })

  it('removes a thread when its remove button is clicked', async () => {
    stub([{ threadId: 1, slug: 'b', title: 'hello', unread: 0, dead: false }])
    const wrapper = mountDropdown()
    await wrapper.find('button[aria-label="Watched threads"]').trigger('click')

    await wrapper.find('button[aria-label="Stop watching"]').trigger('click')

    expect(removeMock).toHaveBeenCalledWith(1)
    wrapper.unmount()
  })

  it('closes the dropdown when a row link is clicked', async () => {
    stub([{ threadId: 1, slug: 'b', title: 'hello', unread: 0, dead: false }])
    const wrapper = mountDropdown()
    await wrapper.find('button[aria-label="Watched threads"]').trigger('click')

    await wrapper.find('a').trigger('click')

    expect(wrapper.find('a').exists()).toBe(false)
    wrapper.unmount()
  })

  it('closes the dropdown when clicking outside it', async () => {
    stub([{ threadId: 1, slug: 'b', title: 'hello', unread: 0, dead: false }])
    const wrapper = mountDropdown()
    await wrapper.find('button[aria-label="Watched threads"]').trigger('click')
    expect(wrapper.find('a').exists()).toBe(true)

    document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('a').exists()).toBe(false)
    wrapper.unmount()
  })
})

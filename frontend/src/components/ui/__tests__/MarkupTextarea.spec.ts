import { describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

import MarkupTextarea from '@/components/ui/MarkupTextarea.vue'
import { REFUSAL } from '@/utils/formatting'

function mountEditor(text: string, attrs: Record<string, string> = {}) {
  const wrapper = mount(MarkupTextarea, { props: { modelValue: text }, attrs })
  const textarea = wrapper.find('textarea').element
  return { wrapper, textarea }
}

describe('MarkupTextarea', () => {
  it('renders a toolbar button for every format', () => {
    const { wrapper } = mountEditor('')
    const titles = wrapper.findAll('button').map((button) => button.attributes('title'))
    expect(titles).toEqual([
      'Bold',
      'Italic',
      'Underline',
      'Strikethrough',
      'Spoiler',
      'Inline code',
      'Code block',
      'Quote',
      'Escape markdown',
    ])
  })

  it('passes attributes through to the textarea', () => {
    const { wrapper } = mountEditor('', { id: 'reply-body', rows: '4', placeholder: 'Reply body…' })
    const textarea = wrapper.find('textarea')
    expect(textarea.attributes('id')).toBe('reply-body')
    expect(textarea.attributes('rows')).toBe('4')
    expect(textarea.attributes('placeholder')).toBe('Reply body…')
  })

  it('applies the clicked format to the selection and restores it', async () => {
    const { wrapper, textarea } = mountEditor('bold it')
    textarea.setSelectionRange(0, 4)
    await wrapper.find('button[title="Bold"]').trigger('click')
    await flushPromises()
    expect(wrapper.emitted('update:modelValue')).toEqual([['**bold** it']])
    expect(textarea.value).toBe('**bold** it')
    expect(textarea.selectionStart).toBe(2)
    expect(textarea.selectionEnd).toBe(6)
  })

  it('escapes the selection from the escape button', async () => {
    const { wrapper, textarea } = mountEditor('>>123')
    textarea.setSelectionRange(0, 5)
    await wrapper.find('button[title="Escape markdown"]').trigger('click')
    await flushPromises()
    expect(wrapper.emitted('update:modelValue')).toEqual([['\\>\\>123']])
  })

  it('shows the refusal reason and keeps the text unchanged', async () => {
    const { wrapper, textarea } = mountEditor('`x`')
    textarea.setSelectionRange(0, 3)
    await wrapper.find('button[title="Bold"]').trigger('click')
    await flushPromises()
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
    expect(wrapper.text()).toContain(REFUSAL.inlineCode)
  })

  it('clears the refusal reason on input', async () => {
    const { wrapper, textarea } = mountEditor('`x`')
    textarea.setSelectionRange(0, 3)
    await wrapper.find('button[title="Bold"]').trigger('click')
    expect(wrapper.text()).toContain(REFUSAL.inlineCode)
    await wrapper.find('textarea').trigger('input')
    expect(wrapper.text()).not.toContain(REFUSAL.inlineCode)
  })

  it('clears the refusal reason after a successful apply', async () => {
    const { wrapper, textarea } = mountEditor('`x` y')
    textarea.setSelectionRange(0, 3)
    await wrapper.find('button[title="Bold"]').trigger('click')
    expect(wrapper.text()).toContain(REFUSAL.inlineCode)
    textarea.setSelectionRange(4, 5)
    await wrapper.find('button[title="Bold"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).not.toContain(REFUSAL.inlineCode)
  })
})

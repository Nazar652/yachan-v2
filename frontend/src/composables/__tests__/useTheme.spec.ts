import { beforeEach, describe, expect, it } from 'vitest'

import { THEME_STORAGE_KEY, useTheme } from '@/composables/useTheme'

beforeEach(() => {
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
})

describe('useTheme', () => {
  it('defaults to light and applies the attribute', () => {
    const { theme } = useTheme()
    expect(theme.value).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('restores a stored dark theme', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    const { theme } = useTheme()
    expect(theme.value).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('falls back to light on an unknown stored value', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'solarized')
    const { theme } = useTheme()
    expect(theme.value).toBe('light')
  })

  it('toggle flips the theme, the attribute and the stored value', () => {
    const { theme, toggle } = useTheme()

    toggle()
    expect(theme.value).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')

    toggle()
    expect(theme.value).toBe('light')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
  })
})

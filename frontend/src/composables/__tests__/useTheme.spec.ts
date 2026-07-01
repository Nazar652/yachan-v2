import { beforeEach, describe, expect, it, vi } from 'vitest'

import { THEME_STORAGE_KEY } from '@/composables/useTheme'

// theme state is a module-level singleton (shared across every useTheme()
// caller), so each test resets modules and re-imports to get a fresh instance
beforeEach(() => {
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
  vi.resetModules()
})

describe('useTheme', () => {
  it('defaults to light and applies the attribute', async () => {
    const { useTheme } = await import('@/composables/useTheme')
    const { theme } = useTheme()
    expect(theme.value).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('restores a stored dark theme', async () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    const { useTheme } = await import('@/composables/useTheme')
    const { theme } = useTheme()
    expect(theme.value).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('falls back to light on an unknown stored value', async () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'solarized')
    const { useTheme } = await import('@/composables/useTheme')
    const { theme } = useTheme()
    expect(theme.value).toBe('light')
  })

  it('toggle flips the theme, the attribute and the stored value', async () => {
    const { useTheme } = await import('@/composables/useTheme')
    const { theme, toggle } = useTheme()

    toggle()
    expect(theme.value).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')

    toggle()
    expect(theme.value).toBe('light')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
  })

  it('shares theme state between independent useTheme() callers', async () => {
    const { useTheme } = await import('@/composables/useTheme')
    const header = useTheme()
    const captchaWidget = useTheme()

    header.toggle()

    expect(captchaWidget.theme.value).toBe('dark')
  })
})

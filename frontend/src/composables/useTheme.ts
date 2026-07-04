import { ref } from 'vue'

export type Theme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'yachan_theme'

function readStoredTheme(): Theme {
  return localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light'
}

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem(THEME_STORAGE_KEY, theme)
}

// module-level singleton: every caller shares the same ref, so toggling the
// theme in one component (e.g. AppHeader) is reflected reactively in others
// (e.g. CaptchaWidget) without prop drilling
const theme = ref<Theme>(readStoredTheme())

applyTheme(theme.value)

function toggle() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'

  applyTheme(theme.value)
}

// light/dark theme switch persisted to localStorage; the data-theme attribute
// on <html> drives the token overrides in main.css
export function useTheme() {
  return { theme, toggle }
}

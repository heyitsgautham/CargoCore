export const THEME_STORAGE_KEY = 'theme'

export function resolveThemePreference() {
  if (typeof window === 'undefined') return 'dark'

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY)
  if (storedTheme === 'dark' || storedTheme === 'light') return storedTheme

  return 'dark'
}

export function applyThemePreference(theme) {
  const resolvedTheme = theme === 'light' ? 'light' : 'dark'

  if (typeof document !== 'undefined') {
    const isDark = resolvedTheme === 'dark'
    document.documentElement.classList.toggle('dark', isDark)
    document.documentElement.style.colorScheme = resolvedTheme
  }

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(THEME_STORAGE_KEY, resolvedTheme)
  }

  return resolvedTheme
}

export function initializeTheme() {
  return applyThemePreference(resolveThemePreference())
}

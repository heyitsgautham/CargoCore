import { beforeEach, describe, expect, it } from 'vitest'
import {
  THEME_STORAGE_KEY,
  applyThemePreference,
  initializeTheme,
  resolveThemePreference,
} from '@/utils/theme'

beforeEach(() => {
  localStorage.clear()
  document.documentElement.className = ''
  document.documentElement.style.colorScheme = ''
})

describe('theme preference', () => {
  it('defaults to dark when nothing valid is stored', () => {
    expect(resolveThemePreference()).toBe('dark')
    localStorage.setItem(THEME_STORAGE_KEY, 'sepia')
    expect(resolveThemePreference()).toBe('dark')
  })

  it('returns a stored light or dark choice', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'light')
    expect(resolveThemePreference()).toBe('light')
  })

  it('applies light mode by removing the dark class and saving the choice', () => {
    document.documentElement.classList.add('dark')

    expect(applyThemePreference('light')).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(document.documentElement.style.colorScheme).toBe('light')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
  })

  it('treats any unknown value as dark', () => {
    expect(applyThemePreference('neon')).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('initializeTheme applies the stored preference', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'light')
    expect(initializeTheme()).toBe('light')
    expect(document.documentElement.style.colorScheme).toBe('light')
  })
})

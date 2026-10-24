import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useToast } from '@/composables/useToast'

beforeEach(() => {
  vi.useFakeTimers()
  useToast().toasts.value = []
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useToast', () => {
  it('shares one toast list across callers', () => {
    const a = useToast()
    const b = useToast()

    a.success('Saved')

    expect(b.toasts.value).toHaveLength(1)
    expect(b.toasts.value[0]).toMatchObject({ message: 'Saved', type: 'success' })
  })

  it('tags each helper with its own type', () => {
    const toast = useToast()
    toast.error('e')
    toast.info('i')
    toast.warning('w')

    expect(toast.toasts.value.map((t) => t.type)).toEqual(['error', 'info', 'warning'])
  })

  it('removes a toast after 3.5 seconds', () => {
    const toast = useToast()
    toast.info('Bye soon')

    vi.advanceTimersByTime(3499)
    expect(toast.toasts.value).toHaveLength(1)

    vi.advanceTimersByTime(1)
    expect(toast.toasts.value).toHaveLength(0)
  })
})

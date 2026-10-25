import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

describe('useAutoRefresh', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('counts down every second and refreshes when the countdown runs out', async () => {
    const refresh = vi.fn()
    const auto = useAutoRefresh(refresh, { seconds: 5 })

    auto.start()
    await vi.advanceTimersByTimeAsync(3000)
    expect(auto.countdown.value).toBe(2)
    expect(refresh).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(2000)
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(auto.countdown.value).toBe(5)
    auto.stop()
  })

  it('skips a refresh while the previous load is busy', async () => {
    const refresh = vi.fn()
    const auto = useAutoRefresh(refresh, { seconds: 2, isBusy: () => true })

    auto.start()
    await vi.advanceTimersByTimeAsync(6000)
    expect(refresh).not.toHaveBeenCalled()
    auto.stop()
  })

  it('pauses and resumes with toggle', async () => {
    const refresh = vi.fn()
    const auto = useAutoRefresh(refresh, { seconds: 2 })
    auto.start()

    auto.toggle()
    expect(auto.enabled.value).toBe(false)
    await vi.advanceTimersByTimeAsync(10000)
    expect(refresh).not.toHaveBeenCalled()

    auto.toggle()
    expect(auto.enabled.value).toBe(true)
    await vi.advanceTimersByTimeAsync(2000)
    expect(refresh).toHaveBeenCalledTimes(1)
    auto.stop()
  })
})

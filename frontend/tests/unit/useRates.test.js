import { beforeEach, describe, expect, it, vi } from 'vitest'

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body }
}

// useRates keeps a module-level cache, so each test loads a fresh copy.
async function loadUseRates() {
  vi.resetModules()
  return (await import('@/composables/useRates')).useRates
}

beforeEach(() => {
  localStorage.clear()
})

describe('useRates', () => {
  it('starts from the built-in defaults before the backend answers', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise(() => {})),
    )
    const useRates = await loadUseRates()

    const { rates, ratesReady } = useRates()

    expect(ratesReady.value).toBe(false)
    expect(rates.value.perKmRate).toBe(12)
    expect(rates.value.materials.map((m) => m.id)).toEqual(['box', 'bubbleWrap', 'crate'])
  })

  it('loads rates from the backend and converts the old materials object to a list', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { perKmRate: 20, materials: { box: 60, crate: 250 } }))
    vi.stubGlobal('fetch', fetchMock)
    localStorage.setItem('auth_token', 'tok')
    const useRates = await loadUseRates()

    const { rates, ratesReady } = useRates()
    await vi.waitFor(() => expect(ratesReady.value).toBe(true))

    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer tok')
    expect(rates.value.perKmRate).toBe(20)
    expect(rates.value.materials).toEqual([
      { id: 'box', name: 'Box', rate: 60, unit: 'pcs' },
      { id: 'bubbleWrap', name: 'Bubble Wrap', rate: 20, unit: 'm' },
      { id: 'crate', name: 'Crate Rental', rate: 250, unit: 'pcs' },
    ])
  })

  it('fetches once no matter how many components call it', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { perKmRate: 15, materials: [] }))
    vi.stubGlobal('fetch', fetchMock)
    const useRates = await loadUseRates()

    useRates()
    useRates()
    useRates()

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('keeps the defaults when the backend is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const useRates = await loadUseRates()

    const { rates, ratesReady } = useRates()
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(ratesReady.value).toBe(false)
    expect(rates.value.baseBookingFee).toBe(220)
  })

  it('saveRates PUTs the new config and shares it with every caller', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, { perKmRate: 12, materials: [] }))
      .mockResolvedValueOnce(jsonResponse(200, { perKmRate: 30, materials: [] }))
    vi.stubGlobal('fetch', fetchMock)
    const useRates = await loadUseRates()

    const first = useRates()
    const second = useRates()
    await first.saveRates({ perKmRate: 30 })

    expect(fetchMock.mock.calls[1][1].method).toBe('PUT')
    expect(second.rates.value.perKmRate).toBe(30)
  })

  it('saveRates throws when the backend rejects the update', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, { materials: [] }))
      .mockResolvedValueOnce(jsonResponse(403, {}))
    vi.stubGlobal('fetch', fetchMock)
    const useRates = await loadUseRates()

    await expect(useRates().saveRates({})).rejects.toThrow('Failed to save rates')
  })

  it('refreshRates refetches and replaces the cached rates', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, { perKmRate: 13, materials: [] }))
      .mockResolvedValueOnce(jsonResponse(200, { perKmRate: 14, materials: [] }))
    vi.stubGlobal('fetch', fetchMock)
    const useRates = await loadUseRates()

    const { rates, ratesReady, refreshRates } = useRates()
    await vi.waitFor(() => expect(rates.value.perKmRate).toBe(13))
    await refreshRates()

    expect(ratesReady.value).toBe(true)
    expect(rates.value.perKmRate).toBe(14)
  })
})

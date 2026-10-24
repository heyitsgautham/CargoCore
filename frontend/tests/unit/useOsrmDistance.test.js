import { describe, expect, it, vi } from 'vitest'
import { fetchRoadDistanceKm } from '@/composables/useOsrmDistance'

// Chennai Central to Chennai airport: about 14 km straight line.
const FROM = [13.0827, 80.2707]
const TO = [12.9941, 80.1709]

function mockFetch(response) {
  const fetchMock = vi.fn().mockResolvedValue(response)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('fetchRoadDistanceKm', () => {
  it('converts the OSRM route distance from metres to km with one decimal', async () => {
    const fetchMock = mockFetch({
      ok: true,
      json: async () => ({ code: 'Ok', routes: [{ distance: 18_765 }] }),
    })

    await expect(fetchRoadDistanceKm(...FROM, ...TO)).resolves.toBe(18.8)

    const url = fetchMock.mock.calls[0][0]
    expect(url).toContain('/80.2707,13.0827;80.1709,12.9941')
  })

  it('never returns less than 1 km', async () => {
    mockFetch({ ok: true, json: async () => ({ code: 'Ok', routes: [{ distance: 120 }] }) })
    await expect(fetchRoadDistanceKm(...FROM, ...FROM)).resolves.toBe(1)
  })

  it('falls back to haversine times 1.35 when OSRM answers with an error', async () => {
    mockFetch({ ok: false, json: async () => ({}) })
    const km = await fetchRoadDistanceKm(...FROM, ...TO)

    expect(km).toBeGreaterThan(19)
    expect(km).toBeLessThan(21)
  })

  it('falls back when OSRM finds no route', async () => {
    mockFetch({ ok: true, json: async () => ({ code: 'NoRoute', routes: [] }) })
    const km = await fetchRoadDistanceKm(...FROM, ...TO)
    expect(km).toBeGreaterThan(19)
  })

  it('falls back when the request throws', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const km = await fetchRoadDistanceKm(...FROM, ...TO)
    expect(km).toBeGreaterThan(19)
  })
})

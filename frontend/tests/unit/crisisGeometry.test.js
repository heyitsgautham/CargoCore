import { describe, expect, it } from 'vitest'
import {
  buildApproximateCoords,
  hasCoordinates,
} from '@/LWD-views/Dispatcher/crisis/crisisGeometry'

describe('crisis map coordinates', () => {
  it('accepts only finite latitude and longitude', () => {
    expect(hasCoordinates(12.97, 77.59)).toBe(true)
    expect(hasCoordinates(null, 77.59)).toBe(false)
    expect(hasCoordinates(Number.NaN, 1)).toBe(false)
  })

  it('spreads markers around an anchor so none share a point', () => {
    const anchor = [12.97, 77.59]
    const points = [0, 1, 2, 3].map((i) => buildApproximateCoords(anchor, i))
    expect(points[0]).toEqual([12.97, 77.61])
    expect(new Set(points.map((p) => p.join())).size).toBe(4)
    for (const [lat, lng] of points) {
      expect(Math.hypot(lat - anchor[0], lng - anchor[1])).toBeLessThan(0.06)
    }
  })

  it('returns null without a usable anchor', () => {
    expect(buildApproximateCoords(null, 0)).toBeNull()
    expect(buildApproximateCoords([1], 0)).toBeNull()
  })
})

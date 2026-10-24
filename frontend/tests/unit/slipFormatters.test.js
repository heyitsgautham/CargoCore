import { describe, expect, it } from 'vitest'
import {
  assetCode,
  buildAssetEquipment,
  buildTripSchedule,
  cleanText,
  compactAddress,
  defaultAssetQuantities,
  escapeHtml,
  estimateBoxes,
  estimateDistanceKm,
  estimateFuelLiters,
  estimateTravelMinutes,
  fmtShort,
  formatDistance,
  formatDuration,
  haversineKm,
  inr,
  num,
  routeLabel,
  routeViaLabel,
  summarizeSpecialItems,
  vehicleCapacityLabel,
} from '@/composables/slips/formatters'

describe('text and number helpers', () => {
  it('formats rupees with Indian digit grouping', () => {
    expect(inr(1234567)).toBe('₹12,34,567')
    expect(inr(undefined)).toBe('₹0')
  })

  it('escapes every HTML-significant character', () => {
    expect(escapeHtml(`<a href="x">Tom & 'Jerry'</a>`)).toBe(
      '&lt;a href=&quot;x&quot;&gt;Tom &amp; &#39;Jerry&#39;&lt;/a&gt;',
    )
    expect(escapeHtml(null)).toBe('')
  })

  it('falls back for blank text and non-numeric numbers', () => {
    expect(cleanText('  ')).toBe('—')
    expect(cleanText(' Ravi ')).toBe('Ravi')
    expect(num('12.5')).toBe(12.5)
    expect(num('abc', 7)).toBe(7)
  })

  it('tidies addresses and keeps the first two parts for route labels', () => {
    expect(compactAddress(' 12 MG Rd ,  Indiranagar, Bengaluru ,')).toBe(
      '12 MG Rd, Indiranagar, Bengaluru',
    )
    expect(routeLabel('12 MG Rd, Indiranagar, Bengaluru')).toBe('12 MG Rd, Indiranagar')
    expect(routeLabel('', 'Unknown')).toBe('Unknown')
  })

  it('returns TBD or the raw value for dates it cannot format', () => {
    expect(fmtShort(null)).toBe('TBD')
    expect(fmtShort('someday')).toBe('someday')
    expect(fmtShort('2026-04-05T12:00:00Z')).toMatch(/2026/)
  })
})

describe('distance and time estimates', () => {
  it('computes great-circle distance and rejects bad coordinates', () => {
    expect(haversineKm(12.9716, 77.5946, 13.0827, 80.2707)).toBeCloseTo(290, -1)
    expect(haversineKm('x', 1, 2, 3)).toBeNull()
  })

  it('prefers an explicit order distance, else adds 24% to the straight line', () => {
    expect(estimateDistanceKm({ distance_km: 42 })).toBe(42)
    const fromCoords = estimateDistanceKm({
      pickupLat: 12.97,
      pickupLng: 77.59,
      deliveryLat: 13.08,
      deliveryLng: 77.59,
    })
    expect(fromCoords).toBeCloseTo(haversineKm(12.97, 77.59, 13.08, 77.59) * 1.24, 5)
    expect(estimateDistanceKm({})).toBeNull()
  })

  it('formats distances and durations', () => {
    expect(formatDistance(12.34)).toBe('Distance: 12.3 km')
    expect(formatDistance(150.6)).toBe('Distance: 151 km')
    expect(formatDistance(null)).toBe('Route based on dispatch plan')
    expect(formatDuration(45)).toBe('45 min')
    expect(formatDuration(90)).toBe('1.5 hrs')
    expect(formatDuration(0)).toBe('TBD')
  })

  it('uses slower speeds and lower mileage for trucks', () => {
    expect(estimateTravelMinutes(28, 'Truck XL')).toBe(60)
    expect(estimateTravelMinutes(30, 'Mini')).toBe(60)
    expect(estimateTravelMinutes(null)).toBe(45)
    expect(estimateFuelLiters(55, 'heavy truck')).toBe(10)
    expect(estimateFuelLiters(0)).toBeNull()
  })

  it('builds a trip schedule from the scheduled time', () => {
    const schedule = buildTripSchedule({
      scheduledAt: '2026-04-05T09:00:00',
      distance_km: 30,
      laborCount: 2,
    })

    expect(schedule.loadTime).toBe('75 minutes')
    expect(schedule.unloadTime).toBe('55 minutes')
    expect(schedule.totalDistance).toBe('30.0 km')
    expect(schedule.routeMeta).toBe('Distance: 30.0 km | Est. Time: 1.0 hrs')
    expect(schedule.pickupTime).toMatch(/^09:00 AM$/)
  })
})

describe('cargo and asset helpers', () => {
  it('labels vehicle capacity from type or weight', () => {
    expect(vehicleCapacityLabel('Truck')).toBe('3.5 Tons')
    expect(vehicleCapacityLabel('', 1000)).toBe('2.0 Tons')
    expect(vehicleCapacityLabel('Mini', 100)).toBe('1.0 Ton')
  })

  it('estimates boxes from count, then volume, then weight', () => {
    expect(estimateBoxes({ boxCount: 12 })).toBe(12)
    expect(estimateBoxes({ volume: 2 })).toBe(16)
    expect(estimateBoxes({ weight: 350 })).toBe(10)
    expect(estimateBoxes({})).toBe(1)
  })

  it('summarises special handling tags', () => {
    expect(summarizeSpecialItems({ notes: 'Fragile glass, PRIORITY', laborCount: 3 })).toBe(
      'Fragile • Priority • 3 crew',
    )
    expect(summarizeSpecialItems({ cargoType: 'Electronics' })).toBe('Electronics')
  })

  it('describes the route or falls back to the vehicle', () => {
    expect(routeViaLabel({ pickupAddr: 'A, B, C', deliveryAddr: 'D, E' }, 'KA01')).toBe(
      'Via dispatch route from A, B to D, E',
    )
    expect(routeViaLabel({}, 'KA01')).toBe('Assigned vehicle: KA01')
  })

  it('builds asset codes from label initials', () => {
    expect(assetCode('Moving Boxes', 0)).toBe('MB-001')
    expect(assetCode('', 9)).toBe('AK-010')
  })

  it('scales default asset quantities with weight and crew', () => {
    expect(defaultAssetQuantities({ weight: 700, laborCount: 3 })).toMatchObject({
      'Moving Boxes': 20,
      'Bubble Wrap (rolls)': 3,
      'Moving Blankets': 6,
      'Tape Rolls': 4,
    })
  })

  it('normalises provided assets and drops empty rows', () => {
    const items = buildAssetEquipment({
      assetItems: [
        { name: 'Tape Rolls', count: 5, condition: 'New' },
        { label: 'Ghost Item', qty: 0 },
      ],
    })

    expect(items).toEqual([{ label: 'Tape Rolls', id: 'TR-001', qty: 5, cond: 'New' }])
  })

  it('falls back to the default kit when no assets are provided', () => {
    const items = buildAssetEquipment({ weight: 0 })
    expect(items).toHaveLength(7)
    expect(items[0]).toEqual({ label: 'Moving Boxes', id: 'MB-001', qty: 6, cond: 'Ready' })
  })
})

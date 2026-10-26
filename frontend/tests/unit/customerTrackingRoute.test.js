import { ref } from 'vue'
import { describe, expect, it } from 'vitest'
import {
  buildRouteBundle,
  getRouteFocusSettings,
  hasUsableRouteData,
  mergeRouteSegments,
  pointFromValues,
} from '@/IV-views/Individual/tracking/routeData'
import { useRouteSummary } from '@/IV-views/Individual/tracking/useRouteSummary'

describe('customer tracking route data', () => {
  it('reads coordinates only when both values are finite numbers', () => {
    expect(pointFromValues('12.9', 77.6)).toEqual([12.9, 77.6])
    expect(pointFromValues('', 77.6)).toBeNull()
    expect(pointFromValues('north', 77.6)).toBeNull()
  })

  it('joins route legs without repeating the shared point', () => {
    expect(
      mergeRouteSegments(
        [
          [1, 1],
          [2, 2],
        ],
        [
          [2, 2],
          [3, 3],
        ],
      ),
    ).toEqual([
      [1, 1],
      [2, 2],
      [3, 3],
    ])
  })

  it('falls back to straight legs and accepts a bundle with both legs', () => {
    const bundle = buildRouteBundle({ warehouse: [1, 1], pickup: [2, 2], dest: [3, 3] })

    expect(bundle.warehouseToPickup.length).toBeGreaterThanOrEqual(2)
    expect(bundle.pickupToDest.length).toBeGreaterThanOrEqual(2)
    expect(bundle.coords[0]).toEqual([1, 1])
    expect(bundle.coords.at(-1)).toEqual([3, 3])
    expect(hasUsableRouteData(bundle)).toBe(true)
    expect(hasUsableRouteData(null)).toBe(false)
    expect(hasUsableRouteData({})).toBe(false)
  })

  it('zooms out further for longer routes', () => {
    const short = getRouteFocusSettings([
      [12.97, 77.59],
      [12.975, 77.595],
    ])
    const long = getRouteFocusSettings([
      [12.97, 77.59],
      [13.97, 78.59],
    ])
    expect(short.maxZoom).toBeGreaterThan(long.maxZoom)
    expect(getRouteFocusSettings([])).toEqual({ maxZoom: 12, duration: 0.8, padFactor: 0.35 })
  })
})

describe('customer tracking route summary', () => {
  function summary(order, coords = {}) {
    return useRouteSummary({
      activeMove: ref(order),
      warehouseCoords: ref(coords.warehouse || null),
      warehouseToPickupCoords: ref(coords.warehouseToPickup || []),
      pickupCoords: ref(coords.pickup || null),
      pickupToDestCoords: ref(coords.pickupToDest || []),
      destCoords: ref(coords.dest || null),
    })
  }

  it('names three stages and the full route when the order goes through a warehouse', () => {
    const s = summary(
      {
        warehouseName: 'North Hub',
        pickup: 'MG Road, Bengaluru',
        destination: 'Indiranagar, Bengaluru',
        status: 'pending',
      },
      { warehouse: [1, 1], pickup: [2, 2], dest: [3, 3] },
    )

    expect(s.routeStageLabels.value).toEqual(['Warehouse', 'Pickup', 'Destination'])
    expect(s.routeBlueprintLabel.value).toBe('North Hub → MG Road → Indiranagar')
    expect(s.routeLegendItems.value.map((i) => [i.key, i.dashed])).toEqual([
      ['warehouse-pickup', true],
      ['pickup-destination', true],
    ])
  })

  it('ticks the checklist up to the warehouse stage the order reached', () => {
    const s = summary({
      status: 'pending',
      warehouseSubstatus: 'PACKED',
      laborCount: 2,
      progress: 0,
    })

    expect(s.serviceChecklist.value.map((step) => step.done)).toEqual([
      false,
      true,
      true,
      true,
      false,
      false,
      false,
    ])
    expect(s.logColor('amber')).toBe('#f59e0b')
    expect(s.isWarehouseEvent('Packing completed')).toBe(true)
  })
})

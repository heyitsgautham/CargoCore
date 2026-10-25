import { beforeEach, describe, expect, it } from 'vitest'
import {
  buildDriverDeliveryMetrics,
  buildDriverOrderContext,
  buildDriverOrderRoutes,
  buildEtaTargets,
  buildPickupLocations,
  chooseMapCenter,
  chooseMapZoom,
  driverBusyReason,
  findBusyDriverIds,
  isDriverAssignable,
  mergeLiveMapOrders,
  placeCrises,
  withDeliveryCoords,
} from '@/LWD-views/Dispatcher/dashboard/dispatchMapData'
import {
  DRIVER_TRAIL_MAX_POINTS,
  DRIVER_TRAIL_RETENTION_MS,
  DRIVER_TRAIL_STORAGE_KEY,
  buildRouteHistoryTrails,
  extendDriverTrails,
  loadDriverTrailHistory,
  pruneDriverTrailHistory,
  saveDriverTrailHistory,
} from '@/LWD-views/Dispatcher/dashboard/driverTrails'
import {
  ETA_THRESHOLD_MINUTES,
  computeEtaCoverage,
  emptyEtaCoverage,
} from '@/LWD-views/Dispatcher/dashboard/etaCoverage'

const resolvePickup = (order) => (order.pickupLat ? [order.pickupLat, order.pickupLng] : null)
const resolveDestination = (order) =>
  order.deliveryLat ? [order.deliveryLat, order.deliveryLng] : null

describe('map orders', () => {
  it('lets active order data replace pending data and drops finished orders', () => {
    const merged = mergeLiveMapOrders(
      [
        { id: 1, status: 'CONFIRMED', note: 'pending copy' },
        { id: 2, status: 'CONFIRMED' },
      ],
      [
        { id: 1, status: 'IN_TRANSIT', note: 'active copy' },
        { id: 2, status: 'DELIVERED' },
        { id: 3, status: 'CANCELLED' },
      ],
    )

    expect(merged).toEqual([{ id: 1, status: 'IN_TRANSIT', note: 'active copy' }])
  })

  it('places pickups, unloading points and ETA targets only where coordinates resolve', () => {
    const orders = [
      {
        id: 7,
        pickupLat: 12.9,
        pickupLng: 77.6,
        deliveryLat: 13,
        deliveryLng: 77.7,
        priority: 'HIGH',
      },
      { id: 8, pickupAddr: 'No coords yet' },
    ]

    expect(buildPickupLocations(orders, resolvePickup)).toEqual([
      expect.objectContaining({ id: 7, lat: 12.9, lng: 77.6, locationLabel: 'Customer Pickup' }),
    ])
    expect(withDeliveryCoords(orders, resolveDestination)).toEqual([
      expect.objectContaining({ id: 7, resolvedDeliveryLat: 13, resolvedDeliveryLng: 77.7 }),
    ])
    expect(buildEtaTargets(orders, resolvePickup, resolveDestination).map((t) => t.id)).toEqual([
      'pickup-7',
      'delivery-7',
    ])
  })
})

describe('drivers', () => {
  const orders = [
    { id: 1, driverId: 'd1', status: 'CONFIRMED', deliveryAddr: 'MG Road' },
    { id: 2, driverId: 'd1', status: 'IN_TRANSIT', pickupAddr: 'Hub' },
    { id: 3, driverId: 'd2', status: 'DELIVERED' },
    { id: 4, status: 'CONFIRMED' },
  ]

  it('picks the most advanced order per driver and counts deliveries', () => {
    const context = buildDriverOrderContext(orders)
    expect(context.get('d1')).toMatchObject({ orderId: 2, status: 'IN_TRANSIT', label: 'Hub' })
    expect(context.get('d2')).toMatchObject({ orderId: 3, rank: 99 })

    const metrics = buildDriverDeliveryMetrics(orders)
    expect(metrics.get('d1')).toEqual({ delivered: 0, pending: 2 })
    expect(metrics.get('d2')).toEqual({ delivered: 1, pending: 0 })
  })

  it('treats drivers with unfinished orders as busy', () => {
    const busy = findBusyDriverIds(orders)
    expect([...busy]).toEqual(['d1'])

    expect(isDriverAssignable({ id: 'd2', statusColor: 'bg-green-500' }, busy)).toBe(true)
    expect(isDriverAssignable({ id: 'd1', statusColor: 'bg-green-500' }, busy)).toBe(false)
    expect(isDriverAssignable({ id: 'd3', statusColor: 'bg-gray-500' }, busy)).toBe(false)
    expect(driverBusyReason({ id: 'd1' }, busy)).toBe('Assigned')
    expect(driverBusyReason({ id: 'd3', maintenance: true }, busy)).toBe('Maintenance')
    expect(driverBusyReason({ id: 'd4', statusColor: 'bg-gray-500' }, busy)).toBe('Offline')
  })

  it('draws a route from each live driver to every unfinished order with an unloading point', () => {
    const routes = buildDriverOrderRoutes(
      [
        { driver_id: 'd1', driver_name: 'Ravi', latitude: 12.9, longitude: 77.6 },
        { driver_id: 'd2', latitude: null, longitude: null },
      ],
      [
        { id: 1, driverId: 'd1', status: 'ASSIGNED', deliveryLat: 13, deliveryLng: 77.7 },
        { id: 2, driverId: 'd1', status: 'DELIVERED', deliveryLat: 13, deliveryLng: 77.7 },
        { id: 3, driverId: 'd2', status: 'ASSIGNED', deliveryLat: 13, deliveryLng: 77.7 },
      ],
      resolveDestination,
    )

    expect(routes).toEqual([
      expect.objectContaining({
        id: 'route-d1-1',
        from: [12.9, 77.6],
        to: [13, 77.7],
        driverLocationLabel: '12.90000, 77.60000',
        destinationLabel: 'Order #1 unloading point',
      }),
    ])
  })
})

describe('map framing', () => {
  const base = { firstPickup: null, firstDestination: null, activeDrivers: [], hubs: [], zones: [] }

  it('centres on the dispatcher hub first and falls back through live data', () => {
    expect(chooseMapCenter({ ...base, scopedHub: { lat: 1, lng: 2 } })).toEqual([1, 2])
    expect(chooseMapCenter({ ...base, firstPickup: { lat: 3, lng: 4 } })).toEqual([3, 4])
    expect(
      chooseMapCenter({ ...base, activeDrivers: [{ latitude: 0 }, { latitude: 5, longitude: 6 }] }),
    ).toEqual([5, 6])
    expect(chooseMapCenter({ ...base, zones: [{ lat: 7, lng: 8 }] })).toEqual([7, 8])
    expect(chooseMapCenter(base)).toBeNull()
    expect(chooseMapZoom({ ...base, activeDrivers: [{}] })).toBe(12)
    expect(chooseMapZoom(base)).toBe(11)
  })

  it('spreads crises without coordinates around the first hub', () => {
    const placed = placeCrises(
      [{ id: 'a', lat: 10, lng: 20 }, { id: 'b' }, { id: 'c' }],
      [{ lat: 12, lng: 77 }],
      null,
    )

    expect(placed[0]).toEqual({ id: 'a', lat: 10, lng: 20 })
    expect(placed[1].lat).not.toBe(placed[2].lat)
    expect(Math.abs(placed[1].lat - 12)).toBeLessThan(0.1)
  })
})

describe('driver trails', () => {
  beforeEach(() => localStorage.clear())

  const driver = { driver_id: 'd1', driver_name: 'Ravi', latitude: 12.9, longitude: 77.6 }
  const noContext = new Map()

  it('adds a point when the driver moves and updates the last point when they stand still', () => {
    const t0 = Date.now()
    let history = extendDriverTrails({}, [driver], noContext, t0)
    history = extendDriverTrails(history, [driver], noContext, t0 + 1000)
    expect(history.d1).toHaveLength(1)
    expect(history.d1[0].ts).toBe(t0 + 1000)

    history = extendDriverTrails(history, [{ ...driver, latitude: 12.91 }], noContext, t0 + 2000)
    expect(history.d1).toHaveLength(2)

    const trails = buildRouteHistoryTrails(history, [driver])
    expect(trails[0]).toMatchObject({ driverId: 'd1', driverName: 'Ravi', pointCount: 2 })
    expect(buildRouteHistoryTrails(history, [])).toEqual([])
  })

  it('forgets samples older than six hours and caps each trail', () => {
    const now = Date.now()
    const old = { lat: 1, lng: 2, ts: now - DRIVER_TRAIL_RETENTION_MS - 1 }
    const many = Array.from({ length: DRIVER_TRAIL_MAX_POINTS + 5 }, (_, i) => ({
      lat: 1,
      lng: 2,
      ts: now - i,
    }))

    expect(pruneDriverTrailHistory({ d1: [old], d2: many, d3: 'bad' }, now)).toEqual({
      d2: many.slice(-DRIVER_TRAIL_MAX_POINTS),
    })
  })

  it('round-trips through localStorage and ignores a corrupt entry', () => {
    const history = { d1: [{ lat: 1, lng: 2, ts: Date.now() }] }
    saveDriverTrailHistory(history)
    expect(loadDriverTrailHistory()).toEqual(history)

    localStorage.setItem(DRIVER_TRAIL_STORAGE_KEY, '{not json')
    expect(loadDriverTrailHistory()).toEqual({})
  })
})

describe('ETA coverage', () => {
  const driver = { driver_id: 'd1', latitude: 12.97, longitude: 77.59, speed: 0 }

  it('reports no reachable stops when there are no targets', () => {
    const coverage = computeEtaCoverage([driver], [])
    expect(coverage.d1).toEqual(emptyEtaCoverage(driver))
    expect(coverage.d1.thresholdMinutes).toBe(ETA_THRESHOLD_MINUTES)
  })

  it('counts stops reachable inside the threshold and names the nearest one', () => {
    const coverage = computeEtaCoverage(
      [driver, { driver_id: 'd2', latitude: null, longitude: null }],
      [
        { id: 'pickup-1', kind: 'pickup', label: 'Pickup • Order #1', coords: [12.975, 77.595] },
        { id: 'delivery-1', kind: 'delivery', label: 'Unloading • Order #1', coords: [13.5, 78.2] },
      ],
    )

    expect(Object.keys(coverage)).toEqual(['d1'])
    expect(coverage.d1).toMatchObject({
      reachableCount: 1,
      nearestLabel: 'Pickup • Order #1',
      nearestKindLabel: 'pickup',
    })
    expect(coverage.d1.radiusMeters).toBeGreaterThanOrEqual(1500)
  })
})

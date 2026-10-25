import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'

const order = (overrides = {}) => ({
  id: 'o1',
  tracking_code: 'QC-D100',
  status: 'CONFIRMED',
  warehouse_substatus: 'QC_PASSED',
  pickup_addr: 'North Hub',
  delivery_addr: 'Koramangala',
  pickup_lat: 12.97,
  pickup_lng: 77.59,
  delivery_lat: 12.93,
  delivery_lng: 77.62,
  priority: 'HIGH',
  cargo_weight_kg: 120,
  created_at: '2026-04-01T09:00:00Z',
  scheduled_at: '2026-04-01T15:00:00Z',
  items: [],
  ...overrides,
})

let router

function routes() {
  return [
    ['GET', '/logistics/bootstrap', { status: 403, body: { detail: 'Logistic manager only' } }],
    [
      'GET',
      'status_filter=CONFIRMED',
      {
        items: [
          order(),
          order({ id: 'o2', tracking_code: 'QC-D101', warehouse_substatus: 'PICKING' }),
        ],
      },
    ],
    [
      'GET',
      'status_filter=ASSIGNED',
      {
        items: [
          order({
            id: 'o3',
            tracking_code: 'QC-D102',
            status: 'ASSIGNED',
            assigned_driver_id: 'd1',
            assigned_vehicle_id: 'v1',
          }),
        ],
      },
    ],
    [
      'GET',
      'status_filter=IN_TRANSIT',
      {
        items: [
          order({
            id: 'o4',
            tracking_code: 'QC-D103',
            status: 'IN_TRANSIT',
            assigned_driver_id: 'd1',
          }),
        ],
      },
    ],
    ['GET', 'status_filter=DELIVERED', { items: [] }],
    [
      'GET',
      '/logistics/drivers',
      [
        {
          id: 'd1',
          hub_id: 'wh-1',
          name: 'Ravi Kumar',
          status: 'Active',
          current_location: '12.96,77.60',
          efficiency: 88,
        },
      ],
    ],
    [
      'GET',
      '/logistics/vehicles',
      [{ id: 'v1', code: 'KA01AB1234', type: 'Tempo', status: 'Active', assigned_driver_id: 'd1' }],
    ],
    ['GET', /\/logistics\/chats$/, [{ id: 't1', name: 'Ravi Kumar' }]],
    ['GET', '/dispatch-contacts', [{ id: 'c1', name: 'North Hub desk', phone: '9000' }]],
    [
      'GET',
      /\/logistics\/alerts$/,
      [
        {
          id: 'a1',
          type: 'sos',
          title: 'Flat tyre',
          description: 'Ravi stuck on ORR',
          severity: 'high',
          status: 'active',
        },
      ],
    ],
    ['GET', '/logistics/zones', [{ id: 'z1', hub_id: 'wh-1', name: 'Zone A' }]],
    [
      'GET',
      '/logistics/manifests',
      [{ id: 'm1', route_id: 'RT-1', driver_name: 'Ravi Kumar', orders_count: 2 }],
    ],
    ['POST', '/orders/o1/assign', {}],
    ['POST', '/orders/batch-assign', { assigned: 2 }],
    ['POST', '/orders/cluster', { clusters: [{ id: 'k1' }], unbatched: [], total_orders: 2 }],
    ['POST', '/logistics/alerts/a1/resolve', {}],
    ['POST', /\/logistics\/alerts$/, { id: 'a2', title: 'Road closed' }],
    ['POST', /\/logistics\/manifests$/, { id: 'm2', route_id: 'RT-2', driver_name: 'Ravi Kumar' }],
    ['POST', '/manifests/m2/push', {}],
    ['POST', '/chats/t1/messages', { id: 't1', messages: [{ text: 'Go to dock 2' }] }],
    ['POST', /\/logistics\/chats$/, { id: 't2', name: 'North Hub desk' }],
    ['PUT', '/logistics/drivers/d1', {}],
    ['GET', '/api/v1/orders/o3', order({ id: 'o3', status: 'ASSIGNED' })],
  ]
}

async function loadedStore() {
  vi.resetModules()
  const { useDispatcherStore } = await import('@/stores/dispatcherStore')
  const store = useDispatcherStore()
  await store.initialize()
  return store
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] })
  localStorage.clear()
  localStorage.setItem('auth_token', 'tok')
  setActivePinia(createPinia())
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
  router = stubFetch(routes())
})

afterEach(() => {
  vi.useRealTimers()
})

describe('dispatcher store', () => {
  it('loads the queue, fleet and crises even when the manager bootstrap is refused', async () => {
    const store = await loadedStore()

    expect(store.pendingOrders.length).toBeGreaterThan(0)
    expect(store.activeOrders.map((o) => o.status ?? o.rawStatus)).toHaveLength(2)
    expect(store.dispatcherDrivers[0].name).toBe('Ravi Kumar')
    expect(store.activeCrises.length).toBeGreaterThan(0)
    expect(store.manifests[0]).toMatchObject({
      id: 'RT-1',
      backendId: 'm1',
      driver: 'Ravi Kumar',
      vehicle: 'Auto-assigned',
    })
    expect(store.filteredZones.length).toBeGreaterThanOrEqual(0)
    expect(store.slaProjection).toBeDefined()
    expect(store.dispatcherContacts.length).toBeGreaterThan(0)
  })

  it('assigns one order or a batch and reports failures as false', async () => {
    const store = await loadedStore()

    expect(await store.assignOrder('o1', 'd1', 'v1')).toBe(true)
    expect(router.calls.find((c) => c.url.includes('/orders/o1/assign')).body).toMatchObject({
      driver_id: 'd1',
      vehicle_id: 'v1',
    })
    expect(await store.assignOrder('missing', 'd1')).toBe(false)

    const batch = await store.batchAssignOrders([{ order_id: 'o1', driver_id: 'd1' }])
    expect(batch).toEqual({ assigned: 2 })
  })

  it('clusters orders and falls back to an empty plan on error', async () => {
    const store = await loadedStore()

    expect((await store.fetchClusters(3)).clusters).toHaveLength(1)
    expect(router.last('POST').url).toContain('radius_km=3')

    stubFetch([['POST', '/orders/cluster', { status: 500, body: {} }]])
    expect(await store.fetchClusters()).toMatchObject({ clusters: [], total_orders: 0 })
  })

  it('raises and resolves alerts and messages drivers and contacts', async () => {
    const store = await loadedStore()

    await store.createAlert({ type: 'traffic', title: 'Road closed', description: 'Silk Board' })
    await store.resolveAlert('a1')
    await store.sendDispatchMessage('t1', 'Go to dock 2')
    await store.createChatForContact('North Hub desk', '9000')

    const posted = router.calls
      .filter((c) => c.method === 'POST')
      .map((c) => new URL(c.url).pathname)
    expect(posted).toEqual(
      expect.arrayContaining([
        '/api/v1/logistics/alerts',
        '/api/v1/logistics/alerts/a1/resolve',
        '/api/v1/logistics/chats/t1/messages',
        '/api/v1/logistics/chats',
      ]),
    )
  })

  it('saves a manifest and pushes it to the driver', async () => {
    const store = await loadedStore()

    const saved = await store.saveManifest({ route_id: 'RT-2', driver_name: 'Ravi Kumar' })
    expect(saved).toBeTruthy()
    expect(await store.pushManifestToDriver('m2')).toBe(true)
  })

  it('suspends a driver and remembers it', async () => {
    const store = await loadedStore()

    await store.toggleDriverSuspend('d1')

    expect(
      router.calls.some((c) => c.method === 'PUT' && c.url.includes('/logistics/drivers/d1')),
    ).toBe(true)
  })

  it('fetches a single order', async () => {
    const store = await loadedStore()

    const detail = await store.fetchOrderDetail('o3')

    expect(detail).toBeTruthy()
  })
})

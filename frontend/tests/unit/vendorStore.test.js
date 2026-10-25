import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { normalizeInvoice, normalizeShipment } from '@/stores/vendor/payloads'
import { stubFetch } from '../helpers/fetchRouter'

const shipment = (overrides = {}) => ({
  id: 'uuid-s1',
  tracking_code: 'QC-V100',
  status: 'IN_TRANSIT',
  pickup_addr: 'North Hub',
  delivery_addr: 'Koramangala',
  created_at: '2026-04-01T09:00:00Z',
  scheduled_at: '2026-04-02T09:00:00Z',
  total_amount: 5000,
  ...overrides,
})

const routes = () => [
  ['GET', '/api/v1/rates', {}],
  [
    'GET',
    '/vendor/dashboard',
    {
      stats: { credit_balance: 2500 },
      invoices: {
        invoices: [
          {
            id: 'INV-1',
            tracking_code: 'QC-V100',
            order_id: 'uuid-s1',
            amount: 5000,
            paid: 0,
            status: 'Overdue',
            due_date: '2026-04-10',
          },
        ],
      },
    },
  ],
  [
    'GET',
    '/vendor/shipments',
    {
      shipments: [
        shipment(),
        shipment({ id: 'uuid-s2', tracking_code: 'QC-V101', status: 'DELIVERED' }),
      ],
    },
  ],
  [
    'GET',
    '/vendor/settings',
    { settings: { company_name: 'Acme', notification_prefs: { email: true } } },
  ],
  [
    'GET',
    '/vendor/damage-reports',
    {
      reports: [
        { id: 'DMG-9', order_id: 'QC-V100', description: 'Wet carton', status: 'reported' },
      ],
    },
  ],
  ['GET', '/vendor/team-members', [{ id: 'm1', name: 'Priya' }]],
  ['GET', '/vendor/api-keys', [{ id: 'k1', name: 'ERP' }]],
  [
    'GET',
    '/vendor/recurring-rules',
    [
      {
        id: 'r1',
        name: 'Weekly restock',
        frequency: 'weekly',
        route: 'A to B',
        details: '{}',
        active: true,
        next_run: '2026-04-08',
      },
    ],
  ],
  ['GET', '/vendor/bulk-uploads', [{ id: 'b1', filename: 'orders.csv' }]],
  [
    'GET',
    '/vendor/support-tickets',
    [{ id: 't1', subject: 'Late pickup', status: 'Open', replies: [] }],
  ],
  [
    'GET',
    '/api/v1/warehouses',
    { items: [{ id: 'wh-1', name: 'North Hub', address: '1 North Road' }] },
  ],
  ['GET', '/vendor/wallet', { balance: 2500 }],
  ['GET', /\/vendor\/notifications$/, [{ id: 'n1', title: 'Pickup scheduled', read: false }]],
  [
    'POST',
    /\/api\/v1\/orders$/,
    shipment({ id: 'uuid-s3', tracking_code: 'QC-V102', status: 'CONFIRMED' }),
  ],
  ['POST', '/vendor/invoices/uuid-s1/pay', { paid: 5000, status: 'Paid' }],
  ['POST', '/vendor/wallet/top-up', { balance: 3500 }],
  ['POST', /\/vendor\/team-members$/, { id: 'm2', name: 'Kiran' }],
  ['DELETE', '/vendor/team-members/m1', {}],
  ['POST', /\/vendor\/api-keys$/, { id: 'k2', name: 'WMS', key: 'ck_live_x' }],
  ['POST', '/vendor/api-keys/k1/revoke', {}],
  ['POST', /\/vendor\/recurring-rules$/, { id: 'r2' }],
  ['PUT', '/vendor/recurring-rules/r1', { id: 'r1' }],
  ['POST', '/vendor/recurring-rules/r1/toggle', { id: 'r1', active: false }],
  ['DELETE', '/vendor/recurring-rules/r1', {}],
  ['POST', '/vendor/recurring/estimate-cost', { distance_km: 12, estimated_cost: 940 }],
  ['POST', /\/vendor\/support-tickets$/, { id: 't2' }],
  ['POST', '/support-tickets/t1/reply', {}],
  ['POST', '/support-tickets/t1/resolve', {}],
  ['POST', '/orders/uuid-s1/cancel', shipment({ status: 'CANCELLED' })],
  ['PUT', '/vendor/settings', { settings: { company_name: 'Acme Logistics' } }],
]

let router

async function loadedStore() {
  vi.resetModules()
  const { useVendorStore } = await import('@/stores/vendorStore')
  const store = useVendorStore()
  await store.initializeVendorData()
  return store
}

beforeEach(() => {
  localStorage.clear()
  localStorage.setItem('auth_token', 'tok')
  setActivePinia(createPinia())
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
  router = stubFetch(routes())
})

describe('vendor payload mapping', () => {
  it('maps a shipment into the vendor table row', () => {
    const row = normalizeShipment(shipment())

    expect(row).toMatchObject({
      id: 'QC-V100',
      backendId: 'uuid-s1',
      statusKey: 'transit',
      status: 'In Transit',
      progress: 65,
    })
    expect(row.route).toBe('North Hub → Koramangala')
  })

  it('maps an invoice and defaults its status', () => {
    expect(
      normalizeInvoice({ id: 'INV-2', tracking_code: 'QC-1', amount: '10', paid: null }),
    ).toMatchObject({
      orderId: 'QC-1',
      amount: 10,
      paid: 0,
      status: 'Unpaid',
    })
  })
})

describe('vendor store', () => {
  it('loads every vendor screen in one initialisation', async () => {
    const store = await loadedStore()

    expect(store.initialized).toBe(true)
    expect(store.shipments.map((s) => s.id)).toEqual(['QC-V100', 'QC-V101'])
    expect(store.invoices[0].status).toBe('Overdue')
    expect(store.walletBalance).toBe(2500)
    expect(store.companySettings.companyName).toBe('Acme')
    // Settings and team members load in parallel; the team list must survive the settings reply.
    expect(store.companySettings.teamMembers).toHaveLength(1)
    expect(store.companySettings.apiKeys).toHaveLength(1)
    expect(store.recurringRules[0].name).toBe('Weekly restock')
    expect(store.tickets[0].subject).toBe('Late pickup')
    expect(store.warehouses[0].name).toBe('North Hub')
  })

  it('records the error when a screen fails to load', async () => {
    stubFetch([['GET', '/vendor/dashboard', { status: 503, body: { detail: 'Maintenance' } }]])
    vi.resetModules()
    const { useVendorStore } = await import('@/stores/vendorStore')
    const store = useVendorStore()

    await expect(store.initializeVendorData()).rejects.toThrow()
    expect(store.error).toBeTruthy()
  })

  it('books a shipment from a hub and refuses an unknown hub', async () => {
    const store = await loadedStore()

    await store.createShipment({
      pickupType: 'hub',
      pickupHub: 'North Hub',
      destination: 'Koramangala',
      destinationCity: 'Bengaluru',
      pincode: '560034',
      pickupDate: '2026-04-05',
      quoteBreakdown: { total: 3000, packingFee: 200, laborCharges: 500 },
      priority: 'Express',
      weight: 120,
    })
    const booking = router.calls.find(
      (c) => c.method === 'POST' && c.url.endsWith('/api/v1/orders'),
    )
    expect(booking.body).toMatchObject({
      order_type: 'VENDOR',
      warehouse_id: 'wh-1',
      priority: 'HIGH',
      base_amount: 2300,
      packing_amount: 200,
      labor_amount: 500,
      delivery_addr: 'Koramangala, Bengaluru, 560034',
    })

    await expect(
      store.createShipment({ pickupType: 'hub', pickupHub: 'Closed Hub' }),
    ).rejects.toThrow('not available')
  })

  it('pays an invoice and rolls back when payment fails', async () => {
    const store = await loadedStore()

    expect(await store.payInvoice('INV-1', 5000)).toBe(true)
    expect(store.invoices[0].status).toBe('Paid')

    store.invoices[0].paid = 0
    store.invoices[0].status = 'Overdue'
    stubFetch([['POST', '/pay', { status: 402, body: {} }]])
    expect(await store.payInvoice('INV-1', 100)).toBe(false)
    expect(store.invoices[0]).toMatchObject({ paid: 0, status: 'Overdue' })
    expect(await store.payInvoice('missing', 1)).toBe(false)
  })

  it('tops up the wallet but refuses a zero amount', async () => {
    const store = await loadedStore()

    expect(await store.addFunds(0)).toBe(false)
    expect(await store.addFunds(1000)).toBe(true)
    expect(router.calls.some((c) => c.url.endsWith('/vendor/wallet/top-up'))).toBe(true)
  })

  it('manages team members, API keys, recurring rules and tickets', async () => {
    const store = await loadedStore()

    await store.addTeamMember({ name: 'Kiran', email: 'kiran@example.com', role: 'Ops' })
    await store.removeTeamMember('m1')
    await store.generateApiKey('WMS')
    await store.revokeApiKey('k1')
    await store.addRecurringRule({
      name: 'Daily',
      frequency: 'daily',
      route: 'A to B',
      details: '{}',
      nextRun: '2026-04-06',
    })
    await store.updateRecurringRule('r1', { name: 'Weekly restock v2' })
    await store.toggleRecurringRule('r1')
    await store.deleteRecurringRule('r1')
    await store.addTicket({ subject: 'Damaged pallet', message: 'Two boxes crushed' })
    await store.replyTicket('t1', 'Any update?')
    await store.resolveTicket('t1')

    const writes = router.calls
      .filter((c) => c.method !== 'GET')
      .map((c) => `${c.method} ${new URL(c.url).pathname.replace('/api/v1/vendor', '')}`)
    expect(writes).toEqual([
      'POST /team-members',
      'DELETE /team-members/m1',
      'POST /api-keys',
      'POST /api-keys/k1/revoke',
      'POST /recurring-rules',
      'PUT /recurring-rules/r1',
      'POST /recurring-rules/r1/toggle',
      'DELETE /recurring-rules/r1',
      'POST /support-tickets',
      'POST /support-tickets/t1/reply',
      'POST /support-tickets/t1/resolve',
    ])
  })

  it('estimates a recurring run and cancels a shipment', async () => {
    const store = await loadedStore()

    const estimate = await store.estimateRecurringCost({
      hubId: 'wh-1',
      hubName: 'North Hub',
      destinationLat: 12.93,
      destinationLon: 77.62,
    })
    expect(estimate).toMatchObject({ estimated_cost: 940 })

    await store.cancelShipment('QC-V100', 'Customer moved')
    expect(router.last('POST').body).toEqual({ reason: 'Customer moved' })
  })

  it('prices a pallet quote and counts unread notifications', async () => {
    const store = await loadedStore()

    const quote = store.calculateQuote(2, 300, 2, true, [{ qty: 3, unitPrice: 50 }])
    expect(quote).toEqual({
      baseTransport: 264,
      laborCharges: 500,
      packingFee: 200,
      materialsCost: 150,
      total: 1114,
    })
    expect(store.calculateQuote(1, 0, 0, false).total).toBe(120)
    expect(store.unreadNotificationsCount).toBeGreaterThan(0)
  })
})

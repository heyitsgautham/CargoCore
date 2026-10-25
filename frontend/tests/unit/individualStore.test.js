import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'

const backendOrder = (overrides = {}) => ({
  id: 'uuid-1',
  tracking_code: 'QC-1001',
  status: 'CONFIRMED',
  warehouse_id: 'wh-1',
  warehouse_substatus: 'AWAITING_PICK',
  pickup_addr: '14 MG Road',
  delivery_addr: '22 Indiranagar',
  created_at: '2026-04-01T09:00:00Z',
  scheduled_at: '2026-04-03T10:00:00Z',
  total_amount: 2400,
  items: [],
  ...overrides,
})

async function freshStore() {
  vi.resetModules()
  const { useIndividualStore } = await import('@/stores/individualStore')
  return useIndividualStore()
}

beforeEach(() => {
  localStorage.clear()
  localStorage.setItem('auth_token', 'tok')
  localStorage.setItem(
    'auth_user',
    JSON.stringify({ name: 'Asha Rao', email: 'asha@example.com', role: 'INDIVIDUAL' }),
  )
  setActivePinia(createPinia())
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

describe('individual store reads', () => {
  it('loads orders, maps them and filters by status', async () => {
    const router = stubFetch([
      ['GET', '/api/v1/rates', {}],
      [
        'GET',
        '/api/v1/orders?',
        {
          items: [
            backendOrder(),
            backendOrder({ id: 'uuid-2', tracking_code: 'QC-1002', status: 'DELIVERED' }),
          ],
        },
      ],
    ])
    const store = await freshStore()

    const result = await store.fetchOrders('delivered')

    expect(result.success).toBe(true)
    expect(router.last('GET').url).toContain('status_filter=DELIVERED')
    expect(store.orders.map((o) => o.status)).toEqual(['pending', 'delivered'])
    expect(store.deliveredOrders).toHaveLength(1)
    expect(store.activeOrders.length + store.pendingOrders.length).toBeGreaterThan(0)
  })

  it('records the server error when orders fail to load', async () => {
    stubFetch([['GET', '/api/v1/orders?', { status: 500, body: { detail: 'Database down' } }]])
    const store = await freshStore()

    const result = await store.fetchOrders()

    expect(result).toEqual({ success: false, message: 'Database down' })
    expect(store.ordersError).toBe('Database down')
    expect(store.ordersLoading).toBe(false)
  })

  it('reports a connection error when fetch throws', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    const store = await freshStore()

    expect((await store.fetchOrders()).message).toBe('Error connecting to the server.')
    expect((await store.fetchProfile()).success).toBe(false)
    expect((await store.fetchPaymentsSummary()).success).toBe(false)
  })

  it('loads the profile, payments, quotes, damage reports and wallet', async () => {
    stubFetch([
      [
        'GET',
        '/customer/profile',
        {
          profile: { name: 'Asha R', email: 'a@x.com', phone: '99' },
          address: 'MG Road',
          language: 'ta',
          notification_prefs: { push: true, sms: false },
        },
      ],
      [
        'GET',
        '/customer/payments',
        {
          total_paid: 500,
          records: [
            {
              id: 'p1',
              tracking_code: 'QC-1001',
              amount: 500,
              mode: 'UPI',
              status: 'completed',
              created_at: '2026-04-01',
            },
          ],
        },
      ],
      [
        'GET',
        '/customer/quotes',
        {
          quotes: [
            { id: 'q1', cargo_type: 'Furniture', from_location: 'A', to_location: 'B', total: 900 },
          ],
        },
      ],
      [
        'GET',
        '/customer/damage-reports',
        {
          reports: [
            { id: 'DMG-1', order_id: 'QC-1001', description: 'Scratch', status: 'reported' },
          ],
        },
      ],
      ['GET', '/customer/wallet', { balance: 1200, pending_transport_charge: 150 }],
      [
        'GET',
        '/customer/notifications',
        [{ id: 'n1', title: 'Hi', message: 'Booked', read: false }],
      ],
    ])
    const store = await freshStore()

    await store.fetchProfile()
    await store.fetchPaymentsSummary()
    await store.fetchQuotes()
    await store.fetchDamageReports()
    await store.fetchWalletBalance()
    await store.fetchNotifications()

    expect(store.user.name).toBe('Asha R')
    expect(store.user.smsAlerts).toBe(false)
    expect(store.payments[0]).toMatchObject({ orderId: 'QC-1001', amount: 500 })
    expect(store.quotes[0]).toMatchObject({ id: 'q1', cargoType: 'Furniture' })
    expect(store.damageReports[0].id).toBe('DMG-1')
    expect(store.walletBalance).toBe(1200)
    expect(store.pendingTransportCharge).toBe(150)
    expect(store.unreadNotificationsCount).toBe(1)
  })

  it('keeps only active hubs from the warehouse list', async () => {
    stubFetch([
      [
        'GET',
        '/api/v1/warehouses',
        {
          items: [
            { id: 1, name: 'North' },
            { id: 2, name: 'Closed', is_active: false },
          ],
        },
      ],
    ])
    const store = await freshStore()

    const hubs = await store.fetchWarehouses()

    expect(hubs).toEqual([{ id: '1', name: 'North', address: '' }])
  })

  it('stores the assignment preview and clears it on failure', async () => {
    const router = stubFetch([
      ['GET', '/assignment-preview', { warehouse_id: 5, warehouse_name: 'North' }],
    ])
    const store = await freshStore()

    await store.fetchOrderAssignmentPreview('wh 5')
    expect(router.last('GET').url).toContain('warehouse_id=wh%205')
    expect(store.assignmentPreview.warehouse_id).toBe('5')

    stubFetch([['GET', '/assignment-preview', { status: 409, body: { detail: 'No hub' } }]])
    expect(await store.fetchOrderAssignmentPreview()).toBeNull()
    expect(store.assignmentPreviewError).toBe('No hub')
  })
})

describe('individual store writes', () => {
  it('creates an order, attaches packing materials and records the payment', async () => {
    const router = stubFetch([
      ['POST', /\/api\/v1\/orders$/, backendOrder({ id: 'uuid-9', tracking_code: 'QC-9009' })],
      ['POST', '/orders/uuid-9/items', []],
      ['GET', '/customer/dashboard', {}],
    ])
    const store = await freshStore()

    const created = await store.createOrder({
      pickup: '14 MG Road',
      destination: '22 Indiranagar',
      vehicleType: 'tempo',
      laborCount: 2,
      cost: { base: 1000, total: 2400 },
      paymentMode: 'ONLINE',
      paymentAmount: 500,
      paymentMethod: 'UPI',
      paymentRef: 'pay_123',
      date: '2026-04-03',
      materialItems: [{ sku: 'PKG-BOX', name: 'Box', quantity: 4 }],
    })

    const orderCall = router.calls.find(
      (c) => c.method === 'POST' && c.url.endsWith('/api/v1/orders'),
    )
    expect(orderCall.body).toMatchObject({
      order_type: 'INDIVIDUAL',
      total_amount: 2400,
      initial_payment_amount: 500,
      initial_payment_mode: 'ONLINE',
    })
    expect(router.calls.find((c) => c.url.includes('/items')).body).toEqual([
      { sku: 'PKG-BOX', quantity: 4, box_count: null, estimated_volume: null },
    ])
    expect(created.trackingCode).toBe('QC-9009')
    expect(store.orders[0].trackingCode).toBe('QC-9009')
    expect(store.payments[0]).toMatchObject({ id: 'pay_123', amount: 500 })
    expect(store.notifications[0].title).toBe('Order Created')
  })

  it('does not charge a cash-on-delivery booking up front', async () => {
    const router = stubFetch([
      ['POST', /\/api\/v1\/orders$/, backendOrder()],
      ['GET', '/customer/dashboard', {}],
    ])
    const store = await freshStore()

    await store.createOrder({ cost: { total: 999 }, paymentMode: 'COD', paymentAmount: 999 })

    expect(router.calls.find((c) => c.method === 'POST').body.initial_payment_amount).toBe(0)
    expect(store.payments).toHaveLength(0)
  })

  it('surfaces the backend error when booking fails', async () => {
    stubFetch([
      [
        'POST',
        /\/api\/v1\/orders$/,
        { status: 409, body: { detail: 'No active warehouses available for assignment' } },
      ],
    ])
    const store = await freshStore()

    await expect(store.createOrder({ cost: { total: 100 } })).rejects.toThrow(
      'No active warehouses',
    )
  })

  it('cancels an order remotely and refreshes it', async () => {
    stubFetch([
      ['GET', '/api/v1/orders?', { items: [backendOrder()] }],
      [
        'POST',
        '/orders/uuid-1/cancel',
        backendOrder({ status: 'CANCELLED', cancel_reason: 'Plans changed' }),
      ],
      ['GET', '/customer/wallet', { balance: 2400 }],
      ['GET', '/customer/tracking', { orders: [] }],
    ])
    const store = await freshStore()
    await store.fetchOrders()

    const result = await store.cancelOrderRemote('QC-1001', 'Plans changed')

    expect(result.success).toBe(true)
    expect(result.order.status).toBe('cancelled')
    expect(store.walletBalance).toBe(2400)
  })

  it('saves profile and settings and tidies up the stored user', async () => {
    stubFetch([
      ['PUT', '/api/v1/auth/me', { name: 'Asha Rao', email: 'asha@example.com', phone: '98' }],
      [
        'PUT',
        '/customer/settings',
        { settings: { language: 'hindi', currency: 'USD', default_payment: 'cod' } },
      ],
      ['GET', '/customer/settings', { settings: { language: 'ta' } }],
    ])
    const store = await freshStore()

    expect(
      (await store.saveProfileRemote({ name: 'Asha Rao', phone: '98', address: 'Home' })).success,
    ).toBe(true)
    expect(JSON.parse(localStorage.getItem('auth_user')).phone).toBe('98')

    await store.saveSettingsRemote({ language: 'hi' })
    expect(store.user.language).toBe('hi')
    expect(store.user.currency).toBe('USD')
    expect(store.user.paymentDefault).toBe('COD')

    await store.fetchSettings()
    expect(store.user.language).toBe('ta')
  })

  it('pays through the wallet or the gateway depending on the mode', async () => {
    const router = stubFetch([
      ['GET', '/api/v1/orders?', { items: [backendOrder()] }],
      ['POST', '/wallet-pay', {}],
      ['POST', '/orders/uuid-1/pay', {}],
    ])
    const store = await freshStore()
    await store.fetchOrders()

    await store.makePayment('QC-1001', 500, 'Cargo Core Wallet')
    await store.makePayment('QC-1001', 300, 'UPI', false, 'pay_9')
    await store.makePayment('QC-1001', 100, 'Card', true)

    expect(
      router.calls.filter((c) => c.method === 'POST').map((c) => c.url.split('/').at(-1)),
    ).toEqual(['wallet-pay', 'pay'])
    expect(store.payments.map((p) => p.status)).toEqual(['simulated', 'completed', 'completed'])
  })

  it('marks notifications read and clears them', async () => {
    stubFetch([
      [
        'GET',
        '/customer/notifications',
        [
          { id: 'n1', read: false },
          { id: 'n2', read: false },
        ],
      ],
      ['PUT', '/customer/notifications/n1', {}],
      ['POST', '/mark-all-read', {}],
      ['DELETE', '/customer/notifications', {}],
    ])
    const store = await freshStore()
    await store.fetchNotifications()

    await store.markNotificationRead('n1')
    expect(store.unreadNotificationsCount).toBe(1)
    await store.markAllNotificationsRead()
    expect(store.unreadNotificationsCount).toBe(0)
    await store.clearNotifications()
    expect(store.notifications).toHaveLength(0)
  })
})

describe('individual store local helpers', () => {
  it('prices a move from distance, crew, packing and vehicle', async () => {
    stubFetch([])
    const store = await freshStore()

    const quote = store.calculateQuote(20, 2, true, 300, 'tempo')

    expect(quote.base).toBe(800)
    expect(quote.labor).toBe(1600)
    expect(quote.packing).toBe(160)
    expect(quote.platformFee).toBe(249)
    expect(quote.total).toBe(
      quote.base +
        quote.labor +
        quote.packing +
        quote.vehicle +
        quote.materials +
        quote.platformFee +
        quote.taxes,
    )
  })

  it('applies the minimum charge and rate overrides', async () => {
    stubFetch([])
    const store = await freshStore()

    expect(store.calculateQuote(1, 0, false, 0, 'mini-truck').base).toBe(500)
    expect(
      store.calculateQuote(10, 1, false, 0, 'hcv', {
        individualDistanceRates: { hcv: 100 },
        individualBookingFee: 0,
        individualLaborRate: 1000,
      }),
    ).toMatchObject({ base: 1000, labor: 1000 })
  })

  it('manages addresses, quotes, ratings and the AI prefill locally', async () => {
    stubFetch([['GET', '/api/v1/orders?', { items: [backendOrder()] }]])
    const store = await freshStore()
    await store.fetchOrders()

    const before = store.savedAddresses.length
    store.saveAddress({ label: 'Office', address: 'Tech Park' })
    expect(store.savedAddresses).toHaveLength(before + 1)
    store.deleteAddress(store.savedAddresses.at(-1).id)
    expect(store.savedAddresses).toHaveLength(before)

    store.addQuote({ cargoType: 'Boxes', total: 100 })
    expect(store.quotes[0].cargoType).toBe('Boxes')

    store.submitRating('QC-1001', 5, 'Great')
    expect(store.orders[0].rating).toBe(5)

    store.setAiPrefill({ rooms: 2 })
    expect(store.aiPrefill).toEqual({ rooms: 2 })
    store.clearAiPrefill()
    expect(store.aiPrefill).toBeNull()

    store.updateProfile({ name: 'New Name' })
    expect(store.userInitials).toBe('NN')
  })
})

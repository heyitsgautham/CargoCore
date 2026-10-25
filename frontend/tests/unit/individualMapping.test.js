import { beforeEach, describe, expect, it } from 'vitest'
import {
  normalizeCurrencySetting,
  normalizeCustomerSettings,
  normalizeLanguageSetting,
  normalizePaymentSetting,
  syncStoredAuthUser,
} from '@/stores/individual/customerSettings'
import {
  buildTransportLog,
  fallbackPackingSku,
  mapQuote,
  normalizeBackendStatus,
  normalizeTrackingOrder,
} from '@/stores/individual/orderMapping'

const events = (log) => log.map((entry) => entry.event)

describe('customer settings', () => {
  it('maps language names and codes, defaulting to English', () => {
    expect(normalizeLanguageSetting('Tamil')).toBe('ta')
    expect(normalizeLanguageSetting(' HI ')).toBe('hi')
    expect(normalizeLanguageSetting('klingon')).toBe('en')
  })

  it('maps currency and payment preferences', () => {
    expect(normalizeCurrencySetting('usd ($)')).toBe('USD')
    expect(normalizeCurrencySetting('Euro EUR')).toBe('EUR')
    expect(normalizeCurrencySetting(null)).toBe('INR')
    expect(normalizePaymentSetting('Partial advance')).toBe('Partial')
    expect(normalizePaymentSetting('cod')).toBe('COD')
    expect(normalizePaymentSetting('Cash on delivery')).toBe('COD')
    expect(normalizePaymentSetting('')).toBe('Full Payment')
  })

  it('fills notification and privacy defaults', () => {
    const settings = normalizeCustomerSettings({
      notification_prefs: { sms: false },
      privacy_prefs: { marketing: true },
    })

    expect(settings.notification_prefs).toEqual({
      push: true,
      sms: false,
      email: true,
      geofence: true,
      promo: false,
    })
    expect(settings.privacy_prefs).toEqual({ location: true, analytics: true, marketing: true })
    expect(settings.language).toBe('en')
  })

  describe('syncStoredAuthUser', () => {
    beforeEach(() => localStorage.clear())

    it('merges a patch into the stored auth user', () => {
      localStorage.setItem('auth_user', JSON.stringify({ id: 1, name: 'Old' }))
      syncStoredAuthUser({ name: 'New' })
      expect(JSON.parse(localStorage.getItem('auth_user'))).toEqual({ id: 1, name: 'New' })
    })

    it('starts from an empty user when none is stored', () => {
      syncStoredAuthUser({ language: 'ta' })
      expect(JSON.parse(localStorage.getItem('auth_user'))).toEqual({ language: 'ta' })
    })
  })
})

describe('normalizeBackendStatus', () => {
  it.each([
    ['DRAFT', 'pending'],
    ['CONFIRMED', 'pending'],
    ['ASSIGNED', 'dispatched'],
    ['IN_TRANSIT', 'in-transit'],
    ['DELIVERED', 'delivered'],
    ['CLOSED', 'delivered'],
    ['CANCELLED', 'cancelled'],
    ['ON_HOLD', 'on_hold'],
  ])('maps %s to %s', (raw, ui) => {
    expect(normalizeBackendStatus(raw)).toBe(ui)
  })
})

describe('buildTransportLog', () => {
  const base = { created_at: '2026-04-01T09:00:00Z', warehouse_id: 'wh-1' }

  it('walks a hub order through every warehouse stage', () => {
    const log = buildTransportLog({ ...base, status: 'IN_TRANSIT' }, 'in-transit', 'DISPATCHED')

    expect(events(log)).toEqual([
      'Order created',
      'Order confirmed',
      'Queued for Picking',
      'Picking started',
      'Picking completed',
      'Packing started',
      'Packing completed',
      'Quality check passed',
      'Ready for dispatch',
      'Dispatched from warehouse',
      'Driver assigned',
      'Shipment in transit',
    ])
  })

  it('stops at the current warehouse stage', () => {
    const log = buildTransportLog({ ...base, status: 'CONFIRMED' }, 'pending', 'PICKING')

    expect(events(log)).toContain('Picking started')
    expect(events(log)).not.toContain('Picking completed')
  })

  it('flags orders on hold', () => {
    expect(
      events(buildTransportLog({ ...base, status: 'CONFIRMED' }, 'pending', 'ON_HOLD')),
    ).toContain('Order On Hold')
  })

  it('skips warehouse steps for direct transport', () => {
    const log = buildTransportLog(
      { created_at: base.created_at, status: 'IN_TRANSIT', packing_amount: 0 },
      'in-transit',
      '',
    )

    expect(events(log)).toContain('Driver assigned')
    expect(events(log)).toContain('Driver en route to pickup')
    expect(events(log)).not.toContain('Queued for Picking')
  })

  it('ends with delivery or cancellation', () => {
    expect(
      events(buildTransportLog({ ...base, status: 'DELIVERED' }, 'delivered', 'DISPATCHED')).at(-1),
    ).toBe('Delivery completed')
    expect(
      events(buildTransportLog({ ...base, status: 'CANCELLED' }, 'cancelled', '')).at(-1),
    ).toBe('Order Cancelled')
  })

  it('shows N/A when the order has no creation time', () => {
    expect(buildTransportLog({ status: 'DRAFT' }, 'pending', '')[0].time).toBe('N/A')
  })
})

describe('normalizeTrackingOrder', () => {
  const order = {
    id: 'uuid-1',
    tracking_code: 'QC-1001',
    status: 'DELIVERED',
    warehouse_id: 42,
    warehouse_substatus: 'DISPATCHED',
    pickup_addr: 'A',
    delivery_addr: 'B',
    created_at: '2026-04-01T09:00:00Z',
    delivered_at: '2026-04-02T10:00:00Z',
    total_amount: '1999',
    base_amount: 500,
    paid_amount: '1999',
    pod_photos: ['p.jpg'],
    delivery_notes: 'Delivered to: Ravi',
    cancel_reason: null,
  }

  it('maps ids, status, money and proof of delivery', () => {
    const mapped = normalizeTrackingOrder(order)

    expect(mapped).toMatchObject({
      id: 'QC-1001',
      backendId: 'uuid-1',
      status: 'delivered',
      warehouseId: '42',
      paymentStatus: 'paid',
      paidAmount: 1999,
      cancellation: null,
    })
    expect(mapped.cost.total).toBe(1999)
    expect(mapped.pod.signedBy).toBe('Ravi')
    expect(mapped.transportLog.at(-1).event).toBe('Delivery completed')
  })

  it('prefers ui_status and records cancellations', () => {
    const mapped = normalizeTrackingOrder({
      ...order,
      ui_status: 'cancelled',
      cancel_reason: 'Moved dates',
      cancellation_fee: 200,
    })

    expect(mapped.status).toBe('cancelled')
    expect(mapped.pod).toBeNull()
    expect(mapped.cancellation).toMatchObject({ reason: 'Moved dates', fee: 200 })
  })

  it('falls back to the uuid and TBD values when fields are missing', () => {
    const mapped = normalizeTrackingOrder({
      id: 7,
      status: 'DRAFT',
      created_at: '2026-04-01T09:00:00Z',
    })

    expect(mapped.id).toBe('7')
    expect(mapped.timeWindow).toBe('TBD')
    expect(mapped.cargoType).toBe('Household Goods')
    expect(mapped.paymentStatus).toBe('pending')
  })
})

describe('quotes and packing SKUs', () => {
  it('renames quote fields for the quotes screen', () => {
    expect(
      mapQuote({
        id: 'q1',
        cargo_type: 'Furniture',
        from_location: 'X',
        to_location: 'Y',
        labor_count: 2,
        total: 900,
      }),
    ).toMatchObject({
      id: 'q1',
      cargoType: 'Furniture',
      from: 'X',
      to: 'Y',
      laborCount: 2,
      total: 900,
    })
  })

  it('builds a short upper-case SKU from a material name', () => {
    expect(fallbackPackingSku('bubbleWrap roll')).toBe('BUBBLE-WRA')
    expect(fallbackPackingSku('  Box  ')).toBe('BOX')
    expect(fallbackPackingSku()).toBe('')
  })
})

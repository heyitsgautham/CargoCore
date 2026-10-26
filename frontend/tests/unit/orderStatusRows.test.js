import { describe, expect, it } from 'vitest'
import {
  STATUS_TRANSITIONS,
  formatTimeOnly,
  mapStatusLabel,
  mapStatusToUI,
  toUiOrder,
} from '@/LWD-views/Dispatcher/orderStatus/orderRows'

describe('order status board rows', () => {
  it('maps backend statuses to board keys and labels', () => {
    expect(mapStatusToUI('CONFIRMED')).toBe('ready')
    expect(mapStatusToUI('IN_TRANSIT')).toBe('in-transit')
    expect(mapStatusToUI('ON_HOLD')).toBe('on-hold')
    expect(mapStatusToUI(null)).toBe('ready')
    expect(mapStatusLabel('ASSIGNED')).toBe('Dispatched')
    expect(mapStatusLabel(undefined)).toBe('Ready')
    expect(STATUS_TRANSITIONS.delivered.backendStatus).toBe('DELIVERED')
  })

  it('shows times only and passes through values it cannot parse', () => {
    expect(formatTimeOnly('—')).toBe('—')
    expect(formatTimeOnly('soon')).toBe('soon')
    expect(formatTimeOnly('2026-10-26T10:00:00')).toMatch(/10[:.]00/)
  })

  it('builds a row with defaults and a proof of delivery time', () => {
    const row = toUiOrder({
      id: 'o1',
      trackingCode: 'QC-1',
      status: 'DELIVERED',
      deliveredAt: '2026-10-26T10:00:00',
      pod: { signedBy: 'Asha' },
    })
    expect(row).toMatchObject({
      id: 'QC-1',
      backendId: 'o1',
      status: 'delivered',
      statusLabel: 'Delivered',
      slaStatus: 'Pending',
      escalated: false,
      pod: { signedBy: 'Asha' },
    })
    expect(row.pod.time).toBe(new Date('2026-10-26T10:00:00').toLocaleString())
    expect(toUiOrder({ id: 'o2', status: 'CONFIRMED' }).pod).toBeNull()
  })
})

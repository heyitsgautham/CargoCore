import { describe, expect, it } from 'vitest'
import {
  formatStatusLabel,
  isRecurringShipment,
  parseStatusKey,
  routeSummary,
  safeDateLabel,
  safeDateTimeLabel,
  statusProgress,
} from '@/stores/vendor/shipmentFormat'

describe('parseStatusKey', () => {
  it.each([
    ['PICKING', 'warehouse'],
    ['qc_passed', 'warehouse'],
    ['ASSIGNED', 'transit'],
    ['IN_TRANSIT', 'transit'],
    ['OUT_FOR_DELIVERY', 'delivery'],
    ['DELIVERED', 'delivered'],
    ['closed', 'delivered'],
    ['CANCELLED', 'cancelled'],
    ['CONFIRMED', 'pending'],
    [null, 'pending'],
  ])('maps %s to %s', (status, key) => {
    expect(parseStatusKey(status)).toBe(key)
  })
})

describe('status label and progress', () => {
  it('labels every key and falls back to Pending', () => {
    expect(formatStatusLabel('warehouse')).toBe('In Warehouse')
    expect(formatStatusLabel('delivery')).toBe('Out for Delivery')
    expect(formatStatusLabel('mystery')).toBe('Pending')
  })

  it('reports progress along the delivery pipeline', () => {
    expect(
      ['pending', 'warehouse', 'transit', 'delivery', 'delivered'].map(statusProgress),
    ).toEqual([15, 35, 65, 85, 100])
    expect(statusProgress('cancelled')).toBe(0)
    expect(statusProgress('unknown')).toBe(0)
  })
})

describe('date labels', () => {
  it('formats valid dates in en-US short form', () => {
    expect(safeDateLabel('2026-04-05T10:00:00Z')).toMatch(/^Apr 0[45], 2026$/)
    expect(safeDateTimeLabel('2026-04-05T10:30:00')).toMatch(/^Apr 05, 2026, \d{2}:30 (AM|PM)$/)
  })

  it('returns the fallback for empty values and echoes unparseable ones', () => {
    expect(safeDateLabel(null)).toBe('TBD')
    expect(safeDateLabel('', 'Not set')).toBe('Not set')
    expect(safeDateLabel('next week')).toBe('next week')
    expect(safeDateTimeLabel(undefined)).toBe('TBD')
    expect(safeDateTimeLabel('soon')).toBe('soon')
  })
})

describe('shipment helpers', () => {
  it('summarises a route with placeholders for missing ends', () => {
    expect(routeSummary('Chennai', 'Bengaluru')).toBe('Chennai → Bengaluru')
    expect(routeSummary('', null)).toBe('Origin → Destination')
  })

  it('detects recurring shipments from flags or the run marker in notes', () => {
    expect(isRecurringShipment({ recurring_rule_id: 'r1' })).toBe(true)
    expect(isRecurringShipment({ is_recurring: true })).toBe(true)
    expect(isRecurringShipment({ delivery_notes: 'RECURRING_RULE:r1|RUN:2026-04-20' })).toBe(true)
    expect(isRecurringShipment({ delivery_notes: 'RECURRING_RULE:r1' })).toBe(false)
    expect(isRecurringShipment({})).toBe(false)
  })
})

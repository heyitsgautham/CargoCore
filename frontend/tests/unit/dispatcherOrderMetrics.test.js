import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  driverStatusColor,
  generateAvatar,
  isDispatcherVisiblePendingOrder,
  isRecurringOrder,
  normalizeCargoMetric,
  parseCoordinate,
  parseMetric,
  resolveCargoVolume,
  resolveCargoWeight,
  roundMetric,
} from '@/stores/dispatcher/orderMetrics'

describe('driver display helpers', () => {
  it('colours active, idle and unknown drivers', () => {
    expect(driverStatusColor('On Route')).toBe('bg-green-500')
    expect(driverStatusColor('on_break')).toBe('bg-yellow-500')
    expect(driverStatusColor('offline')).toBe('bg-gray-500')
    expect(driverStatusColor(null)).toBe('bg-gray-500')
  })

  it('builds an initials avatar URL from the name, then the id', () => {
    expect(generateAvatar('Ravi Kumar', 'd1')).toContain('seed=Ravi%20Kumar')
    expect(generateAvatar('', 'd1')).toContain('seed=d1')
    expect(generateAvatar()).toContain('seed=driver')
  })
})

describe('number parsing', () => {
  it('parses finite numbers and rejects blanks and junk', () => {
    expect(parseCoordinate('13.08')).toBe(13.08)
    expect(parseCoordinate('')).toBeNull()
    expect(parseCoordinate('north')).toBeNull()
    expect(parseMetric(0)).toBe(0)
    expect(parseMetric(undefined)).toBeNull()
  })

  it('rounds to two decimals and drops non-positive cargo metrics', () => {
    expect(roundMetric(1.23456)).toBe(1.23)
    expect(roundMetric(null)).toBeNull()
    expect(normalizeCargoMetric(0)).toBeNull()
    expect(normalizeCargoMetric(-2)).toBeNull()
    expect(normalizeCargoMetric(2.555)).toBe(2.56)
  })
})

describe('cargo metrics', () => {
  it('reads weight from the first field that is present', () => {
    expect(resolveCargoWeight({ cargo_weight_kg: '120.456' })).toBe(120.46)
    expect(resolveCargoWeight({ weight: 80 })).toBe(80)
    expect(resolveCargoWeight({ total_weight: 0 })).toBeNull()
    expect(resolveCargoWeight({})).toBeNull()
  })

  it('reads volume directly or sums item estimates', () => {
    expect(resolveCargoVolume({ cargo_volume_m3: 3.5 })).toBe(3.5)
    expect(
      resolveCargoVolume({ items: [{ estimated_volume: 0.4 }, { estimated_volume: '0.35' }, {}] }),
    ).toBe(0.75)
    expect(resolveCargoVolume({ items: [] })).toBeNull()
  })
})

describe('recurring order visibility', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-04-20T09:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const recurring = (scheduledAt) => ({
    delivery_notes: 'RECURRING_RULE:r1|RUN:x',
    scheduled_at: scheduledAt,
  })

  it('recognises recurring runs from either notes field', () => {
    expect(isRecurringOrder({ deliveryNotes: 'RECURRING_RULE:r|RUN:1' })).toBe(true)
    expect(isRecurringOrder({ delivery_notes: 'one-off' })).toBe(false)
    expect(isRecurringOrder(null)).toBe(false)
  })

  it('always shows one-off orders and recurring orders without a usable date', () => {
    expect(isDispatcherVisiblePendingOrder({ scheduled_at: '2030-01-01' })).toBe(true)
    expect(isDispatcherVisiblePendingOrder(recurring(null))).toBe(true)
    expect(isDispatcherVisiblePendingOrder(recurring('not a date'))).toBe(true)
  })

  it('shows recurring runs up to tomorrow and hides later ones', () => {
    expect(isDispatcherVisiblePendingOrder(recurring('2026-04-20T15:00:00Z'))).toBe(true)
    expect(isDispatcherVisiblePendingOrder(recurring('2026-04-21T23:00:00Z'))).toBe(true)
    expect(isDispatcherVisiblePendingOrder(recurring('2026-04-22T00:30:00Z'))).toBe(false)
  })
})

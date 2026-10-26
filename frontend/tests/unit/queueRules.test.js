import { describe, expect, it } from 'vitest'
import {
  deriveFeasibility,
  evaluateDispatchFeasibility,
  formatCapacityValue,
  formatOrderWeight,
  getPriorityClass,
  getTimeRemaining,
  isDeadlineCritical,
  orderAllowsDirectVehicleSelection,
} from '@/LWD-views/Dispatcher/pendingQueue/queueRules'

const ready = { id: 'o1', readyForDispatch: true, vehicleId: 'v1', weight: 500, volume: 4 }

describe('pending dispatch queue rules', () => {
  it('passes an order that is ready, fits and has a driver available', () => {
    expect(evaluateDispatchFeasibility(ready, 2)).toEqual({
      feasibility: 'feasible',
      failReason: '',
    })
  })

  it('names the reason an order cannot go yet', () => {
    expect(
      evaluateDispatchFeasibility({ ...ready, warehouseSubstatus: 'ON_HOLD' }, 2).failReason,
    ).toBe('Warehouse hold')
    expect(evaluateDispatchFeasibility({ ...ready, readyForDispatch: false }, 2).feasibility).toBe(
      'unchecked',
    )
    expect(evaluateDispatchFeasibility({ ...ready, vehicleId: null }, 2).failReason).toBe(
      'No vehicle',
    )
    expect(
      evaluateDispatchFeasibility({ ...ready, vehicleId: null, type: 'vendor' }, 2).feasibility,
    ).toBe('feasible')
    expect(evaluateDispatchFeasibility({ ...ready, weight: 2500 }, 2).failReason).toBe('Overweight')
    expect(evaluateDispatchFeasibility({ ...ready, volume: 13 }, 2).failReason).toBe('Over volume')
    expect(evaluateDispatchFeasibility(ready, 0).failReason).toBe('No driver')
    expect(evaluateDispatchFeasibility(null, 2).feasibility).toBe('unchecked')
  })

  it('prefers a manual override, then a warehouse hold, then the order state', () => {
    expect(
      deriveFeasibility(ready, { o1: { feasibility: 'infeasible', failReason: 'Road closed' } }),
    ).toEqual({
      feasibility: 'infeasible',
      failReason: 'Road closed',
    })
    expect(deriveFeasibility({ ...ready, status: 'ON_HOLD' }).failReason).toBe('Warehouse hold')
    expect(deriveFeasibility({ ...ready, feasibility: 'feasible' }).feasibility).toBe('feasible')
    expect(deriveFeasibility(ready).feasibility).toBe('unchecked')
  })

  it('counts down to the deadline and flags the last three hours', () => {
    const now = new Date('2026-10-26T10:00:00')
    expect(getTimeRemaining('2026-10-26T12:30:00', now)).toBe('2h 30m remaining')
    expect(getTimeRemaining('2026-10-26T09:00:00', now)).toBe('OVERDUE')
    expect(getTimeRemaining(null, now)).toBe('--')
    expect(isDeadlineCritical('2026-10-26T12:30:00', now)).toBe(true)
    expect(isDeadlineCritical('2026-10-26T14:00:00', now)).toBe(false)
  })

  it('formats loads and priorities', () => {
    expect(formatOrderWeight({ weight: 500, hasWeight: true })).toBe('500 kg')
    expect(formatOrderWeight({ weight: 0, hasWeight: false })).toBe('—')
    expect(formatCapacityValue(4, false, 12, 'm³')).toBe('— / 12 m³')
    expect(getPriorityClass('URGENT')).toContain('text-red-400')
    expect(getPriorityClass('unknown')).toBe(getPriorityClass('NORMAL'))
    expect(orderAllowsDirectVehicleSelection({ type: 'SERVICE_MOVE' })).toBe(true)
    expect(orderAllowsDirectVehicleSelection({ type: 'INDIVIDUAL' })).toBe(false)
  })
})

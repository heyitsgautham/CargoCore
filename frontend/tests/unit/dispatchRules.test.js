import { describe, expect, it } from 'vitest'
import {
  dedupeRecurringDirectCandidates,
  driverHasOpenAssignments,
  isDirectDispatchAiCandidate,
  isDriverAssignableStatus,
  isVehicleDispatchableStatus,
  orderAllowsDirectVehicleSelection,
  priorityWeight,
  recurringRuleId,
  safeTimestamp,
  vehicleFitScore,
  vehicleHasOpenAssignments,
} from '@/LWD-views/Dispatcher/dispatchRules'
import {
  buildRisk,
  hoursUntil,
  orderHasAssignableResources,
  scoreVehicle,
  topDriverMatch,
  topVehicleMatch,
} from '@/LWD-views/Dispatcher/smartAssignment/assignmentRules'

const NOW = new Date('2026-10-26T10:00:00Z').getTime()
const direct = (overrides = {}) => ({
  id: 'o1',
  type: 'VENDOR',
  warehouseSubstatus: 'READY_FOR_DISPATCH',
  packingAmount: 0,
  ...overrides,
})

describe('shared dispatch rules', () => {
  it('reads driver and vehicle availability however the status is spelled', () => {
    expect(isDriverAssignableStatus('On Duty')).toBe(true)
    expect(isDriverAssignableStatus('on_break')).toBe(true)
    expect(isDriverAssignableStatus('offline')).toBe(false)
    expect(isVehicleDispatchableStatus('READY')).toBe(true)
    expect(isVehicleDispatchableStatus('In Maintenance')).toBe(false)
  })

  it('treats delivered and cancelled work as closed', () => {
    expect(
      driverHasOpenAssignments({
        activeOrders: [{ status: 'delivered' }, { status: 'CANCELLED' }],
      }),
    ).toBe(false)
    expect(driverHasOpenAssignments({ activeOrders: [{ status: 'IN_TRANSIT' }] })).toBe(true)
    const active = [{ vehicleId: 7, status: 'ASSIGNED' }]
    expect(vehicleHasOpenAssignments('7', active)).toBe(true)
    expect(vehicleHasOpenAssignments('8', active)).toBe(false)
    expect(vehicleHasOpenAssignments(null, active)).toBe(false)
  })

  it('lets the dispatcher pick vehicles for pickups, service moves and vendor orders only', () => {
    expect(
      ['PARCEL_PICKUP', 'service_move', 'VENDOR'].map((type) =>
        orderAllowsDirectVehicleSelection({ type }),
      ),
    ).toEqual([true, true, true])
    expect(orderAllowsDirectVehicleSelection({ type: 'INDIVIDUAL' })).toBe(false)
  })

  it('spots AI candidates and keeps one occurrence per recurring rule', () => {
    expect(isDirectDispatchAiCandidate(direct())).toBe(true)
    expect(isDirectDispatchAiCandidate(direct({ driverId: 'd1' }))).toBe(false)
    expect(isDirectDispatchAiCandidate(direct({ packingAmount: 2 }))).toBe(false)
    expect(recurringRuleId({ deliveryNotes: 'pallets | RECURRING_RULE:r-9' })).toBe('r-9')

    const later = direct({
      id: 'later',
      deliveryNotes: 'RECURRING_RULE:r-9',
      deadline: '2026-10-28',
    })
    const sooner = direct({
      id: 'sooner',
      deliveryNotes: 'RECURRING_RULE:r-9',
      deadline: '2026-10-27',
    })
    const plain = { id: 'plain', type: 'INDIVIDUAL' }
    expect(dedupeRecurringDirectCandidates([later, plain, sooner]).map((o) => o.id)).toEqual([
      'plain',
      'sooner',
    ])
  })

  it('sorts unknown dates last and ranks priorities', () => {
    expect(safeTimestamp('—')).toBe(Number.MAX_SAFE_INTEGER)
    expect(safeTimestamp('not a date')).toBe(Number.MAX_SAFE_INTEGER)
    expect(['urgent', 'VIP', 'high', 'medium', 'low'].map(priorityWeight)).toEqual([4, 3, 2, 1, 0])
  })

  it('prefers a vehicle of the right type with enough capacity', () => {
    const order = { vehicleType: 'Truck', weight: 2000 }
    expect(vehicleFitScore({ type: 'truck', cargoCapacityTons: 3 }, order)).toBe(83)
    expect(vehicleFitScore({ type: 'truck', cargoCapacityTons: 1 }, order)).toBe(40)
    expect(
      scoreVehicle({ type: 'truck', cargoCapacityTons: 3 }, { ...order, priority: 'VIP' }),
    ).toBe(89)
  })
})

describe('smart assignment rules', () => {
  const hubDriver = { id: 'd1', hubId: 'h1', load: 0, hours: 1, efficiency: 80, activeOrders: [] }
  const farDriver = { id: 'd2', hubId: 'h2', load: 50, hours: 7, efficiency: 40, activeOrders: [] }

  it('recommends the free driver at the order hub, with reasons', () => {
    const match = topDriverMatch({ warehouseId: 'h1' }, [farDriver, hubDriver])
    expect(match.driver.id).toBe('d1')
    expect(match.reasons).toEqual([
      'same warehouse coverage',
      'no active order assigned',
      'healthy shift time remaining',
    ])
    expect(topDriverMatch({}, [])).toBeNull()
  })

  it('only suggests vehicles for direct-dispatch orders without one', () => {
    const pool = [{ id: 'v1', type: 'van' }]
    expect(topVehicleMatch(direct(), pool).vehicle.id).toBe('v1')
    expect(topVehicleMatch(direct({ vehicleId: 'v9' }), pool)).toBeNull()
    expect(topVehicleMatch({ type: 'INDIVIDUAL' }, pool)).toBeNull()
  })

  it('rates risk from free resources, deadline, shift length and priority', () => {
    const driverMatch = { driver: hubDriver }
    const released = { type: 'INDIVIDUAL', vehicleId: 'v1' }
    expect(buildRisk(released, null, null, NOW).level).toBe('High')
    expect(
      buildRisk({ ...released, deadline: '2026-10-26T11:00:00Z' }, driverMatch, null, NOW).text,
    ).toMatch(/window is close/)
    expect(buildRisk(released, { driver: { hours: 9 } }, null, NOW).level).toBe('Medium')
    expect(buildRisk({ ...released, priority: 'VIP' }, driverMatch, null, NOW).level).toBe('Medium')
    expect(buildRisk(released, driverMatch, null, NOW).level).toBe('Low')
    expect(buildRisk(direct(), driverMatch, null, NOW).text).toMatch(/no free vehicle/)
    expect(hoursUntil('2026-10-26T12:00:00Z', NOW)).toBe(2)
  })

  it('needs a driver and a vehicle path before assigning', () => {
    expect(orderHasAssignableResources({ recommendedDriver: {}, vehicleId: 'v1' })).toBe(true)
    expect(orderHasAssignableResources({ recommendedDriver: {}, recommendedVehicle: {} })).toBe(
      true,
    )
    expect(orderHasAssignableResources({ recommendedDriver: {} })).toBe(false)
    expect(orderHasAssignableResources({ vehicleId: 'v1' })).toBe(false)
  })
})

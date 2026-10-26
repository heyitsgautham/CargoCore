import { describe, expect, it } from 'vitest'
import {
  deriveDurationLabel,
  formatVehicleLabel,
  hasOpenAssignments,
  isDriverAssignableStatus,
  isVehicleAssignableStatus,
  mapServiceMove,
  parseApiError,
  parseServiceMoveMeta,
} from '@/LWD-views/Dispatcher/serviceMoves/serviceMoveRecords'

describe('service move rules', () => {
  it('decides which drivers and vehicles can take a move', () => {
    expect(isDriverAssignableStatus('On Duty')).toBe(true)
    expect(isDriverAssignableStatus('ON_BREAK')).toBe(false)
    expect(isVehicleAssignableStatus('In Shop')).toBe(false)
    expect(isVehicleAssignableStatus('Active')).toBe(true)
    expect(
      hasOpenAssignments({ activeOrders: [{ status: 'DELIVERED' }, { status: 'ASSIGNED' }] }),
    ).toBe(true)
    expect(hasOpenAssignments({})).toBe(false)
  })

  it('reads the title and notes packed into delivery notes', () => {
    expect(
      parseServiceMoveMeta('SERVICE_MOVE_META::{"title":"Office move","notes":"Fragile"}'),
    ).toEqual({
      title: 'Office move',
      notes: 'Fragile',
    })
    expect(parseServiceMoveMeta('Call on arrival')).toEqual({ title: '', notes: 'Call on arrival' })
    expect(parseServiceMoveMeta('SERVICE_MOVE_META::{broken')).toEqual({
      title: '',
      notes: 'SERVICE_MOVE_META::{broken',
    })
    expect(deriveDurationLabel('09:00 start · 4h block')).toBe('4 hours')
    expect(deriveDurationLabel('')).toBe('4 hours')
  })

  it('labels vehicles and API errors', () => {
    expect(formatVehicleLabel({ id: 'v1', code: 'TRK-1', type: 'Truck' })).toBe('TRK-1 · Truck')
    expect(formatVehicleLabel({ id: 'v1' })).toBe('Vehicle v1')
    expect(parseApiError({ detail: [{ msg: 'bad date' }] }, 'x')).toBe('bad date')
    expect(parseApiError({}, 'fallback')).toBe('fallback')
  })
})

describe('service move cards', () => {
  const drivers = [{ id: 'd1', name: 'David Miller', vehicle: 'NY-442-XM' }]
  const vehicles = [{ id: 'v9', licensePlate: 'NY-442-XM', code: 'TRK-992', seatCapacity: 3 }]

  it('builds a card with the crew, the driver vehicle and the status badge', () => {
    const card = mapServiceMove(
      {
        id: 'o1',
        tracking_code: 'QC-1',
        cargo_type: 'Office Shift',
        status: 'IN_TRANSIT',
        assigned_driver_id: 'd1',
        delivery_notes: 'SERVICE_MOVE_META::{"title":"Office move","notes":"Fragile"}',
        service_time_block: '09:00 start · 6h block',
      },
      drivers,
      vehicles,
    )
    expect(card).toMatchObject({
      id: 'QC-1',
      title: 'Office move',
      icon: 'domain',
      status: 'In Progress',
      progress: 50,
      vehicle: 'NY-442-XM',
      seatsAvailable: 3,
      duration: '6 hours',
      notes: 'Fragile',
      crew: [{ name: 'David Miller', role: 'Driver', driverId: 'd1' }],
    })
  })

  it('falls back to a generated title and an empty crew', () => {
    const card = mapServiceMove({ id: 'abcdefgh123', status: 'CONFIRMED' }, drivers, vehicles)
    expect(card).toMatchObject({
      title: 'service_move · abcdefgh',
      status: 'Scheduled',
      vehicle: '—',
      crew: [],
      pickup: 'Not specified',
    })
  })
})

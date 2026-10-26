import { describe, expect, it } from 'vitest'
import {
  buildHouseShiftChecklist,
  estimateDistance,
  estimateDuration,
  mapOrderStatusToJobState,
  mapOrderToJob,
  mapOrderTypeToJobType,
  normalizeCrewMembers,
  parseOrderStops,
} from '../src/stores/job/orderMapping.js'

const parcelOrder = {
  id: 'ord-1',
  tracking_code: 'TRK-101',
  order_type: 'INDIVIDUAL',
  cargo_type: 'Document',
  status: 'IN_TRANSIT',
  customer_name: 'Priya Sharma',
  customer_phone: '+91 98450 00000',
  pickup_addr: '12 MG Road, Bengaluru',
  delivery_addr: '40 Indiranagar, Bengaluru',
  delivery_lat: 12.97,
  delivery_lng: 77.64,
  payment_mode: 'cod',
  total_amount: 1200,
  paid_amount: 200,
  items: [
    { id: 'i1', sku: 'ENV-A4', quantity: 2 },
    { id: 'i2', sku: 'BOX-S', quantity: 1 },
  ],
}

describe('order type to job type', () => {
  it('reads house moves, pickups and deliveries from free text', () => {
    expect(mapOrderTypeToJobType('Furniture relocation')).toBe('HOUSE_SHIFT')
    expect(mapOrderTypeToJobType('REVERSE pickup')).toBe('PARCEL_PICKUP')
    expect(mapOrderTypeToJobType('B2B')).toBe('PARCEL_DELIVERY')
    expect(mapOrderTypeToJobType(null)).toBe('PARCEL_DELIVERY')
  })

  it('splits individual bookings on the small package cargo types', () => {
    expect(mapOrderToJob(parcelOrder, null).jobType).toBe('PARCEL_DELIVERY')
    expect(mapOrderToJob({ ...parcelOrder, cargo_type: 'Household Goods' }, null).jobType).toBe('HOUSE_SHIFT')
    expect(mapOrderToJob({ ...parcelOrder, order_type: 'SERVICE_MOVE', cargo_type: 'Document' }, null).jobType).toBe(
      'HOUSE_SHIFT',
    )
  })
})

describe('order status to job state', () => {
  it('maps backend statuses onto each job type state machine', () => {
    expect(mapOrderStatusToJobState('assigned')).toBe('ASSIGNED')
    expect(mapOrderStatusToJobState('IN_TRANSIT')).toBe('IN_TRANSIT')
    expect(mapOrderStatusToJobState('DELIVERED')).toBe('COMPLETED')
    expect(mapOrderStatusToJobState('IN_TRANSIT', 'PARCEL_PICKUP')).toBe('RETURN_TRANSIT')
    expect(mapOrderStatusToJobState('CLOSED', 'PARCEL_PICKUP')).toBe('COMPLETED')
    expect(mapOrderStatusToJobState('ON_HOLD')).toBe('ASSIGNED')
    expect(mapOrderStatusToJobState('DELIVERED', 'HOUSE_SHIFT')).toBe('COMPLETED')
  })
})

describe('estimates', () => {
  it('sizes a parcel job by item count with a 45 minute floor', () => {
    expect(estimateDuration({ items: [] }, 'PARCEL_DELIVERY')).toBe(45)
    expect(estimateDuration({ items: [{ quantity: 3 }] }, 'PARCEL_DELIVERY')).toBe(59)
    expect(estimateDuration({ items: [] }, 'HOUSE_SHIFT')).toBe(360)
  })

  it('uses the manifest distance only for the job the dashboard is running', () => {
    const dashboard = { manifest: { total_distance_km: 31 }, current_job: { jobType: 'PARCEL_DELIVERY' } }
    expect(estimateDistance({}, dashboard, 'PARCEL_DELIVERY')).toBe(31)
    expect(estimateDistance({}, dashboard, 'HOUSE_SHIFT')).toBe(24)
    expect(estimateDistance({}, null, 'PARCEL_PICKUP')).toBe(8.5)
  })
})

describe('crew', () => {
  it('normalizes API crew rows and ticks attendance only when everyone checked in', () => {
    const crew = normalizeCrewMembers([
      { labourer_id: 'l1', name: 'Ravi', checked_in: true },
      { id: 'l2', name: 'Asha', role: 'Packer', checkedIn: false },
    ])
    expect(crew).toEqual([
      { id: 'l1', labourerId: 'l1', name: 'Ravi', role: 'Crew', photo: null, checkedIn: true, checkInTime: null },
      { id: 'l2', labourerId: 'l2', name: 'Asha', role: 'Packer', photo: null, checkedIn: false, checkInTime: null },
    ])
    expect(buildHouseShiftChecklist(crew)[0].completed).toBe(false)
    expect(buildHouseShiftChecklist([crew[0]])[0].completed).toBe(true)
    expect(buildHouseShiftChecklist([])[0].completed).toBe(false)
  })
})

describe('stops', () => {
  it('builds one delivery stop with packages, item count and the cash still due', () => {
    const [stop] = parseOrderStops(parcelOrder, 'PARCEL_DELIVERY')
    expect(stop.stopType).toBe('delivery')
    expect(stop.address).toBe('40 Indiranagar, Bengaluru')
    expect(stop.location).toEqual({ lat: 12.97, lng: 77.64 })
    expect(stop.packages.map((p) => p.barcode)).toEqual(['ENV-A4', 'BOX-S'])
    expect(stop.expectedItems).toBe(3)
    expect(stop.cod).toBe(true)
    expect(stop.codAmount).toBe(1000)
    expect(stop.status).toBe('pending')
    expect(stop.timeWindow).toEqual({ start: '--:--', end: '--:--' })
  })

  it('sends a pickup stop to the pickup address and marks delivered orders complete', () => {
    const [pickup] = parseOrderStops({ ...parcelOrder, status: 'DELIVERED' }, 'PARCEL_PICKUP')
    expect(pickup.stopType).toBe('pickup')
    expect(pickup.address).toBe('12 MG Road, Bengaluru')
    expect(pickup.status).toBe('completed')
  })
})

describe('order to job', () => {
  it('builds a parcel job from the order and the driver dashboard', () => {
    const dashboard = { profile: { driverId: 'DRV-7' }, current_vehicle: { vehicleId: 'VAN-2' } }
    const job = mapOrderToJob(parcelOrder, dashboard)
    expect(job).toMatchObject({
      id: 'ord-1',
      jobId: 'TRK-101',
      currentState: 'IN_TRANSIT',
      vehicleId: 'VAN-2',
      driverId: 'DRV-7',
      customerName: 'Priya Sharma',
      estimatedDuration: 59,
      routeDistance: 8.5,
    })
    expect(job.stops).toHaveLength(1)
  })

  it('builds a house shift with crew, inventory and the balance due', () => {
    const order = { ...parcelOrder, cargo_type: 'Furniture', labor_count: 3, assigned_vehicle_code: 'TRK-9 · 14ft' }
    const dashboard = { crew: [{ labourer_id: 'l1', name: 'Ravi', checked_in: true }] }
    const job = mapOrderToJob(order, dashboard)
    expect(job.jobType).toBe('HOUSE_SHIFT')
    expect(job.vehicleId).toBe('TRK-9')
    expect(job.crewRequired).toBe(3)
    expect(job.crewAssigned).toHaveLength(1)
    expect(job.inventory.map((i) => i.item)).toEqual(['ENV-A4', 'BOX-S'])
    expect(job.balanceDue).toBe(1000)
    expect(job.checklist[0].completed).toBe(true)
  })

  it('reuses the dashboard house shift when it is the same job', () => {
    const current = { jobType: 'HOUSE_SHIFT', jobId: 'TRK-101', currentState: 'PACKING' }
    const job = mapOrderToJob({ ...parcelOrder, cargo_type: 'Furniture' }, { current_job: current })
    expect(job).toBe(current)
  })
})

import { describe, expect, it } from 'vitest'
import {
  computeLogStats,
  groupDriverDocs,
  groupVehicleDocs,
  maintenanceCostLabel,
  maintenanceReportCsv,
  searchDrivers,
  searchLogs,
  searchMaintenance,
  searchTopDrivers,
  searchVehicles,
  vehicleServiceHistory,
} from '@/LWD-views/LogisticManager/fleet/fleetViews'

const notSuspended = () => false

describe('fleet searches', () => {
  it('finds drivers by name, vehicle, job or status and marks suspensions', () => {
    const drivers = [
      {
        id: 'd1',
        name: 'Ravi Kumar',
        vehicle: 'TRK-992',
        currentJob: 'Delivery #9982',
        status: 'Active',
      },
      { id: 'd2', name: 'Meena Das', vehicle: null, currentJob: null, status: 'Suspended' },
    ]

    expect(searchDrivers(drivers, 'trk', notSuspended).map((d) => d.id)).toEqual(['d1'])
    expect(searchDrivers(drivers, '#9982', notSuspended).map((d) => d.id)).toEqual(['d1'])
    expect(
      searchDrivers(drivers, '', (d) => d.status === 'Suspended').map((d) => d.dispatcherSuspended),
    ).toEqual([false, true])
    expect(searchTopDrivers(drivers, 'meena', notSuspended).map((d) => d.id)).toEqual(['d2'])
  })

  it('matches vehicles and maintenance alerts on any listed field', () => {
    const vehicles = [
      {
        id: 'v1',
        code: 'TRK-992',
        type: 'Heavy Truck',
        model: 'Volvo',
        driver: 'Ravi',
        status: 'In Shop',
      },
      { id: 'v2', code: 'VAN-104', type: 'Van', model: 'Ford', driver: 'Meena', status: 'Active' },
    ]
    expect(searchVehicles(vehicles, 'in shop').map((v) => v.id)).toEqual(['v1'])
    expect(searchVehicles(vehicles, 'FORD').map((v) => v.id)).toEqual(['v2'])

    const alerts = [{ id: 'M-1', issue: 'Engine light', status: 'Open' }]
    expect(searchMaintenance(alerts, 'engine')).toHaveLength(1)
    expect(searchMaintenance(alerts, 'tyre')).toHaveLength(0)
  })

  it('limits logs to the selected hub and searches every field', () => {
    const logs = [
      { id: 1, hubId: 'h1', vehicleId: 'TRK-992', cost: 100 },
      { id: 2, hubId: 'h2', vehicleId: 'VAN-104', cost: 50 },
    ]
    expect(searchLogs(logs, '', 'h1').map((l) => l.id)).toEqual([1])
    expect(searchLogs(logs, 'van', 'all').map((l) => l.id)).toEqual([2])
    expect(searchLogs(undefined, '', 'all')).toEqual([])
  })
})

describe('log summaries', () => {
  it('reports fuel price per unit and verified share', () => {
    const stats = computeLogStats('Fuel Logs', [
      { cost: 300, gallons: 10, status: 'Verified' },
      { cost: 100, gallons: 10, status: 'Pending' },
    ])
    expect(stats.title).toBe('Fuel Consumption')
    expect(stats.tiles).toEqual([
      { label: 'Avg Price/Gal', value: '₹20.00' },
      { label: 'Total Volume', value: '20 L' },
    ])
    expect(stats.trend).toMatchObject({ value: '1 / 2', pct: 50 })
    expect(stats.totalCost).toBe(400)
  })

  it('counts open repairs and resolved ones for maintenance logs', () => {
    const stats = computeLogStats('Maintenance Logs', [
      { cost: 900, status: 'Resolved' },
      { cost: 100, status: 'Open' },
      { cost: 200, status: 'Open' },
    ])
    expect(stats.tiles[0]).toEqual({ label: 'Active Repairs', value: 2 })
    expect(stats.tiles[1]).toEqual({ label: 'Avg Repair Cost', value: '₹400' })
    expect(stats.trend).toMatchObject({ value: '1 / 3', pct: 33 })
  })

  it('handles an empty list without dividing by zero', () => {
    const stats = computeLogStats('Cleaning Logs', [])
    expect(stats.title).toBe('Fleet Hygiene')
    expect(stats.tiles[1].value).toBe('₹0')
    expect(stats.trend.pct).toBe(0)
  })
})

describe('documents', () => {
  const vehicleDocs = [
    { vehicleId: 'TRK-992', type: 'Insurance Policy', status: 'Valid', hubId: 'h1' },
    { vehicleId: 'TRK-992', type: 'Registration', status: 'Expired', hubId: 'h1' },
    { vehicleId: 'VAN-104', type: 'Insurance Policy', status: 'Valid', hubId: 'h2' },
  ]

  it('groups vehicle documents per vehicle after hub and search filters', () => {
    expect(Object.keys(groupVehicleDocs(vehicleDocs, 'all', ''))).toEqual(['TRK-992', 'VAN-104'])
    expect(groupVehicleDocs(vehicleDocs, 'h1', 'expired')).toEqual({ 'TRK-992': [vehicleDocs[1]] })
  })

  it('groups driver documents per driver', () => {
    const groups = groupDriverDocs(
      [
        {
          driverId: 'd1',
          driver: 'Ravi',
          type: 'License',
          licenseNo: 'KA01',
          status: 'Valid',
          hubId: 'h1',
        },
        {
          driverId: 'd1',
          driver: 'Ravi',
          type: 'Medical',
          licenseNo: 'KA01',
          status: 'Valid',
          hubId: 'h1',
        },
        {
          driverId: 'd2',
          driver: 'Meena',
          type: 'License',
          licenseNo: 'KA02',
          status: 'Valid',
          hubId: 'h1',
        },
      ],
      'all',
      'ka01',
    )
    expect(groups).toEqual([{ id: 'd1', name: 'Ravi', docs: expect.any(Array) }])
    expect(groups[0].docs).toHaveLength(2)
  })
})

describe('vehicle costs and report', () => {
  const fleetLogs = {
    'Service Logs': [
      { id: 's1', vehicleId: 'v1', service: 'Oil change', date: '2026-10-01', cost: 200 },
    ],
    'Maintenance Logs': [
      { id: 'm1', vehicleId: 'TRK-992', issue: 'Brakes', date: '2026-10-02', cost: 1500 },
      { id: 'm2', vehicleId: 'v1', issue: 'Clutch', date: '2026-10-03', cost: 800 },
    ],
  }

  it('builds a vehicle service history with its total', () => {
    const { history, total } = vehicleServiceHistory(fleetLogs, 'v1')
    expect(history.map((h) => [h.service, h.type])).toEqual([
      ['Oil change', 'Routine'],
      ['Clutch', 'Repair'],
    ])
    expect(total).toBe(1000)
  })

  it('labels the repair cost of a maintenance alert by the vehicle code', () => {
    const vehicles = [{ id: 'v1', code: 'TRK-992' }]
    expect(maintenanceCostLabel(vehicles, fleetLogs, 'v1')).toBe(`₹${(1500).toLocaleString()}`)
    expect(maintenanceCostLabel(vehicles, fleetLogs, 'missing')).toBe('—')
  })

  it('quotes every CSV cell and names the hub', () => {
    const csv = maintenanceReportCsv(
      [{ id: 'v1', code: 'TRK "9"', model: 'Volvo', hubId: 'h1' }],
      [{ id: 'h1', name: 'North Hub' }],
    )
    const [header, row] = csv.split('\r\n')
    expect(header.startsWith('"Vehicle ID","License Plate"')).toBe(true)
    expect(row).toBe('"TRK ""9""","—","—","Volvo","—","—","—","North Hub","—","—"')
  })
})

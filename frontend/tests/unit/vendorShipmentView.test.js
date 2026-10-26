import { describe, expect, it, vi } from 'vitest'
import {
  buildTrackingLogs,
  filterShipments,
  liveDriverPosition,
  shipmentDocuments,
  shipmentPhase,
  statusIcon,
  topRoutes,
} from '@/IV-views/Vendor/tracking/shipmentView'
import { spendChart, volumeChart } from '@/IV-views/Vendor/tracking/trackingCharts'

const shipments = [
  {
    id: 'QC-1',
    statusKey: 'delivered',
    origin: 'Pune',
    destination: 'Mumbai',
    route: 'Pune → Mumbai',
  },
  {
    id: 'QC-2',
    statusKey: 'transit',
    origin: 'Pune',
    destination: 'Mumbai',
    route: 'Pune → Mumbai',
  },
  { id: 'QC-3', statusKey: 'pending', origin: 'Delhi', destination: 'Agra', route: 'Delhi → Agra' },
]

describe('vendor shipment list', () => {
  it('filters by status and by id, destination or route', () => {
    expect(filterShipments(shipments, 'all', '').map((s) => s.id)).toEqual(['QC-1', 'QC-2', 'QC-3'])
    expect(filterShipments(shipments, 'transit', '').map((s) => s.id)).toEqual(['QC-2'])
    expect(filterShipments(shipments, 'all', 'agra').map((s) => s.id)).toEqual(['QC-3'])
  })

  it('ranks the busiest routes with their delivered share', () => {
    expect(topRoutes(shipments)).toEqual([
      { route: 'Pune → Mumbai', count: 2, delivered: 1, rank: '01', onTime: 50 },
      { route: 'Delhi → Agra', count: 1, delivered: 0, rank: '02', onTime: 0 },
    ])
  })
})

describe('selected shipment', () => {
  it('describes delivered, cancelled and moving shipments', () => {
    expect(shipmentPhase({ statusKey: 'delivered' })).toMatchObject({
      etaLabel: 'Delivered',
      mapLabel: 'Delivered',
      driver: { label: 'Trip Completed' },
    })
    expect(shipmentPhase({ statusKey: 'cancelled' }).driver.label).toBe('Assignment Closed')
    expect(shipmentPhase({ statusKey: 'transit', eta: '2 PM' })).toMatchObject({
      etaLabel: '2 PM',
      mapLabel: 'In Transit',
    })
    expect(shipmentPhase(null).etaLabel).toBe('TBD')
  })

  it('reports a live driver position only while the trip is open', () => {
    expect(
      liveDriverPosition({ statusKey: 'transit', driverLat: '12.9', driverLng: 77.6 }),
    ).toEqual([12.9, 77.6])
    expect(
      liveDriverPosition({ statusKey: 'delivered', driverLat: 12.9, driverLng: 77.6 }),
    ).toBeNull()
    expect(liveDriverPosition({ statusKey: 'transit', driverLat: 'x', driverLng: 1 })).toBeNull()
  })

  it('lists the transit log newest first, or the current status without history', () => {
    const logs = buildTrackingLogs({
      statusKey: 'delivered',
      origin: 'Pune',
      destination: 'Mumbai',
      statusHistory: [
        { status: 'Order Placed', time: null },
        { status: 'Delivered', time: null },
      ],
    })
    expect(logs.map((l) => [l.action, l.location, l.icon, l.isCurrent])).toEqual([
      ['Delivered', 'Mumbai', 'done_all', true],
      ['Order Placed', 'Pune', 'shopping_cart', false],
    ])

    const [single] = buildTrackingLogs({ status: 'In Transit', route: 'A → B' })
    expect(single).toMatchObject({
      action: 'In Transit',
      location: 'A → B',
      date: 'Today',
      isCurrent: true,
    })
    expect(statusIcon('Something else')).toBe('radio_button_checked')
  })

  it('offers proof of delivery and the invoice only after delivery', () => {
    const open = vi.fn()
    const slips = { labels: {}, icons: {}, open }

    expect(shipmentDocuments({ statusKey: 'transit' }, slips).map((d) => d.key)).toEqual([
      'bookingConfirmation',
    ])
    const delivered = shipmentDocuments({ statusKey: 'delivered', pod: { photoCount: 1 } }, slips)
    expect(delivered.map((d) => d.key)).toEqual([
      'bookingConfirmation',
      'proofOfDelivery',
      'finalTaxInvoice',
    ])
    expect(delivered[1].description).toBe('1 proof file recorded')
    delivered[2].action()
    expect(open).toHaveBeenCalledWith('finalTaxInvoice')
  })
})

describe('vendor tracking charts', () => {
  it('plots monthly spend and order counts', () => {
    const monthly = [
      { month: 'Sep', spend: 1000, orders: 3 },
      { month: 'Oct', spend: 2500, orders: 5 },
    ]
    expect(spendChart(monthly)).toMatchObject({
      labels: ['Sep', 'Oct'],
      datasets: [{ data: [1000, 2500] }],
    })
    expect(volumeChart(monthly).datasets[0].data).toEqual([3, 5])
  })
})

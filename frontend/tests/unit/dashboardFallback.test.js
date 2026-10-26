import { describe, expect, it } from 'vitest'
import { buildFallbackDashboard } from '@/LWD-views/WarehouseManager/dashboard/dashboardFallback'

const now = new Date('2026-10-26T15:30:00')

describe('warehouse dashboard fallback', () => {
  it('summarises pending, ready and low-stock work from the raw lists', () => {
    const dash = buildFallbackDashboard(
      {
        inventoryItems: [
          {
            sku: 'TAPE',
            name: 'Tape',
            quantity_on_hand: 5,
            safety_stock: 10,
            category: 'Consumables',
          },
          { sku: 'BOX', name: 'Box', quantity_on_hand: 50, safety_stock: 10, category: 'Packing' },
        ],
        warehouseOrders: [
          {
            id: 'o1',
            tracking_code: 'QC-1',
            status: 'CONFIRMED',
            created_at: '2026-10-26T09:10:00',
            items: [{}, {}],
          },
          { id: 'o2', status: 'IN_TRANSIT', created_at: '2026-10-26T10:00:00' },
          { id: 'o3', status: 'DELIVERED', created_at: '2026-10-25T10:00:00' },
        ],
        labourers: [{ is_active: true }, { is_active: false }],
      },
      now,
    )

    expect(dash).toMatchObject({
      total_inventory_value: 5500,
      pending_orders_count: 1,
      ready_for_dispatch: 1,
      next_truck_minutes: 15,
      active_labor: 1,
      total_labor: 2,
    })
    expect(dash.critical_skus).toEqual([
      { id: 'TAPE', name: 'Tape', current: 5, min: 10, sku: 'TAPE' },
    ])
    expect(dash.picking_queue[0]).toMatchObject({ id: 'QC-1', items: 2, priority: 'Normal' })
    expect(dash.efficiency_insight).toBe('1 of 3 orders completed. 1 orders pending pick.')
  })

  it('counts picks per hour from 06:00 up to the current hour', () => {
    const dash = buildFallbackDashboard(
      { warehouseOrders: [{ status: 'CONFIRMED', created_at: '2026-10-26T09:10:00' }] },
      now,
    )
    const chart = dash.throughput_chart
    expect(chart.labels[0]).toBe('06:00')
    expect(chart.labels.at(-1)).toBe('15:00')
    expect(chart.datasets[0].data[3]).toBe(1)
  })

  it('leaves the staff and stock charts empty without data', () => {
    const dash = buildFallbackDashboard({ kpis: { order_count: 7, labour_count: 4 } }, now)
    expect(dash.pending_orders_count).toBe(7)
    expect(dash.total_labor).toBe(4)
    expect(dash.stock_packaging_chart).toBeNull()
    expect(dash.active_staff_chart).toBeNull()
    expect(dash.efficiency_insight).toBe('No orders assigned to this warehouse yet.')
  })
})

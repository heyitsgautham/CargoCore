import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { useZoneMetrics } from '@/LWD-views/WarehouseManager/comparativeViewers/zoneMetrics'

const day = (date, fields) => ({ metric_date: `${date}T12:00:00`, ...fields })

function setup(cache = {}, floor = { sections: [], racks: [] }) {
  return useZoneMetrics(ref(cache), floor)
}

describe('zone metrics', () => {
  it('rounds the latest metric and tells "not fetched" apart from "no data"', () => {
    const m = setup({
      z1: { latest: { orders_processed: 41.6, picking_accuracy_pct: 99.4 }, series: [] },
      z2: { latest: null, series: [] },
    })

    expect(m.getZoneMetricValue('z1', 'orders_processed')).toBe(42)
    expect(m.getZoneMetricValue('z1', 'picking_accuracy')).toBe(99)
    expect(m.getZoneMetricValue('z1', 'throughput')).toBeNull()
    expect(m.getZoneMetricValue('z2', 'orders_processed')).toBeNull()
    expect(m.getZoneMetricValue('missing', 'orders_processed')).toBeNull()
  })

  it('reports the percent change between the last two days', () => {
    const m = setup({
      up: {
        series: [
          day('2026-10-24', { orders_processed: 40 }),
          day('2026-10-25', { orders_processed: 50 }),
        ],
      },
      down: {
        series: [
          day('2026-10-24', { throughput_items_per_hour: 200 }),
          day('2026-10-25', { throughput_items_per_hour: 150 }),
        ],
      },
      zero: {
        series: [
          day('2026-10-24', { orders_processed: 0 }),
          day('2026-10-25', { orders_processed: 9 }),
        ],
      },
      one: { series: [day('2026-10-25', { orders_processed: 9 })] },
    })

    expect(m.getMetricTrend('up', 'orders_processed')).toBe(25)
    expect(m.getMetricTrend('down', 'throughput')).toBe(-25)
    expect(m.getMetricTrend('zero', 'orders_processed')).toBeNull()
    expect(m.getMetricTrend('one', 'orders_processed')).toBeNull()
    expect(m.getMetricTrend('up', 'unknown_metric')).toBeNull()
  })

  it('counts racks through the sections that belong to a zone', () => {
    const floor = {
      sections: [
        { id: 's1', groupId: 'z1' },
        { id: 's2', groupId: 'z1' },
        { id: 's3', groupId: 'z2' },
      ],
      racks: [{ sectionId: 's1' }, { sectionId: 's1' }, { sectionId: 's2' }, { sectionId: 's3' }],
    }
    const m = setup({ z1: { latest: { capacity_used_pct: 66.4 } } }, floor)

    expect(m.getZoneRackCount('z1')).toBe(3)
    expect(m.getZoneRackCount('z3')).toBe(0)
    expect(m.getUsedRacks({ id: 'z1', value: '10%' })).toBe('2 Racks')
    expect(m.getUsedRacks({ id: 'z3', value: '50%' })).toBe('–')
  })

  it('prefers the API capacity and falls back to the zone label', () => {
    const m = setup({ z1: { latest: { capacity_used_pct: 72.6 } } })

    expect(m.getCapacityPct({ id: 'z1', value: '10%' })).toBe(73)
    expect(m.getCapacityPct({ id: 'z2', value: 'Full' })).toBe(100)
    expect(m.getCapacityPct({ id: 'z2', value: '45%' })).toBe(45)
    expect(m.getCapacityPct({ id: 'z2', value: 'Empty' })).toBe('–')
  })

  it('grades staffing by active pickers', () => {
    const m = setup({
      full: { latest: { active_pickers: 12 } },
      mid: { latest: { active_pickers: 6 } },
      low: { latest: { active_pickers: 2 } },
    })

    expect(m.getStaffingStatus('full').label).toBe('Optimal')
    expect(m.getStaffingStatus('mid').label).toBe('Moderate')
    expect(m.getStaffingStatus('low').label).toBe('Low Staff')
    expect(m.getStaffingStatus('none')).toEqual({
      label: '–',
      color: 'text-gray-400 dark:text-gray-500',
    })
  })

  it('charts the last seven days of the chosen field', () => {
    const series = Array.from({ length: 9 }, (_, i) =>
      day(`2026-10-${String(10 + i).padStart(2, '0')}`, {
        throughput_items_per_hour: i * 10.4,
        capacity_used_pct: 50,
      }),
    )
    const m = setup({ z1: { series }, empty: { series: [] } })

    const throughput = m.getLineChartData('z1', 'Throughput')
    expect(throughput.labels).toHaveLength(7)
    expect(throughput.labels[0]).toBe('Mon')
    expect(throughput.datasets[0].data).toEqual([21, 31, 42, 52, 62, 73, 83])
    expect(throughput.datasets[0].borderColor).toBe('#3b82f6')

    const stock = m.getLineChartData('z1', 'Stock', 'green')
    expect(stock.datasets[0].data.every((v) => v === 50)).toBe(true)
    expect(stock.datasets[0].borderColor).toBe('#10b981')

    expect(m.getLineChartData('empty', 'Throughput')).toBeNull()
  })

  it('splits active pickers into pickers, stowers and QA', () => {
    const m = setup({
      z1: { latest: { active_pickers: 10 } },
      z0: { latest: { active_pickers: 0 } },
    })

    expect(m.getLaborData('z1').datasets[0].data).toEqual([6, 3, 1])
    expect(m.getLaborData('z0')).toBeNull()
    expect(m.getLaborData('missing')).toBeNull()
  })
})

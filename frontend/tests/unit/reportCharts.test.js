import { describe, expect, it } from 'vitest'
import {
  fuelAnomalyText,
  hubEfficiencyChart,
  paymentReconChart,
  procurementCapitalChart,
  revenueStreamChart,
  rmaReasonBuckets,
  rmaReasonsChart,
  slaChart,
} from '@/LWD-views/LogisticManager/reports/reportCharts'
import {
  attendanceCounts,
  exportRows,
  loggedInOn,
  toCsv,
  userLeave,
} from '@/LWD-views/LogisticManager/reports/reportRows'

describe('report charts', () => {
  it('splits income into standard deliveries and personal moves', () => {
    const chart = revenueStreamChart([
      { amount: 300, desc: 'Vendor delivery' },
      { amount: 100, desc: 'House move Indiranagar' },
      { amount: -50, desc: 'Fuel' },
    ])
    expect(chart.datasets[0].data).toEqual([75, 25])
    expect(revenueStreamChart([]).datasets[0].data).toEqual([65, 35])
  })

  it('flags a fuel expense 40% above the average', () => {
    const txs = [
      { amount: -100, desc: 'Fuel refill', date: 'Oct 1' },
      { amount: -100, desc: 'Fuel refill', date: 'Oct 2' },
      { amount: -400, desc: 'Fuel bulk', date: 'Oct 3' },
    ]
    expect(fuelAnomalyText(txs)).toBe(
      `Transaction "Fuel bulk" on Oct 3 was ₹${(400).toLocaleString()} — 100% above fleet average.`,
    )
    expect(fuelAnomalyText(txs.slice(0, 2))).toBeNull()
    expect(fuelAnomalyText(txs.slice(0, 1))).toBeNull()
  })

  it('falls back to default labels when report metrics are missing', () => {
    expect(paymentReconChart({}).labels).toEqual(['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
    expect(
      paymentReconChart({ payment_reconciliation: { labels: ['A'], expected_cod: [5] } }),
    ).toMatchObject({ labels: ['A'] })
    expect(procurementCapitalChart(null).datasets[0].data).toEqual([0, 0])
    expect(slaChart({ slaCompliance: { week: [1, 2] } }).datasets[0].data).toEqual([1, 2])
  })

  it('colours hubs by efficiency band', () => {
    const chart = hubEfficiencyChart([
      { name: 'North', efficiency: 95 },
      { name: 'South', efficiency: 85 },
      { name: 'West', efficiency: 60 },
    ])
    expect(chart.labels).toEqual(['North', 'South', 'West'])
    expect(chart.datasets[0].backgroundColor).toEqual(['#10b981', '#f59e0b', '#ef4444'])
  })

  it('counts return reasons by keyword when the backend has no metrics', () => {
    const returns = [
      { reason: 'Box arrived broken' },
      { reason: 'Wrong item sent' },
      { reason: 'Delayed by a week' },
      { reason: 'Changed mind' },
      { reason: 'Colour' },
      { reason: '' },
    ]
    expect(rmaReasonBuckets(returns)).toEqual({
      Damaged: 1,
      'Wrong Item': 1,
      'Late Delivery': 1,
      'Changed Mind': 1,
      Other: 1,
    })
    expect(rmaReasonsChart({}, [{ reason: 'cracked' }])).toMatchObject({
      labels: ['Damaged'],
      datasets: [{ data: [1] }],
    })
    expect(rmaReasonsChart({ rma_reasons: { labels: ['X'], values: [3] } }, [])).toMatchObject({
      labels: ['X'],
      datasets: [{ data: [3] }],
    })
  })
})

describe('report rows', () => {
  const users = [
    { id: 'u1', name: 'Ravi', email: 'r@x.in', lastLogin: '2026-10-26T09:00:00', status: 'Active' },
    {
      id: 'u2',
      name: 'Meena',
      email: 'm@x.in',
      lastLogin: '2026-10-20T09:00:00',
      status: 'On Leave',
    },
    { id: 'u3', name: 'Imran', email: 'i@x.in', status: 'Active' },
  ]

  it('counts who logged in today, who is on leave and who is missing', () => {
    expect(loggedInOn(users[0], '2026-10-26')).toBe(true)
    expect(loggedInOn(users[2], '2026-10-26')).toBe(false)
    expect(attendanceCounts(users, '2026-10-26')).toEqual({
      present: 1,
      onLeave: 1,
      unplanned: 1,
      presentPct: 33,
    })
    expect(attendanceCounts([], '2026-10-26').presentPct).toBe(0)
  })

  it('estimates leave taken from status, or from the last character of the id', () => {
    expect(userLeave({ id: 'x', status: 'Vacation' })).toEqual({
      allowed: 20,
      taken: 5,
      balance: 15,
      extra: 0,
    })
    // 'a' is char code 97, and 97 % 6 is 1
    expect(userLeave({ id: 'a', status: 'Active' }).taken).toBe(1)
  })

  it('exports the attendance tab with presence for the given day', () => {
    const rows = exportRows('attendance', { filteredUsers: users }, '2026-10-26')
    expect(rows[0]).toEqual(['Name', 'Email', 'Status Today', 'Last Login'])
    expect(rows.slice(1).map((r) => r[2])).toEqual(['Present', 'Absent', 'Absent'])
    expect(exportRows('unknown', {}, '2026-10-26')).toEqual([])
  })

  it('quotes CSV cells and doubles embedded quotes', () => {
    expect(
      toCsv([
        ['a', 'say "hi"'],
        [null, 3],
      ]),
    ).toBe('"a","say ""hi"""\r\n"","3"')
  })
})

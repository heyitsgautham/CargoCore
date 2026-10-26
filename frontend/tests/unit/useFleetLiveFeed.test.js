import { ref } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import { useFleetLiveFeed } from '@/composables/useFleetLiveFeed'
import {
  trendChartData,
  trendChartOptions,
  trendTooltipLabel,
} from '@/LWD-views/LogisticManager/dashboard/trendChart'

class FakeSocket {
  static OPEN = 1
  static instances = []
  constructor(url) {
    this.url = url
    this.readyState = 0
    this.sent = []
    FakeSocket.instances.push(this)
  }
  send(msg) {
    this.sent.push(msg)
  }
  close() {}
}

beforeEach(() => {
  vi.useFakeTimers()
  FakeSocket.instances = []
  vi.stubGlobal('WebSocket', FakeSocket)
  localStorage.setItem('auth_token', 'tok')
})

afterEach(() => vi.useRealTimers())

describe('fleet live feed', () => {
  it('loads drivers with a position and fits the map to them', async () => {
    stubFetch([
      [
        'GET',
        '/tracking/drivers',
        [
          { driver_id: 'd1', latitude: 12.9, longitude: 77.6 },
          { driver_id: 'd2', latitude: null, longitude: 77.6 },
        ],
      ],
    ])
    const fitBounds = vi.fn()
    const feed = useFleetLiveFeed({ mapRef: ref({ leafletObject: { fitBounds } }) })

    await feed.fetchLiveDrivers()

    expect(feed.liveDrivers.value.map((d) => d.driver_id)).toEqual(['d1'])
    expect(fitBounds).toHaveBeenCalledOnce()
    expect(feed.fleetLoading.value).toBe(false)
  })

  it('applies socket updates, answers pings and polls while reconnecting', async () => {
    const router = stubFetch([['GET', '/tracking/drivers', []]])
    const feed = useFleetLiveFeed()

    feed.connectFleetWs()
    const socket = FakeSocket.instances[0]
    expect(socket.url).toContain('/ws/fleet?token=tok')

    socket.onopen()
    expect(feed.wsConnected.value).toBe(true)
    socket.onmessage({
      data: JSON.stringify({ type: 'location_update', driver_id: 'd1', latitude: 1, longitude: 2 }),
    })
    socket.onmessage({
      data: JSON.stringify({ type: 'location_update', driver_id: 'd1', latitude: 3, longitude: 4 }),
    })
    socket.onmessage({ data: JSON.stringify({ type: 'ping' }) })
    expect(feed.liveDrivers.value).toEqual([
      expect.objectContaining({ driver_id: 'd1', latitude: 3 }),
    ])
    expect(socket.sent).toEqual([JSON.stringify({ type: 'pong' })])

    socket.onclose()
    expect(feed.wsConnected.value).toBe(false)
    await vi.advanceTimersByTimeAsync(2000)
    expect(FakeSocket.instances).toHaveLength(2)
    await vi.advanceTimersByTimeAsync(30000)
    expect(router.calls.some((c) => c.url.includes('/tracking/drivers'))).toBe(true)

    feed.disconnectFleetWs()
  })
})

describe('dashboard trend chart', () => {
  const stats = { slaCompliance: { week: [90, 95] }, revenue: { month: [1, 2, 3] }, orders: {} }

  it('plots the selected series for the week or month', () => {
    expect(trendChartData(stats, 'sla', 'week')).toMatchObject({
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      datasets: [{ label: 'SLA Compliance (%)', data: [90, 95] }],
    })
    expect(trendChartData(stats, 'revenue', 'month').labels).toEqual([1, 2, 3])
    expect(trendChartData(stats, 'orders', 'week').datasets[0].data).toEqual([])
  })

  it('scales SLA from 70 to 100 and formats each tooltip', () => {
    expect(trendChartOptions('sla').scales.y).toMatchObject({ min: 70, max: 100 })
    expect(trendChartOptions('orders').scales.y.min).toBe(0)
    expect(trendTooltipLabel('sla', 'SLA', 95)).toBe('SLA: 95%')
    expect(trendTooltipLabel('revenue', '', 1200)).toBe(`$${(1200).toLocaleString()}`)
  })
})

import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'

const HUB = 'hub-1'

vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => ({
    authToken: 'token',
    currentWarehouse: { id: 'hub-1' },
    currentUser: { warehouse_id: 'hub-1' },
    ensureWarehouseContext: async () => {},
  }),
}))

vi.mock('@/composables/useSlipPrinter', () => ({
  useSlipPrinter: () => ({ openSlipWithData: vi.fn() }),
}))

const { default: Picking } = await import('@/LWD-views/WarehouseManager/Picking.vue')

function order(id, substatus, overrides = {}) {
  return {
    id,
    tracking_code: `QC-${id}`,
    warehouse_id: HUB,
    status: 'CONFIRMED',
    warehouse_substatus: substatus,
    packing_amount: 250,
    labor_count: 0,
    items: [{ quantity: 1 }],
    total_amount: 1000,
    ...overrides,
  }
}

let router

beforeEach(() => {
  localStorage.clear()
  router = stubFetch([
    [
      'GET',
      '/api/v1/orders?',
      {
        items: [
          order('a', 'AWAITING_PICK'),
          order('b', 'PICKING'),
          order('c', 'PACKING'),
          order('d', 'AWAITING_PICK', { labor_count: 2 }),
        ],
      },
    ],
    ['GET', '/api/v1/labourers', { items: [{ id: 'l1', name: 'Ravi', is_active: true }] }],
    ['GET', '/api/v1/inventory?', { total: 5 }],
    ['GET', '/floor-plan', { sections: [{}] }],
    ['GET', '/operations/quality-checks', { items: [] }],
    ['GET', '/operations/packing-stations', { items: [] }],
    ['POST', '/start-picking', { ok: true }],
    ['POST', '/revert-picking', { ok: true }],
  ])
})

afterEach(() => {
  vi.useRealTimers()
})

async function mountPicking() {
  const wrapper = mount(Picking, {
    global: {
      provide: { openScanner: vi.fn(), lastGlobalScan: null },
      stubs: { Teleport: true },
    },
  })
  await flushPromises()
  return wrapper
}

function cardIds(wrapper) {
  return wrapper.findAll('.font-mono.text-primary.font-bold').map((node) => node.text())
}

describe('Picking view', () => {
  it('shows a card for every active wave, with short-staffed orders on hold', async () => {
    const wrapper = await mountPicking()

    expect(cardIds(wrapper)).toEqual(['QC-d', 'QC-a', 'QC-b', 'QC-c'])
    expect(wrapper.text()).toContain('Need 2 labourer(s) — 0 assigned')
    wrapper.unmount()
  })

  it('narrows the board when a status filter is toggled and clears it again', async () => {
    const wrapper = await mountPicking()
    const picking = wrapper.findAll('button').find((b) => b.text() === 'Picking')

    await picking.trigger('click')
    expect(wrapper.text()).toContain('1 orders')
    expect(wrapper.text()).toContain('(filtered)')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Clear')
      .trigger('click')
    expect(wrapper.text()).toContain('4 orders')
    expect(wrapper.text()).not.toContain('(filtered)')
    wrapper.unmount()
  })

  it('starts picking an awaiting wave and undoes it through the revert endpoint', async () => {
    const wrapper = await mountPicking()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Start Picking')
      .trigger('click')
    await flushPromises()

    const start = router.calls.find((c) => c.url.includes('/orders/a/start-picking'))
    expect(start.method).toBe('POST')
    expect(start.body).toEqual({ labourer_id: null })
    expect(wrapper.text()).toContain('QC-a moved to PICKING')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Undo')
      .trigger('click')
    await flushPromises()

    expect(router.calls.some((c) => c.url.includes('/orders/a/revert-picking'))).toBe(true)
    expect(wrapper.text()).toContain('Reverted to AWAITING PICK')
    wrapper.unmount()
  })
})

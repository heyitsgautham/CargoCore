import { computed, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import { useOrderActions } from '@/LWD-views/Dispatcher/orderStatus/useOrderActions'
import { useStatusTransitions } from '@/LWD-views/Dispatcher/orderStatus/useStatusTransitions'

const toast = () => ({ success: vi.fn(), warning: vi.fn(), error: vi.fn() })
const store = () => ({ fetchActiveOrders: vi.fn().mockResolvedValue() })

beforeEach(() => {
  localStorage.setItem('auth_token', 'tok')
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

describe('order status transitions', () => {
  function setup(orders) {
    const selected = ref(orders)
    const deps = {
      API_BASE: 'http://api',
      bulkUpdating: ref(false),
      canDispatchOrder: (o) => Boolean(o.driverId),
      clearSelection: vi.fn(),
      getOrderKey: (o) => o.backendId,
      selectedDispatchableReadyOrders: computed(() =>
        selected.value.filter((o) => o.status === 'ready'),
      ),
      selectedDispatchedOrders: computed(() =>
        selected.value.filter((o) => o.status === 'dispatched'),
      ),
      selectedTransitOrders: computed(() =>
        selected.value.filter((o) => o.status === 'in-transit'),
      ),
      store: store(),
      toast: toast(),
      transitionPending: ref({}),
    }
    return { deps, ...useStatusTransitions(deps) }
  }

  it('moves an order to in transit once the backend accepts it', async () => {
    const router = stubFetch([['POST', '/orders/o1/transition', {}]])
    const order = { id: 'QC-1', backendId: 'o1', status: 'dispatched', driverId: 'd1' }
    const { deps, updateStatus, isTransitionPending } = setup([])

    await updateStatus(order, 'in-transit')

    expect(router.calls[0].body).toEqual({ next_status: 'IN_TRANSIT' })
    expect(order).toMatchObject({
      status: 'in-transit',
      statusLabel: 'In Transit',
      slaStatus: 'In Transit',
    })
    expect(deps.clearSelection).toHaveBeenCalledWith(['o1'])
    expect(deps.toast.success).toHaveBeenCalledWith('In Transit updated for QC-1')
    expect(isTransitionPending(order)).toBe(false)
  })

  it('refuses to dispatch an order without a driver and leaves it unchanged', async () => {
    const router = stubFetch([])
    const order = { id: 'QC-2', backendId: 'o2', status: 'ready' }
    const { deps, updateStatus } = setup([])

    await updateStatus(order, 'dispatched')

    expect(router.calls).toHaveLength(0)
    expect(order.status).toBe('ready')
    expect(deps.toast.warning).toHaveBeenCalledWith('Assign a driver before dispatching QC-2')
  })

  it('keeps the status when the backend refuses the transition', async () => {
    stubFetch([['POST', '/transition', { status: 409, body: { detail: 'Already delivered' } }]])
    const order = { id: 'QC-3', backendId: 'o3', status: 'in-transit' }
    const { deps, updateStatus } = setup([])

    await updateStatus(order, 'delivered')

    expect(order.status).toBe('in-transit')
    expect(deps.toast.error).toHaveBeenCalledWith('Already delivered')
  })

  it('reports partial success for a bulk update', async () => {
    stubFetch([
      ['POST', '/orders/a/transition', {}],
      ['POST', '/orders/b/transition', { status: 500, body: { detail: 'boom' } }],
    ])
    const orders = [
      { id: 'QC-A', backendId: 'a', status: 'in-transit' },
      { id: 'QC-B', backendId: 'b', status: 'in-transit' },
    ]
    const { deps, applyBulkStatus } = setup(orders)

    await applyBulkStatus('delivered')

    expect(deps.toast.warning).toHaveBeenCalledWith(
      'Delivered updated for 1 orders. 1 failed and stayed selected.',
    )
    expect(deps.store.fetchActiveOrders).toHaveBeenCalled()
    expect(deps.bulkUpdating.value).toBe(false)
  })
})

describe('order action menu', () => {
  function setup(orders) {
    const deps = {
      API_BASE: 'http://api',
      actionModal: ref({ type: 'cancel', order: null, reason: '', error: '' }),
      actionPending: ref({}),
      actionSubmitting: ref(false),
      orderMenu: ref(null),
      orders: ref(orders),
      showActionModal: ref(false),
      store: store(),
      toast: toast(),
    }
    return { deps, ...useOrderActions(deps) }
  }

  it('offers cancel only before the trip starts and escalate once', () => {
    const { canCancelOrder, canEscalateOrder, hasMenuActions } = setup([])
    expect(canCancelOrder({ status: 'dispatched' })).toBe(true)
    expect(canCancelOrder({ status: 'in-transit' })).toBe(false)
    expect(canEscalateOrder({ status: 'delivered', escalated: true })).toBe(false)
    expect(hasMenuActions({ status: 'cancelled' })).toBe(false)
  })

  it('needs a reason, then cancels and removes the order', async () => {
    const router = stubFetch([['POST', '/orders/o1/cancel', {}]])
    const order = { id: 'QC-1', backendId: 'o1', status: 'ready' }
    const { deps, cancelOrder, submitActionModal } = setup([order])

    await cancelOrder(order)
    expect(deps.showActionModal.value).toBe(true)

    deps.actionModal.value.reason = ' x '
    await submitActionModal()
    expect(deps.actionModal.value.error).toBe('Please enter a short reason before continuing.')
    expect(router.calls).toHaveLength(0)

    deps.actionModal.value.reason = 'Customer called to cancel'
    await submitActionModal()
    expect(router.calls[0].body).toEqual({ reason: 'Customer called to cancel' })
    expect(deps.orders.value).toEqual([])
    expect(deps.showActionModal.value).toBe(false)
  })

  it('escalates an order and marks it for the logistics manager', async () => {
    stubFetch([['POST', '/orders/o2/escalate', { id: 'esc-1', status: 'OPEN' }]])
    const order = { id: 'QC-2', backendId: 'o2', status: 'in-transit' }
    const { deps, escalateOrder, submitActionModal, isActionPending } = setup([order])

    await escalateOrder(order)
    await submitActionModal()

    expect(order).toMatchObject({ escalated: true, escalationId: 'esc-1', slaStatus: 'ESCALATED' })
    expect(deps.toast.success).toHaveBeenCalledWith('Order QC-2 escalated')
    expect(isActionPending(order)).toBe(false)
  })

  it('keeps the dialog open with the server error when cancelling fails', async () => {
    stubFetch([
      ['POST', '/orders/o3/cancel', { status: 400, body: { detail: 'Already in transit' } }],
    ])
    const order = { id: 'QC-3', backendId: 'o3', status: 'ready' }
    const { deps, cancelOrder, submitActionModal } = setup([order])

    await cancelOrder(order)
    await submitActionModal()

    expect(deps.actionModal.value.error).toBe('Already in transit')
    expect(deps.showActionModal.value).toBe(true)
    expect(deps.orders.value).toHaveLength(1)
  })
})

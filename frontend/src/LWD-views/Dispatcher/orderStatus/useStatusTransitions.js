// Moving orders to dispatched, in transit or delivered, one at a time or in bulk,
// applying each change to the table once the backend accepts it.
import { STATUS_TRANSITIONS } from './orderRows'
import { getStoredAccessToken } from '@/config/api'

export function useStatusTransitions({
    API_BASE,
    bulkUpdating,
    canDispatchOrder,
    clearSelection,
    getOrderKey,
    selectedDispatchableReadyOrders,
    selectedDispatchedOrders,
    selectedTransitOrders,
    store,
    toast,
    transitionPending,
}) {
    function setTransitionPending(order, pending) {
        const key = getOrderKey(order)
        transitionPending.value = { ...transitionPending.value, [key]: pending }
    }

    function isTransitionPending(order) {
        return Boolean(transitionPending.value[getOrderKey(order)]) || bulkUpdating.value
    }

    function applyTransitionLocally(order, newStatus) {
        const config = STATUS_TRANSITIONS[newStatus]
        if (!config) return

        order.status = newStatus
        order.statusLabel = config.label
        order.lastUpdated = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

        if (newStatus === 'dispatched') {
            order.slaStatus = 'On Track'
            order.slaClass = 'bg-green-500/20 text-green-400'
        } else if (newStatus === 'in-transit') {
            order.slaStatus = 'In Transit'
            order.slaClass = 'bg-purple-500/20 text-purple-400'
        } else if (newStatus === 'delivered') {
            order.slaStatus = 'Delivered'
            order.slaClass = 'bg-green-500/20 text-green-400'
        }
    }

    async function transitionOrderStatus(order, newStatus, options = {}) {
        const { silent = false, refresh = true } = options
        const config = STATUS_TRANSITIONS[newStatus]
        if (!config) return false

        if (newStatus === 'dispatched' && !canDispatchOrder(order)) {
            const message = `Assign a driver before dispatching ${order.id}`
            if (!silent) {
                toast.warning(message)
            }
            throw new Error(message)
        }

        const orderId = order.backendId || order.id
        if (!orderId) {
            const message = 'No backend order ID available for transition'
            if (!silent) {
                console.error(message)
                toast.error(message)
            }
            throw new Error(message)
        }

        setTransitionPending(order, true)
        try {
            const token = getStoredAccessToken()
            const res = await fetch(`${API_BASE}/api/v1/orders/${orderId}/transition`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ next_status: config.backendStatus }),
            })

            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || res.statusText || 'Status update failed')
            }

            applyTransitionLocally(order, newStatus)
            clearSelection([getOrderKey(order)])

            if (refresh) {
                await store.fetchActiveOrders().catch(() => {})
            }

            if (!silent) {
                toast.success(`${config.label} updated for ${order.id}`)
            }
            return true
        } catch (error) {
            console.error('Transition error:', error)
            if (!silent) {
                const message = error instanceof Error
                    ? error.message
                    : 'Network error while updating order status. Please try again.'
                toast.error(message)
            }
            throw error
        } finally {
            setTransitionPending(order, false)
        }
    }

    async function updateStatus(order, newStatus) {
        try {
            await transitionOrderStatus(order, newStatus)
        } catch (_) {}
    }

    async function applyBulkStatus(newStatus) {
        const statusGroups = {
            dispatched: selectedDispatchableReadyOrders.value,
            'in-transit': selectedDispatchedOrders.value,
            delivered: selectedTransitOrders.value,
        }
        const targets = statusGroups[newStatus] || []
        const label = STATUS_TRANSITIONS[newStatus]?.label || 'Updated'

        if (!targets.length) return

        bulkUpdating.value = true
        try {
            const results = await Promise.allSettled(
                targets.map(order => transitionOrderStatus(order, newStatus, { silent: true, refresh: false }))
            )

            const successCount = results.filter(result => result.status === 'fulfilled').length
            const failureCount = results.length - successCount

            await store.fetchActiveOrders().catch(() => {})

            if (failureCount === 0) {
                toast.success(`${label} updated for ${successCount} order${successCount === 1 ? '' : 's'}`)
            } else if (successCount > 0) {
                toast.warning(`${label} updated for ${successCount} orders. ${failureCount} failed and stayed selected.`)
            } else {
                toast.error(`Unable to update selected orders to ${label.toLowerCase()}.`)
            }
        } finally {
            bulkUpdating.value = false
        }
    }

    return { isTransitionPending, updateStatus, applyBulkStatus }
}

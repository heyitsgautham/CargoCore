// The per-order action menu: cancel or escalate with a reason, through a shared dialog.
import { getStoredAccessToken } from '@/config/api'

export function useOrderActions({
    API_BASE,
    actionModal,
    actionPending,
    actionSubmitting,
    orderMenu,
    orders,
    showActionModal,
    store,
    toast,
}) {
    function toggleOrderMenu(order) {
        const key = order.backendId || order.id
        orderMenu.value = orderMenu.value === key ? null : key
    }

    function setActionPending(order, pending) {
        const key = order.backendId || order.id
        actionPending.value = { ...actionPending.value, [key]: pending }
    }

    function isActionPending(order) {
        const key = order.backendId || order.id
        return Boolean(actionPending.value[key])
    }

    function canCancelOrder(order) {
        return ['ready', 'dispatched'].includes(order.status)
    }

    function canEscalateOrder(order) {
        return ['ready', 'dispatched', 'in-transit', 'delivered'].includes(order.status) && !order.escalated
    }

    function hasMenuActions(order) {
        return canCancelOrder(order) || canEscalateOrder(order)
    }

    function openActionModal(type, order) {
        actionModal.value = {
            type,
            order,
            reason: type === 'cancel'
                ? 'Dispatcher cancelled before route execution'
                : 'Order needs logistics manager review',
            error: '',
        }
        showActionModal.value = true
    }

    function closeActionModal() {
        showActionModal.value = false
        actionModal.value = {
            type: 'cancel',
            order: null,
            reason: '',
            error: '',
        }
    }

    async function cancelOrder(order) {
        orderMenu.value = null
        openActionModal('cancel', order)
    }

    async function submitCancel(order, reason) {
        const orderId = order.backendId || order.id
        if (!orderId) throw new Error('Order ID is missing. Please refresh and try again.')

        setActionPending(order, true)
        try {
            const token = getStoredAccessToken()
            const res = await fetch(`${API_BASE}/api/v1/orders/${orderId}/cancel`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ reason }),
            })

            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || res.statusText)
            }

            orders.value = orders.value.filter(o => (o.backendId || o.id) !== orderId)
            await store.fetchActiveOrders().catch(() => {})
            toast.success(`Order ${order.id} cancelled`)
        } catch (error) {
            console.error('Cancel error:', error)
            throw error
        } finally {
            setActionPending(order, false)
        }
    }

    async function escalateOrder(order) {
        orderMenu.value = null
        if (order.escalated) return
        openActionModal('escalate', order)
    }

    async function submitEscalation(order, reason) {
        const orderId = order.backendId || order.id
        if (!orderId) throw new Error('Order ID is missing. Please refresh and try again.')

        setActionPending(order, true)
        try {
            const token = getStoredAccessToken()
            const res = await fetch(`${API_BASE}/api/v1/orders/${orderId}/escalate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ reason }),
            })

            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || res.statusText)
            }

            const escalation = await res.json().catch(() => null)
            order.escalated = true
            order.escalationId = escalation?.id || order.escalationId || null
            order.escalationStatus = escalation?.status || 'OPEN'
            order.slaStatus = 'ESCALATED'
            order.slaClass = 'bg-red-500/20 text-red-400'
            await store.fetchActiveOrders().catch(() => {})
            toast.success(`Order ${order.id} escalated`)
        } catch (error) {
            console.error('Escalation error:', error)
            throw error
        } finally {
            setActionPending(order, false)
        }
    }

    async function submitActionModal() {
        const order = actionModal.value.order
        const trimmedReason = actionModal.value.reason.trim()
        if (!order) return

        if (trimmedReason.length < 3) {
            actionModal.value.error = 'Please enter a short reason before continuing.'
            return
        }

        actionModal.value.error = ''
        actionSubmitting.value = true
        try {
            if (actionModal.value.type === 'cancel') {
                await submitCancel(order, trimmedReason)
            } else {
                await submitEscalation(order, trimmedReason)
            }
            closeActionModal()
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Something went wrong. Please try again.'
            actionModal.value.error = message
            toast.error(message)
        } finally {
            actionSubmitting.value = false
        }
    }

    return {
        toggleOrderMenu,
        isActionPending,
        canCancelOrder,
        canEscalateOrder,
        hasMenuActions,
        closeActionModal,
        cancelOrder,
        escalateOrder,
        submitActionModal,
    }
}

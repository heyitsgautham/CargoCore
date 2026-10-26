// Loading, cancelling, rescheduling and rating the customer's orders, plus the hubs they book from.
import { apiUrl } from '@/config/api'
import { normalizeTrackingOrder } from './orderMapping'

export function useCustomerOrders({
    applyDamageReportsToOrders,
    assignmentPreview,
    assignmentPreviewError,
    cancelOrder,
    dashboardError,
    dashboardLoading,
    dashboardSummary,
    fetchNotifications,
    fetchWalletBalance,
    normalizeBackendOrder,
    notifications,
    orders,
    ordersError,
    ordersLoading,
    rescheduleOrder,
    trackingError,
    trackingLoading,
    user,
    warehouses,
}) {
    async function fetchWarehouses() {
        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(apiUrl('api/v1/warehouses?page=1&page_size=100'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}))
                throw new Error(errData.detail || 'Failed to load hubs')
            }
            const data = await res.json()
            warehouses.value = (Array.isArray(data) ? data : data.items || [])
                .filter((warehouse) => warehouse?.is_active !== false)
                .map((warehouse) => ({
                    id: String(warehouse.id),
                    name: warehouse.name,
                    address: warehouse.address || '',
                }))
            return warehouses.value
        } catch (error) {
            console.warn('[individualStore] fetchWarehouses failed:', error)
            return warehouses.value
        }
    }

    async function fetchOrderAssignmentPreview(warehouseId = null) {
        try {
            const token = localStorage.getItem('auth_token')
            const query = warehouseId ? `?warehouse_id=${encodeURIComponent(warehouseId)}` : ''
            const res = await fetch(apiUrl(`api/v1/orders/assignment-preview${query}`), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}))
                throw new Error(errData.detail || 'Failed to resolve assignment preview')
            }
            const data = await res.json()
            assignmentPreviewError.value = ''
            assignmentPreview.value = {
                ...data,
                warehouse_id: String(data.warehouse_id),
            }
            return assignmentPreview.value
        } catch (error) {
            console.warn('[individualStore] fetchOrderAssignmentPreview failed:', error)
            assignmentPreview.value = null
            assignmentPreviewError.value = error?.message || 'Failed to resolve assignment preview'
            return null
        }
    }

    async function fetchDashboardSummary() {
        dashboardLoading.value = true
        dashboardError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/dashboard'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                dashboardError.value = errData.detail || 'Failed to load dashboard data.'
                return { success: false, message: dashboardError.value }
            }

            const data = await response.json()
            dashboardSummary.value = data
            user.value = {
                ...user.value,
                name: data.profile?.name || user.value.name,
                email: data.profile?.email || user.value.email,
                phone: data.profile?.phone || user.value.phone,
                joiningDate: data.profile?.created_at || user.value.joiningDate,
            }

            // Load notifications in parallel with dashboard (best-effort)
            fetchNotifications().catch(() => {})

            return { success: true, data }
        } catch (error) {
            dashboardError.value = 'Error connecting to the server.'
            return { success: false, message: dashboardError.value }
        } finally {
            dashboardLoading.value = false
        }
    }

    async function fetchOrders(status = null) {
        ordersLoading.value = true
        ordersError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const params = new URLSearchParams({ page: '1', page_size: '50' })
            if (status && status !== 'all') {
                const backendStatusMap = {
                    pending: 'CONFIRMED',
                    dispatched: 'ASSIGNED',
                    'in-transit': 'IN_TRANSIT',
                    delivered: 'DELIVERED',
                    cancelled: 'CANCELLED',
                }
                const backendStatus = backendStatusMap[status]
                if (backendStatus) params.set('status_filter', backendStatus)
            }

            const response = await fetch(apiUrl(`api/v1/orders?${params.toString()}`), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                ordersError.value = errData.detail || 'Failed to load orders.'
                return { success: false, message: ordersError.value }
            }

            const data = await response.json()
            orders.value = (data.items || []).map(normalizeBackendOrder)
            applyDamageReportsToOrders()
            return { success: true, data: orders.value }
        } catch (error) {
            ordersError.value = 'Error connecting to the server.'
            return { success: false, message: ordersError.value }
        } finally {
            ordersLoading.value = false
        }
    }

    async function fetchTrackingOrders() {
        trackingLoading.value = true
        trackingError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/tracking'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                trackingError.value = errData.detail || 'Failed to load tracking data.'
                return { success: false, message: trackingError.value }
            }

            const data = await response.json()
            orders.value = (data.orders || []).map(normalizeTrackingOrder)
            return { success: true, data: orders.value }
        } catch (error) {
            trackingError.value = 'Error connecting to the server.'
            return { success: false, message: trackingError.value }
        } finally {
            trackingLoading.value = false
        }
    }

    async function cancelOrderRemote(id, reason = 'Cancelled by customer') {
        const order = orders.value.find(o => o.id === id || o.backendId === id)
        if (!order?.backendId) {
            const local = cancelOrder(id)
            return { success: !!local, order: local }
        }

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl(`api/v1/orders/${order.backendId}/cancel`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ reason }),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to cancel order.' }
            }

            const updated = await response.json()
            const normalized = normalizeBackendOrder(updated)
            const index = orders.value.findIndex(o => o.backendId === updated.id)
            if (index >= 0) orders.value[index] = normalized
            // Refresh wallet so balance reflects the refund immediately
            await fetchWalletBalance()
            // Re-fetch tracking orders so Tracking.vue shows updated status + cancel log entry
            fetchTrackingOrders().catch(() => {})
            return {
                success: true,
                order: normalized,
                walletRefund: updated.wallet_refund_amount ?? 0,
            }
        } catch (error) {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    async function submitCustomerRating(backendId, rating, feedback = null) {
        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl(`api/v1/orders/${backendId}/customer-rating`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ rating, feedback }),
            })
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to submit rating.' }
            }
            const updated = await response.json()
            const idx = orders.value.findIndex(o => o.backendId === backendId)
            if (idx !== -1) {
                orders.value[idx].customerRating = updated.customer_rating
                orders.value[idx].customerFeedback = updated.customer_feedback
            }
            return { success: true }
        } catch {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    async function rescheduleOrderRemote(id, newDate, newTime) {
        const order = orders.value.find(o => o.id === id || o.backendId === id)
        if (!order?.backendId) {
            rescheduleOrder(id, newDate, newTime)
            return { success: true }
        }

        try {
            const token = localStorage.getItem('auth_token')
            const scheduled_at = newDate ? new Date(newDate).toISOString() : null
            const response = await fetch(apiUrl(`api/v1/orders/${order.backendId}`), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ scheduled_at }),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to reschedule order.' }
            }

            const updated = await response.json()
            const normalized = normalizeBackendOrder(updated)
            const index = orders.value.findIndex(o => o.backendId === updated.id)
            if (index >= 0) orders.value[index] = normalized
            notifications.value.unshift({
                id: Date.now(), title: 'Rescheduled', message: `${normalized.id} moved to ${newDate}.`, time: 'Just now', read: false, icon: 'schedule',
            })
            return { success: true, order: normalized }
        } catch (error) {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    return {
        fetchWarehouses,
        fetchOrderAssignmentPreview,
        fetchDashboardSummary,
        fetchOrders,
        fetchTrackingOrders,
        cancelOrderRemote,
        submitCustomerRating,
        rescheduleOrderRemote,
     }
}
